"""用户画像聚合：偏好标签、统计特征、长期记忆，供 AgentMemory 页面展示。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.scan_history import recent_scans
from app.models import AgentMemory
from app.repositories import user_repo


def get_profile(db: Session, user_id: int) -> dict:
    stat = user_repo.get_statistic(db, user_id)
    like_genres = stat.user_like_genres.split("|") if stat and stat.user_like_genres else []
    memories = _load_memories(db, user_id)
    return {
        "user_id": user_id,
        "like_genres": like_genres,
        "rating_count": stat.user_rating_count if stat else 0,
        "avg_rating": stat.user_avg_rating if stat else None,
        "avg_released_year": stat.user_avg_released_year if stat else None,
        "recent_scans": recent_scans(user_id, 10),
        "memories": memories,
    }


def _load_memories(db: Session, user_id: int) -> list[dict]:
    try:
        rows = db.scalars(
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(20)
        ).all()
    except Exception:
        return []
    return [{"type": m.memory_type, "content": m.content} for m in rows]
