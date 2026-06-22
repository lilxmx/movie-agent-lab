"""统一响应包装，替代旧项目的 ResultWrapper。"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "ApiResponse":
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(cls, message: str, code: int = 1) -> "ApiResponse":
        return cls(code=code, message=message, data=None)
