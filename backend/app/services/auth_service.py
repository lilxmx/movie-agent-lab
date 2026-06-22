"""鉴权业务逻辑。沿用旧库密码规则 MD5(password+salt) 以兼容存量用户。"""
import secrets

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.core.security import create_access_token, md5_with_salt, verify_legacy_password
from app.repositories import user_repo
from app.schemas.auth import LoginResult


def login(db: Session, user_name: str, raw_password: str) -> LoginResult:
    user = user_repo.get_by_name(db, user_name)
    if user is None or user.user_is_alive == 0:
        raise BusinessError("用户名不存在或已被冻结")
    if not verify_legacy_password(raw_password, user.user_password, user.user_salt or ""):
        raise BusinessError("密码错误")
    token = create_access_token(user.user_id, extra={"name": user.user_name})
    return LoginResult(
        access_token=token,
        user_id=user.user_id,
        user_name=user.user_name,
        rating_num=user_repo.rating_count(db, user.user_id),
    )


def register(db: Session, user_name: str, raw_password: str) -> LoginResult:
    if user_repo.get_by_name(db, user_name) is not None:
        raise BusinessError("用户名已存在")
    salt = secrets.token_hex(8)
    hashed = md5_with_salt(raw_password, salt)
    user = user_repo.create_user(db, user_name, hashed, salt)
    token = create_access_token(user.user_id, extra={"name": user.user_name})
    return LoginResult(access_token=token, user_id=user.user_id, user_name=user.user_name)
