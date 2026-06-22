"""Redis 客户端，复用旧 embedding 缓存（itemEmb / graphEmb / userEmb 等）。"""
from functools import lru_cache

import redis

from app.core.config import settings


@lru_cache
def get_redis() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
    )
