"""知识库检索服务：直接查询 MySQL movieSummary 表。

不依赖内存索引，每次搜索实时从数据库检索，重启无需重建。
检索逻辑：
  1. 将查询拆分为关键词（2字以上中文词 + 英文单词）
  2. 对每个关键词用 LIKE 匹配电影名和简介
  3. 按命中关键词数量排序，返回 top_k
"""
import re

from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.models import Movie, MovieSummary


def _extract_keywords(query: str) -> list[str]:
    """从查询中提取有效关键词：英文单词 + 长度≥2 的中文片段。"""
    keywords: list[str] = []
    # 英文单词（至少 2 个字母）
    keywords.extend(w for w in re.findall(r"[a-zA-Z]{2,}", query))
    # 中文：按非中文字符分割，保留长度≥2 的片段
    for chunk in re.split(r"[^\u4e00-\u9fff]+", query):
        if len(chunk) >= 2:
            # 长段再按 2/3 字切分成 bigram/trigram，提高召回
            keywords.append(chunk)
            for i in range(len(chunk) - 1):
                keywords.append(chunk[i : i + 2])
    # 去重、去空，保留唯一
    seen: set[str] = set()
    result: list[str] = []
    for k in keywords:
        if k and k not in seen:
            seen.add(k)
            result.append(k)
    return result


def search(db: Session, query: str, top_k: int = 5) -> list[dict]:
    """直接查询 MySQL，返回最相关的电影列表。"""
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    # 构建 LIKE 条件：电影名 OR 简介中包含该关键词
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(Movie.movie_name.like(pattern))
        conditions.append(MovieSummary.movie_summary.like(pattern))

    stmt = (
        select(
            Movie.movie_id,
            Movie.movie_name,
            MovieSummary.movie_summary,
        )
        .join(MovieSummary, MovieSummary.movie_id == Movie.movie_id)
        .where(or_(*conditions))
        .limit(top_k * 5)  # 多取一些，再在内存里排序
    )

    rows = db.execute(stmt).all()
    if not rows:
        return []

    # 计算每条结果命中多少个关键词，排序取 top_k
    scored: list[tuple[int, int, str]] = []
    for movie_id, name, summary in rows:
        combined = f"{name} {summary or ''}"
        hits = sum(1 for kw in keywords if kw in combined)
        scored.append((hits, movie_id, name))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {"movie_id": mid, "title": title, "matched_keywords": hits}
        for hits, mid, title in scored[:top_k]
    ]
