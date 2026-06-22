"""对话推荐路由。"""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.chatbot import service
from app.chatbot.schemas import ChatReply, MessageCreate, SessionCreate, SessionInfo
from app.core.deps import CurrentUserDep, DbDep, OptionalUserDep
from app.core.response import ApiResponse
from app.models import ChatSession

router = APIRouter(prefix="/chat", tags=["对话推荐"])


@router.get("/sessions", response_model=ApiResponse[list[SessionInfo]])
def list_sessions(db: DbDep, user_id: CurrentUserDep):
    """返回当前登录用户的所有会话，按最近更新倒序。"""
    return ApiResponse.ok(service.list_sessions(db, user_id))


@router.post("/sessions", response_model=ApiResponse[SessionInfo])
def create_session(body: SessionCreate, db: DbDep, user_id: OptionalUserDep):
    return ApiResponse.ok(service.create_session(db, user_id, body.title, body.mode))


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
def delete_session(session_id: str, db: DbDep, user_id: CurrentUserDep):
    """删除会话及其全部消息和 trace 记录（仅会话所有者可删）。"""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除他人会话")
    service.delete_session(db, session_id)
    return ApiResponse.ok(None)


@router.get("/sessions/{session_id}/messages", response_model=ApiResponse)
def list_messages(session_id: str, db: DbDep):
    return ApiResponse.ok(service.list_messages(db, session_id))


@router.post("/sessions/{session_id}/messages", response_model=ApiResponse[ChatReply])
def post_message(session_id: str, body: MessageCreate, db: DbDep, user_id: OptionalUserDep):
    return ApiResponse.ok(service.post_message(db, session_id, user_id, body.content))


@router.post("/sessions/{session_id}/messages/stream")
def post_message_stream(session_id: str, body: MessageCreate, db: DbDep, user_id: OptionalUserDep):
    """SSE 流式端点：实时推送 Agent 各步骤进度，最后推送完整推荐结果。

    每条 SSE 消息格式：
      data: {"type": "step"|"tool"|"result", "message": "...", "data": {...}}

    前端用 fetch + ReadableStream 消费（EventSource 不支持 POST）。
    """

    def generate():
        for event in service.stream_message(db, session_id, user_id, body.content):
            # 只向前端推送展示字段，不暴露 trace 字段
            payload = {"type": event.type, "message": event.message, "data": event.data}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
