"""推荐策略注册器。传统推荐与 Agent 推荐通过 mode 注册不同实现，解耦调用方。"""
from __future__ import annotations

from app.core.exceptions import BusinessError
from app.recsys.contracts import Recommender


class RecommenderRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, Recommender] = {}

    def register(self, mode: str, recommender: Recommender) -> None:
        self._registry[mode] = recommender

    def get(self, mode: str) -> Recommender:
        if mode not in self._registry:
            raise BusinessError(f"未知推荐模式: {mode}")
        return self._registry[mode]

    def modes(self) -> list[str]:
        return list(self._registry)


registry = RecommenderRegistry()
