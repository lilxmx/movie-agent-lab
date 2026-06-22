"""评论点赞路由。"""
from fastapi import APIRouter

from app.core.deps import CurrentUserDep, DbDep
from app.core.response import ApiResponse
from app.services import social_service

router = APIRouter(prefix="/comments", tags=["评论"])


@router.post("/{comment_id}/like", response_model=ApiResponse)
def like(comment_id: int, db: DbDep, user_id: CurrentUserDep):
    liked = social_service.like_comment(db, user_id, comment_id)
    return ApiResponse.ok(liked, message="点赞成功" if liked else "取消点赞")
