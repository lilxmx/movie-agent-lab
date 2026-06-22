"""个性化推荐主流程，迁移自旧 UserServiceImpl.recMovieIds。

召回：按用户偏好类型 + 平均观影年份邻域过滤，剔除已评分电影。
排序：按 A/B 测试选定模型打分。冷启动用户（无统计）回退热门。
"""
from sqlalchemy.orm import Session

from app.recsys.classic import rankers
from app.recsys.classic.ab_test import model_by_user_id
from app.recsys.classic.builder import build_items
from app.recsys.classic.hot import HotRecommender
from app.recsys.contracts import RecRequest, RecResult
from app.repositories import movie_repo, user_repo

_DEFAULT_MODEL = "WideAndDeep"


def _choose_model(db: Session, user_id: int) -> str:
    if user_repo.get_ab_test_flag(db) == 1:
        return model_by_user_id(user_id)
    return _DEFAULT_MODEL


def _recall(db: Session, user_id: int, like_genres: str, avg_year: int | None) -> list[int]:
    target_year = avg_year or 2000
    candidates = movie_repo.candidate_ids_by_genres_and_year(db, like_genres, target_year, 2)
    rated = set(movie_repo.rated_movie_ids(db, user_id))
    return [mid for mid in candidates if mid not in rated]


class PersonalizedRecommender:
    name = "personalized"

    def recommend(self, db: Session, req: RecRequest) -> RecResult:
        if req.user_id is None:
            return HotRecommender().recommend(db, req)

        stat = user_repo.get_statistic(db, req.user_id)
        if stat is None or not stat.user_like_genres:
            return HotRecommender().recommend(db, req)

        model = _choose_model(db, req.user_id)
        candidate_ids = _recall(db, req.user_id, stat.user_like_genres, stat.user_avg_released_year)
        scores = rankers.rank(db, model, req.user_id, candidate_ids)
        ranked_ids = sorted(scores, key=scores.get, reverse=True)[: req.size]
        items = build_items(
            db, ranked_ids, scores=scores, reason=f"基于你的偏好（{model}）", source="classic"
        )
        result = RecResult(mode="classic", items=items)
        result.trace_id = f"rec_{model}_{result.trace_id[4:]}"
        return result
