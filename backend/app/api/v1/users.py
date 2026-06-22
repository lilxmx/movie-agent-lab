"""用户中心路由：收藏、评分历史、浏览历史。"""
from fastapi import APIRouter

from app.core.deps import CurrentUserDep, DbDep
from app.core.response import ApiResponse
from app.memory.scan_history import recent_scans
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户中心"])


@router.get("/{user_id}/collections", response_model=ApiResponse)
def collections(user_id: int, db: DbDep, page: int = 1, page_size: int = 10):
    return ApiResponse.ok(user_service.collections(db, user_id, page, page_size))


@router.get("/{user_id}/ratings", response_model=ApiResponse)
def ratings(user_id: int, db: DbDep, page: int = 1, page_size: int = 10):
    return ApiResponse.ok(user_service.rating_history(db, user_id, page, page_size))


@router.get("/{user_id}/history", response_model=ApiResponse)
def history(user_id: int, _current: CurrentUserDep, size: int = 20):
    return ApiResponse.ok(recent_scans(user_id, size))
