"""API v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    chat,
    comments,
    config,
    eval,
    knowledge,
    memory,
    movies,
    recommendations,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(config.router)
api_router.include_router(movies.router)
api_router.include_router(comments.router)
api_router.include_router(users.router)
api_router.include_router(recommendations.router)
api_router.include_router(chat.router)
api_router.include_router(memory.router)
api_router.include_router(knowledge.router)
api_router.include_router(eval.router)
