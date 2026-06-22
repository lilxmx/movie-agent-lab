"""对话推荐 schema。"""
from datetime import datetime

from pydantic import BaseModel

from app.recsys.contracts import RecItem


class SessionCreate(BaseModel):
    title: str | None = None
    mode: str = "chatbot"  # chatbot / agent_recommend / traditional_recommend


class SessionInfo(BaseModel):
    session_id: str
    title: str | None = None
    mode: str = "chatbot"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageInfo(BaseModel):
    role: str
    content: str
    extra_data: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChatReply(BaseModel):
    """一次对话推荐的返回：助手回复 + 关联推荐电影。"""

    session_id: str
    reply: str
    recommendations: list[RecItem] = []
