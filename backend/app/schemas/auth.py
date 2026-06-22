"""鉴权相关 schema。"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    user_name: str
    user_password: str


class RegisterRequest(BaseModel):
    user_name: str
    user_password: str


class LoginResult(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_name: str
    rating_num: int = 0


class CurrentUser(BaseModel):
    user_id: int
    user_name: str
