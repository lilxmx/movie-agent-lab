"""相似电影推荐，迁移自旧 MovieServiceImpl.getSimilarMovie。

流程：多路召回（类型 top / 平均分 top / 上映年份邻域）→ Embedding 余弦相似度排序
→ 结果 id 缓存到 Redis similarMovieId:%s。
"""
import redis
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis
from app.recsys.classic import embedding
from app.recsys.classic.builder import build_items
from app.recsys.contracts import RecRequest, RecResult
from app.repositories import movie_repo

_CACHE_KEY = "similarMovieId:{}"


def _recall(db: Session, movie, exclude_id: int) -> list[int]:
    candidates: set[int] = set()
    for genre in (movie.movie_genres or "").split("|"):
        if genre:
            candidates.update(movie_repo.top_ids_by_genre(db, genre, 30))
    candidates.update(movie_repo.top_ids_by_avg(db, 20))
    if movie.movie_released_year and str(movie.movie_released_year).isdigit():
        candidates.update(
            movie_repo.top_ids_by_released_year(db, int(movie.movie_released_year), 2, 10)
        )
    candidates.discard(exclude_id)
    return list(candidates)


def _rank_by_embedding(target_emb: list[float], candidate_ids: list[int]) -> list[int]:
    scored: list[tuple[int, float]] = []
    for mid in candidate_ids:
        emb = embedding.load_movie_emb(mid)
        if emb is None:
            continue
        scored.append((mid, embedding.cosine_similarity(target_emb, emb)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in scored]


def _read_cache(movie_id: int) -> list[int]:
    try:
        values = get_redis().lrange(_CACHE_KEY.format(movie_id), 0, -1)
        return [int(v) for v in values]
    except (redis.RedisError, ValueError):
        return []


def _write_cache(movie_id: int, ids: list[int]) -> None:
    if not ids:
        return
    try:
        client = get_redis()
        key = _CACHE_KEY.format(movie_id)
        client.delete(key)
        client.rpush(key, *ids)
    except redis.RedisError:
        pass


class SimilarRecommender:
    name = "similar"

    def recommend(self, db: Session, req: RecRequest) -> RecResult:
        if req.movie_id is None:
            return RecResult(mode="classic", items=[])

        cached = _read_cache(req.movie_id)
        if cached:
            items = build_items(db, cached[: req.size], reason="与该片风格相近", source="classic")
            return RecResult(mode="classic", items=items)

        movie = movie_repo.get_by_id(db, req.movie_id)
        target_emb = embedding.load_movie_emb(req.movie_id)
        if movie is None or target_emb is None:
            # 无向量时退化为同类型高分召回
            fallback = _recall(db, movie, req.movie_id) if movie else []
            items = build_items(db, fallback[: req.size], reason="同类高分电影", source="classic")
            return RecResult(mode="classic", items=items)

        ranked = _rank_by_embedding(target_emb, _recall(db, movie, req.movie_id))
        result_ids = ranked[: req.size]
        _write_cache(req.movie_id, result_ids)
        items = build_items(db, result_ids, reason="与该片风格相近", source="classic")
        return RecResult(mode="classic", items=items)
