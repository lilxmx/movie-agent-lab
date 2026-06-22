"""TF Serving 客户端，迁移自旧 ModelServing.java，地址改为配置化。

TF_SERVING_ENABLED=false 时返回 None，由调用方走本地回退打分，
便于在无模型部署的环境下开发联调。
"""
import httpx

from app.core.config import settings

_URLS = {
    "NeuralCF": settings.tf_serving_neuralcf_url,
    "DeepCrossing": settings.tf_serving_deepcrossing_url,
    "WideAndDeep": settings.tf_serving_wideanddeep_url,
}


def predict(model: str, instances: list[dict]) -> list[float] | None:
    if not settings.tf_serving_enabled:
        return None
    url = _URLS.get(model)
    if not url:
        return None
    try:
        resp = httpx.post(url, json={"instances": instances}, timeout=5.0)
        resp.raise_for_status()
        predictions = resp.json().get("predictions", [])
        return [float(p[0]) if isinstance(p, list) else float(p) for p in predictions]
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return None
