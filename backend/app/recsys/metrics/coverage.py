"""推荐覆盖率指标，迁移自旧 ManagerService.coverageMetric。

覆盖率 = 被推荐触达的电影种类数 / 全部电影数，衡量推荐多样性。
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Movie, UserStatistic
from app.recsys.agentic.mock_pipeline import AgentRecommender
from app.recsys.classic.personalized import PersonalizedRecommender
from app.recsys.contracts import RecRequest


def coverage(db: Session, mode: str = "classic", sample_users: int = 50, size: int = 10) -> dict:
    total_movies = db.scalar(select(func.count()).select_from(Movie)) or 0
    recommender = AgentRecommender() if mode == "agent" else PersonalizedRecommender()

    user_ids = [
        r[0] for r in db.execute(select(UserStatistic.user_id).limit(sample_users)).all()
    ]
    covered: set[int] = set()
    for uid in user_ids:
        result = recommender.recommend(db, RecRequest(user_id=uid, scene="personalized", size=size))
        covered.update(item.movie_id for item in result.items)

    ratio = round(len(covered) / total_movies, 4) if total_movies else 0.0
    return {
        "mode": mode,
        "total_movies": total_movies,
        "covered_movies": len(covered),
        "sampled_users": len(user_ids),
        "coverage": ratio,
    }
