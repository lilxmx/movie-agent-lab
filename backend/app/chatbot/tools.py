"""Agent 工具调用层：负责多路召回候选电影。

每个工具独立召回一批候选，最终合并去重，送给 LLM 重排。
工具不感知彼此，可独立扩展。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.chatbot.intent import GENRE_CN_TO_DB, UserIntent
from app.models import Movie
from app.repositories import movie_repo, user_repo


# ---- 工具返回结构 ----

class Candidate:
    __slots__ = ("movie_id", "title", "genres", "avg_rating", "sources")

    def __init__(self, movie: Movie, sources: list[str]):
        self.movie_id: int = movie.movie_id
        self.title: str = movie.movie_name
        self.genres: str = movie.movie_genres or ""
        self.avg_rating: float = 0.0   # 由调用方填充
        self.sources: list[str] = sources  # 记录来源，方便解释


# ---- 各工具实现 ----

def tool_similar_by_ref(db: Session, ref_titles: list[str], size: int = 20) -> list[int]:
    """按参考电影名搜索，直接复用 SimilarRecommender 的内部召回+排序逻辑（含 Redis 缓存）。"""
    from app.recsys.classic.similar import SimilarRecommender
    from app.recsys.contracts import RecRequest

    rec = SimilarRecommender()
    result: list[int] = []
    for title in ref_titles:
        movies, _ = movie_repo.search(db, 1, 3, title, 0)
        for m in movies:
            rec_result = rec.recommend(db, RecRequest(movie_id=m.movie_id, size=size))
            result.extend(item.movie_id for item in rec_result.items)
    return result


def tool_genre_recall(db: Session, genres: list[str], size_per_genre: int = 15) -> list[int]:
    """按偏好类型从数据库召回高分电影。

    自动把中文类型名映射为数据库中实际存储的英文标签（如 科幻→Sci-Fi）。
    同时保留原词兜底，兼容数据库里直接存中文的情况。
    """
    result: list[int] = []
    for genre in genres:
        db_tag = GENRE_CN_TO_DB.get(genre, genre)  # 映射到英文，未找到则原样
        ids = movie_repo.top_ids_by_genre(db, db_tag, size_per_genre)
        if not ids and db_tag != genre:
            # 回退：用原始中文词再试一次
            ids = movie_repo.top_ids_by_genre(db, genre, size_per_genre)
        result.extend(ids)
    return result


def tool_personalized_recall(db: Session, user_id: int, size: int = 20) -> list[int]:
    """基于用户偏好统计进行个性化召回（复用旧推荐逻辑）。"""
    stat = user_repo.get_statistic(db, user_id)
    if not stat or not stat.user_like_genres:
        return []
    rated = set(movie_repo.rated_movie_ids(db, user_id))
    candidates = movie_repo.candidate_ids_by_genres_and_year(
        db,
        stat.user_like_genres,
        stat.user_avg_released_year or 2000,
        5,
    )
    return [cid for cid in candidates if cid not in rated][:size]


def tool_hot_fallback(db: Session, size: int = 20) -> list[int]:
    """兜底：返回全局热门电影。"""
    return movie_repo.hot_movie_ids(db, size)


def tool_semantic_search(db: Session, keywords: list[str], size: int = 15) -> list[int]:
    """利用知识库关键词检索召回相关电影。"""
    from app.knowledge import service as ks

    query = " ".join(keywords)
    hits = ks.search(db, query, size)
    return [h["movie_id"] for h in hits if h.get("movie_id")]


# ---- 多路召回汇总 ----

def recall_candidates(
    db: Session,
    intent: UserIntent,
    user_id: int | None,
    max_candidates: int = 40,
) -> list[Candidate]:
    """根据意图调用多个工具，合并去重，返回候选列表。"""
    id_sources: dict[int, list[str]] = {}

    def add(ids: list[int], source: str) -> None:
        for mid in ids:
            id_sources.setdefault(mid, []).append(source)

    # 1. 参考电影相似召回
    if intent.reference_movies:
        add(tool_similar_by_ref(db, intent.reference_movies, 20), "相似召回")

    # 2. 类型召回
    if intent.preferred_genres:
        add(tool_genre_recall(db, intent.preferred_genres, 15), "类型召回")

    # 3. 语义/关键词搜索（用偏好词）
    if intent.preferred_mood or intent.preferred_genres:
        kws = intent.preferred_genres + intent.preferred_mood
        add(tool_semantic_search(db, kws, 15), "语义检索")

    # 4. 个性化召回（已登录）
    if user_id:
        add(tool_personalized_recall(db, user_id, 20), "个性化")

    # 5. 兜底热门
    if len(id_sources) < 10:
        add(tool_hot_fallback(db, 20), "热门")

    if not id_sources:
        return []

    # 按召回工具数量排序（多个工具同时命中说明相关性更高）
    ranked_ids = sorted(id_sources, key=lambda mid: len(id_sources[mid]), reverse=True)
    ranked_ids = ranked_ids[:max_candidates]

    # 批量拉取电影信息
    movies = movie_repo.movies_by_ids(db, ranked_ids)
    stats = movie_repo.statistics_by_ids(db, ranked_ids)

    result: list[Candidate] = []
    for mid in ranked_ids:
        m = movies.get(mid)
        if not m:
            continue
        c = Candidate(m, id_sources[mid])
        stat = stats.get(mid)
        c.avg_rating = round(stat.movie_avg_rating or 0.0, 2) if stat else 0.0
        result.append(c)

    return result
