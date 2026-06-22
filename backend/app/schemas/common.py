"""通用分页 schema。"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Paged(BaseModel, Generic[T]):
    items: list[T]
    total: int
