"""集中式配置，所有外部地址、密钥、CDN 路径均来自环境变量，杜绝硬编码。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Movie Agent Lab"
    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "integratedrecsys"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    tf_serving_neuralcf_url: str = ""
    tf_serving_deepcrossing_url: str = ""
    tf_serving_wideanddeep_url: str = ""
    tf_serving_enabled: bool = False

    # 可选：mock / openai / volcano / spark
    llm_provider: str = "mock"

    # OpenAI 官方 / One API 兼容中转
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # 字节跳动火山引擎 Ark（豆包系列）
    volcano_api_key: str = ""
    volcano_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcano_model: str = "doubao-seed-2-0-lite-250428"

    # 讯飞星火（新版 HTTP API，APIPassword 鉴权）
    # 旧版 WebSocket HMAC 鉴权字段保留，供其他工具使用
    spark_api_app_id: str = ""
    spark_api_key: str = ""
    spark_api_secret: str = ""
    # 新版 HTTP API：控制台 → API Key → APIPassword
    spark_api_password: str = ""
    spark_base_url: str = "https://spark-api-open.xf-yun.com/v1"
    spark_model: str = "generalv3.5"

    poster_cdn_url: str = "http://127.0.0.1/posters/"
    poster_bg_cdn_url: str = "http://127.0.0.1/poster_background/"
    cast_poster_cdn_url: str = "http://127.0.0.1/cast_poster/"

    vector_store_provider: str = "memory"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
