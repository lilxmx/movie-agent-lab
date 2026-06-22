"""FastAPI 依赖：数据库会话与当前登录用户解析。"""
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthError
from app.core.security import decode_access_token

DbDep = Annotated[Session, Depends(get_db)]


def _extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return authorization


def get_optional_user_id(authorization: str | None = Header(default=None)) -> int | None:
    """可选登录：游客也可访问，返回 None 表示未登录。"""
    token = _extract_token(authorization)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        return None


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    """必须登录，否则抛出鉴权异常。"""
    user_id = get_optional_user_id(authorization)
    if user_id is None:
        raise AuthError()
    return user_id


OptionalUserDep = Annotated[int | None, Depends(get_optional_user_id)]
CurrentUserDep = Annotated[int, Depends(get_current_user_id)]
