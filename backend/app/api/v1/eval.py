"""评测沙箱路由（Phase 5 起步：覆盖率指标）。"""
from fastapi import APIRouter

from app.core.deps import DbDep
from app.core.response import ApiResponse
from app.recsys.metrics import coverage as coverage_metric

router = APIRouter(prefix="/eval", tags=["评测沙箱"])


@router.get("/metrics/coverage", response_model=ApiResponse)
def coverage(db: DbDep, mode: str = "classic", sample_users: int = 50, size: int = 10):
    return ApiResponse.ok(coverage_metric.coverage(db, mode, sample_users, size))
