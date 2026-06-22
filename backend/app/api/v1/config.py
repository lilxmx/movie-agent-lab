"""前端运行时配置：CDN 地址与可用推荐模式，避免前端硬编码。"""
from fastapi import APIRouter

from app.core.config import settings
from app.core.response import ApiResponse
from app.recsys.registry import registry

router = APIRouter(prefix="/config", tags=["配置"])


@router.get("/client", response_model=ApiResponse)
def client_config():
    return ApiResponse.ok(
        {
            "poster_cdn": settings.poster_cdn_url,
            "poster_bg_cdn": settings.poster_bg_cdn_url,
            "cast_poster_cdn": settings.cast_poster_cdn_url,
            "rec_modes": registry.modes(),
        }
    )
