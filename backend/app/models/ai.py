"""AI-native 新增表（Phase 7 由 Alembic 创建，不影响旧表）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecommendationRun(Base):
    """每次推荐调用的可追溯日志。"""

    __tablename__ = "recommendation_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    mode: Mapped[str] = mapped_column(String(32))  # classic / agent
    scene: Mapped[str | None] = mapped_column(String(32))
    model_name: Mapped[str | None] = mapped_column(String(64))
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(32), server_default="chatbot")  # chatbot / agent_recommend / traditional_recommend
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    msg_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(16))  # user / assistant / system / tool
    content: Mapped[str] = mapped_column(Text)
    extra_data: Mapped[str | None] = mapped_column(Text)  # JSON, 存储推荐结果等附加数据
    model_name: Mapped[str | None] = mapped_column(String(64))
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgentTrace(Base):
    """Agent 每步推理的结构化追踪记录，用于回放、bad case 分析、训练数据构造。"""

    __tablename__ = "agent_trace"

    trace_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("chat_sessions.session_id"), index=True)
    msg_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chat_messages.msg_id"), index=True)
    step_type: Mapped[str] = mapped_column(String(32))  # retrieve_memory / call_tool / recommend / reflect
    input: Mapped[str | None] = mapped_column(Text)
    output: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    memory_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    memory_type: Mapped[str] = mapped_column(String(16))  # short / long / preference
    content: Mapped[str] = mapped_column(Text)
    embedding_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
