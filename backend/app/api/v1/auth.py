"""鉴权路由。"""
from fastapi import APIRouter

from app.core.deps import CurrentUserDep, DbDep
from app.core.response import ApiResponse
from app.schemas.auth import CurrentUser, LoginRequest, LoginResult, RegisterRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["鉴权"])


@router.post("/login", response_model=ApiResponse[LoginResult])
def login(body: LoginRequest, db: DbDep):
    return ApiResponse.ok(auth_service.login(db, body.user_name, body.user_password))


@router.post("/register", response_model=ApiResponse[LoginResult])
def register(body: RegisterRequest, db: DbDep):
    return ApiResponse.ok(auth_service.register(db, body.user_name, body.user_password))


@router.get("/me", response_model=ApiResponse[CurrentUser])
def me(user_id: CurrentUserDep, db: DbDep):
    from app.repositories import user_repo

    user = user_repo.get_by_id(db, user_id)
    name = user.user_name if user else ""
    return ApiResponse.ok(CurrentUser(user_id=user_id, user_name=name))


@router.post("/logout", response_model=ApiResponse)
def logout():
    # JWT 无状态，登出由前端清除 token 即可
    return ApiResponse.ok(message="已登出")
