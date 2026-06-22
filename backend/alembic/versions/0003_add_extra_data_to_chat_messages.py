"""add extra_data to chat_messages

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-22

为 chat_messages 添加 extra_data 字段，用于持久化 assistant 消息附带的推荐结果 JSON。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("extra_data", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("chat_messages", "extra_data")
