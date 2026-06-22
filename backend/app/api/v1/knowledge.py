"""知识库路由：直接查询 MySQL movieSummary 表，无需预建索引。"""
from pydantic import BaseModel

from fastapi import APIRouter

from app.core.deps import DbDep
from app.core.response import ApiResponse
from app.knowledge import service

router = APIRouter(prefix="/knowledge", tags=["知识库"])


class SearchBody(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search", response_model=ApiResponse)
def search(body: SearchBody, db: DbDep):
    return ApiResponse.ok(service.search(db, body.query, body.top_k))
