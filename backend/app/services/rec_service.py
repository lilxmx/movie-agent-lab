"""推荐调度服务：统一入口，按 mode/scene 选择策略并记录运行日志。"""
from sqlalchemy.orm import Session

from app.models import RecommendationRun
from app.recsys.contracts import RecRequest, RecResult
from app.recsys.registry import registry


def _resolve_mode(mode: str, scene: str) -> str:
    """classic 模式下按 scene 选择具体策略；agent 模式直接用 agent 策略。"""
    if mode == "agent":
        return "agent"
    return scene if scene in {"hot", "similar", "personalized"} else "personalized"


def recommend(db: Session, mode: str, req: RecRequest) -> RecResult:
    strategy_key = _resolve_mode(mode, req.scene)
    recommender = registry.get(strategy_key)
    result = recommender.recommend(db, req)
    _log_run(db, req, mode, strategy_key, result)
    return result


def _log_run(
    db: Session, req: RecRequest, mode: str, strategy_key: str, result: RecResult
) -> None:
    try:
        db.add(
            RecommendationRun(
                user_id=req.user_id,
                mode=mode,
                scene=req.scene,
                model_name=strategy_key,
                trace_id=result.trace_id,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
