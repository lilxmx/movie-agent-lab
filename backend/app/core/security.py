"""JWT 鉴权与密码哈希，替代旧项目的 Redis token + Md5Util。

兼容旧库：旧用户密码为 MD5(password + salt)。登录校验时若用户记录带 salt，
则按旧规则校验，保证存量用户可直接登录；新注册用户也沿用同一规则以兼容旧库结构。
"""
import hashlib
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


def md5_with_salt(raw_password: str, salt: str) -> str:
    return hashlib.md5(f"{raw_password}{salt}".encode()).hexdigest()


def verify_legacy_password(raw_password: str, hashed: str, salt: str) -> bool:
    return md5_with_salt(raw_password, salt) == hashed


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
