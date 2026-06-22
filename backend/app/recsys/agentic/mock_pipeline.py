"""Agent 推荐 mock pipeline（Phase 5）。

独立于传统推荐路线：以"用户意图 + 短期记忆 + 偏好"为输入，产出带自然语言
理由的推荐。当前为 mock 实现，预留 Phase 9 接入真实 Agent / 工具调用的扩展点。
"""
from sqlalchemy.orm import Session

from app.memory.scan_history import recent_scans
from app.recsys.classic.builder import build_items
from app.recsys.contracts import RecRequest, RecResult
from app.repositories import movie_repo, user_repo

_REASON_TEMPLATES = [
    "结合你最近浏览的偏好，推测你会喜欢这部",
    "根据你的高分评价习惯，这部值得一看",
    "与你常看的题材契合，适合下次观影",
]


def _candidate_ids(db: Session, req: RecRequest) -> list[int]:
    if req.user_id is None:
        return movie_repo.hot_movie_ids(db, req.size)

    scanned = recent_scans(req.user_id, req.size)
    stat = user_repo.get_statistic(db, req.user_id)
    if stat and stat.user_like_genres:
        candidates = movie_repo.candidate_ids_by_genres_and_year(
            db, stat.user_like_genres, stat.user_avg_released_year or 2000, 3
        )
        rated = set(movie_repo.rated_movie_ids(db, req.user_id))
        candidates = [m for m in candidates if m not in rated]
    else:
        candidates = movie_repo.hot_movie_ids(db, req.size * 2)

    merged = scanned + [m for m in candidates if m not in scanned]
    return merged[: req.size]


class AgentRecommender:
    name = "agent"

    def recommend(self, db: Session, req: RecRequest) -> RecResult:
        ids = _candidate_ids(db, req)
        items = build_items(db, ids, source="agent")
        for idx, item in enumerate(items):
            item.reason = _REASON_TEMPLATES[idx % len(_REASON_TEMPLATES)]
            item.score = round(1.0 - idx * 0.03, 4)
        return RecResult(mode="agent", items=items)
