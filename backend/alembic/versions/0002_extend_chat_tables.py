"""extend chat tables and add agent_trace

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-22

扩展 chat_sessions / chat_messages，新增 agent_trace 追踪表。
不修改旧业务表。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # chat_sessions：新增 mode 字段
    op.add_column(
        "chat_sessions",
        sa.Column("mode", sa.String(32), nullable=False, server_default="chatbot"),
    )

    # chat_messages：新增 user_id / model_name / token_count
    op.add_column("chat_messages", sa.Column("user_id", sa.Integer, nullable=True))
    op.add_column("chat_messages", sa.Column("model_name", sa.String(64), nullable=True))
    op.add_column("chat_messages", sa.Column("token_count", sa.Integer, nullable=True))

    # 新增 agent_trace 表
    op.create_table(
        "agent_trace",
        sa.Column("trace_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("chat_sessions.session_id"), nullable=False, index=True),
        sa.Column("msg_id", sa.Integer, sa.ForeignKey("chat_messages.msg_id"), nullable=True, index=True),
        sa.Column("step_type", sa.String(32), nullable=False),  # retrieve_memory / call_tool / recommend / reflect
        sa.Column("input", sa.Text, nullable=True),
        sa.Column("output", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_trace")
    op.drop_column("chat_messages", "token_count")
    op.drop_column("chat_messages", "model_name")
    op.drop_column("chat_messages", "user_id")
    op.drop_column("chat_sessions", "mode")
