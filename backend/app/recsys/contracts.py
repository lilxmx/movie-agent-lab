"""推荐系统统一契约。传统推荐与 Agent 推荐返回同一格式，前端可无差别渲染。"""
from __future__ import annotations

import uuid
from typing import Protocol

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class RecItem(BaseModel):
    movie_id: int
    title: str
    score: float = 0.0
    reason: str = ""
    source: str = ""


class RecResult(BaseModel):
    mode: str
    trace_id: str = Field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:12]}")
    items: list[RecItem] = []


class RecRequest(BaseModel):
    """统一推荐请求。不同策略按需读取字段。"""

    user_id: int | None = None
    movie_id: int | None = None
    scene: str = "personalized"  # hot / similar / personalized
    size: int = 10


class Recommender(Protocol):
    """推荐策略统一接口，便于注册与替换（策略模式）。"""

    name: str

    def recommend(self, db: Session, req: RecRequest) -> RecResult: ...
