"""Agent Memory 路由：用户画像。"""
from fastapi import APIRouter

from app.core.deps import DbDep
from app.core.response import ApiResponse
from app.memory.profile import get_profile

router = APIRouter(prefix="/memory", tags=["Agent Memory"])


@router.get("/profile/{user_id}", response_model=ApiResponse)
def profile(user_id: int, db: DbDep):
    return ApiResponse.ok(get_profile(db, user_id))
