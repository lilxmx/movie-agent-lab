"""create AI-native tables

Revision ID: 0001
Revises:
Create Date: 2026-06-22

新增 AI-native 表，不修改任何旧业务表。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_runs",
        sa.Column("run_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, index=True),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("scene", sa.String(32)),
        sa.Column("model_name", sa.String(64)),
        sa.Column("trace_id", sa.String(64), index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "chat_sessions",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer, index=True),
        sa.Column("title", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "chat_messages",
        sa.Column("msg_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), index=True, nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "agent_memories",
        sa.Column("memory_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, index=True, nullable=False),
        sa.Column("memory_type", sa.String(16), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_memories")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("recommendation_runs")
