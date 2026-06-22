"""排序层：将召回候选按指定模型打分。

支持四种模型：emb / NeuralCF / DeepCrossing / WideAndDeep。
真实 TF Serving 不可用时，统一回退为按电影平均分排序，保证链路可跑通。
"""
from sqlalchemy.orm import Session

from app.recsys.classic import embedding, model_serving
from app.repositories import movie_repo


def _fallback_scores(db: Session, candidate_ids: list[int]) -> dict[int, float]:
    stats = movie_repo.statistics_by_ids(db, candidate_ids)
    return {
        mid: float(stats[mid].movie_avg_rating or 0.0) if mid in stats else 0.0
        for mid in candidate_ids
    }


def _emb_scores(db: Session, user_id: int, candidate_ids: list[int]) -> dict[int, float]:
    user_emb = embedding.load_user_emb(user_id)
    if user_emb is None:
        return _fallback_scores(db, candidate_ids)
    scores: dict[int, float] = {}
    for mid in candidate_ids:
        movie_emb = embedding.load_movie_emb(mid)
        scores[mid] = (
            embedding.cosine_similarity(user_emb, movie_emb) if movie_emb else 0.0
        )
    return scores


def _deep_scores(
    db: Session, user_id: int, candidate_ids: list[int], model: str
) -> dict[int, float]:
    instances = [{"movieId": mid, "userId": user_id} for mid in candidate_ids]
    predictions = model_serving.predict(model, instances)
    if predictions is None or len(predictions) != len(candidate_ids):
        return _fallback_scores(db, candidate_ids)
    return dict(zip(candidate_ids, predictions))


def rank(db: Session, model: str, user_id: int, candidate_ids: list[int]) -> dict[int, float]:
    if not candidate_ids:
        return {}
    if model == "emb":
        return _emb_scores(db, user_id, candidate_ids)
    return _deep_scores(db, user_id, candidate_ids, model)
