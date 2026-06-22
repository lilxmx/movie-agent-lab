"""Embedding 工具与 Redis 加载，迁移自旧 Embedding.java + RedisRepository。

旧 Redis 中存有三类向量（空格分隔的 float 字符串）：
  userEmb:%s   用户向量（User2Vec）
  itemEmb:%s   电影向量（Item2Vec）
  graphEmb:%s  电影向量（DeepWalk）
"""
import math

import redis

from app.core.redis_client import get_redis

USER_EMB = "userEmb:{}"
ITEM_EMB = "itemEmb:{}"
GRAPH_EMB = "graphEmb:{}"


def parse_emb(raw: str | None) -> list[float] | None:
    if not raw:
        return None
    try:
        return [float(x) for x in raw.split()]
    except ValueError:
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return -1.0
    return dot / (norm_a * norm_b)


def _load(key_template: str, entity_id: int) -> list[float] | None:
    try:
        raw = get_redis().get(key_template.format(entity_id))
    except redis.RedisError:
        return None
    return parse_emb(raw)


def load_user_emb(user_id: int) -> list[float] | None:
    return _load(USER_EMB, user_id)


def load_movie_emb(movie_id: int) -> list[float] | None:
    """优先 Item2Vec，缺失时回退 DeepWalk（与旧逻辑一致）。"""
    return _load(ITEM_EMB, movie_id) or _load(GRAPH_EMB, movie_id)
