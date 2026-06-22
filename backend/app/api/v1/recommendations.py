"""推荐路由：传统推荐与 Agent 推荐，返回统一格式。"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.deps import DbDep, OptionalUserDep
from app.core.response import ApiResponse
from app.recsys.contracts import RecRequest, RecResult
from app.services import rec_service

router = APIRouter(prefix="/recommendations", tags=["推荐"])


class RecBody(BaseModel):
    scene: str = "personalized"  # hot / similar / personalized
    movie_id: int | None = None
    size: int = 10


def _build_req(body: RecBody, user_id: int | None) -> RecRequest:
    return RecRequest(user_id=user_id, movie_id=body.movie_id, scene=body.scene, size=body.size)


@router.post("/classic", response_model=ApiResponse[RecResult])
def classic(body: RecBody, db: DbDep, user_id: OptionalUserDep):
    result = rec_service.recommend(db, "classic", _build_req(body, user_id))
    return ApiResponse.ok(result)


@router.post("/agent", response_model=ApiResponse[RecResult])
def agent(body: RecBody, db: DbDep, user_id: OptionalUserDep):
    result = rec_service.recommend(db, "agent", _build_req(body, user_id))
    return ApiResponse.ok(result)
