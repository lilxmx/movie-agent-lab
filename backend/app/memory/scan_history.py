"""用户浏览历史（短期记忆雏形），复用旧 Redis key userScanHistory:%s。

Redis 不可用时静默降级，不影响主流程。
"""
import redis

from app.core.redis_client import get_redis

_KEY = "userScanHistory:{}"
_MAX = 100


def record_scan(user_id: int, movie_id: int) -> None:
    try:
        client = get_redis()
        key = _KEY.format(user_id)
        client.lrem(key, 0, movie_id)
        client.lpush(key, movie_id)
        client.ltrim(key, 0, _MAX - 1)
    except redis.RedisError:
        pass


def recent_scans(user_id: int, size: int = 20) -> list[int]:
    try:
        client = get_redis()
        values = client.lrange(_KEY.format(user_id), 0, size - 1)
        return [int(v) for v in values]
    except (redis.RedisError, ValueError):
        return []
