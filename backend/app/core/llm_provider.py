"""LLM Provider 抽象层（策略 + 工厂）。

替代旧 chat.vue 前端直连讯飞星火（API Key 暴露在前端的安全隐患）。
所有 LLM 调用统一走后端，密钥仅存在于后端环境变量。

支持 Provider：
  mock    - 本地开发无需密钥
  openai  - OpenAI / 任意兼容接口（One API 等中转）
  volcano - 字节跳动火山引擎 Ark（豆包系列）
  spark   - 讯飞星火（新版 HTTP API，兼容 OpenAI 格式）

通过 LLM_PROVIDER 环境变量切换，未配置密钥时自动回退 mock。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import httpx

from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], system: str | None = None) -> str: ...


class MockProvider(LLMProvider):
    """无需任何密钥的占位实现，便于本地开发与演示。"""

    def chat(self, messages: list[dict], system: str | None = None) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return (
            f"我已理解你的观影需求：「{last_user}」。"
            "已为你在右侧整理了几部可能合适的电影，可点击查看详情或反馈喜好。"
        )


class _OpenAICompatProvider(LLMProvider):
    """通用 OpenAI Chat Completions 兼容实现，子类只需传入连接参数。"""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def chat(self, messages: list[dict], system: str | None = None) -> str:
        payload_messages = ([{"role": "system", "content": system}] if system else []) + messages
        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "messages": payload_messages},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class OpenAIProvider(_OpenAICompatProvider):
    """OpenAI 官方接口（或 One API 等兼容中转）。"""

    def __init__(self) -> None:
        super().__init__(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )


class VolcanoProvider(_OpenAICompatProvider):
    """字节跳动火山引擎 Ark —— 豆包系列模型。

    接口文档：https://www.volcengine.com/docs/82379/1494384
    鉴权：Authorization: Bearer <ARK_API_KEY>
    model 填写 Endpoint ID（ep-xxxx）或 Model ID（doubao-seed-2-0-lite-...）。
    """

    def __init__(self) -> None:
        super().__init__(
            api_key=settings.volcano_api_key,
            base_url=settings.volcano_base_url,
            model=settings.volcano_model,
        )


class SparkProvider(_OpenAICompatProvider):
    """讯飞星火大模型（新版 HTTP REST API，兼容 OpenAI Chat Completions 格式）。

    接口文档：https://www.xfyun.cn/doc/spark/HTTP调用文档.html
    鉴权：Authorization: Bearer <SPARK_API_KEY>  (APIPassword 格式)
    """

    def __init__(self) -> None:
        super().__init__(
            api_key=settings.spark_api_password,
            base_url=settings.spark_base_url,
            model=settings.spark_model,
        )


# ------------------------------------------------------------------
# 注册表：provider 名称 → (Provider 类, 是否已配置密钥的检查函数)
# ------------------------------------------------------------------
_REGISTRY: dict[str, tuple[type[LLMProvider], "Callable[[], bool]"]] = {
    "openai": (OpenAIProvider, lambda: bool(settings.openai_api_key)),
    "volcano": (VolcanoProvider, lambda: bool(settings.volcano_api_key)),
    "spark": (SparkProvider, lambda: bool(settings.spark_api_password)),
}


def get_llm_provider() -> LLMProvider:
    """工厂函数：根据 LLM_PROVIDER 环境变量返回对应实例，未配置密钥时回退 mock。"""
    name = settings.llm_provider.lower()
    if name in _REGISTRY:
        cls, is_configured = _REGISTRY[name]
        if is_configured():
            return cls()
    return MockProvider()
