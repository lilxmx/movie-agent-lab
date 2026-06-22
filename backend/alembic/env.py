"""Alembic 环境。仅管理 AI-native 新表，不触碰旧业务表。"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
from app.models import ai  # noqa: F401  确保新表元数据被加载

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# 只管理这些 AI-native 表，避免 autogenerate 误删旧表
_MANAGED_TABLES = {
    "recommendation_runs",
    "chat_sessions",
    "chat_messages",
    "agent_memories",
}


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in _MANAGED_TABLES
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
