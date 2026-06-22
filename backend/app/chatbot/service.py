"""对话推荐服务：接入 Agent 流程。

用户每条消息经过完整 Agent pipeline：
  意图解析 → 多路召回 → LLM 重排解释 → Memory 写入
会话消息同时入库，保留多轮上下文。关键推理步骤写入 agent_trace。
"""
import json
import uuid
from collections.abc import Generator
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chatbot.agent import AgentEvent, run_agent, run_agent_stream
from app.chatbot.schemas import ChatReply, MessageInfo, SessionInfo
from app.core.exceptions import BusinessError
from app.core.llm_provider import get_llm_provider
from app.models import AgentTrace, ChatMessage, ChatSession


def create_session(db: Session, user_id: int | None, title: str | None, mode: str = "chatbot") -> SessionInfo:
    session = ChatSession(
        session_id=uuid.uuid4().hex,
        user_id=user_id,
        title=title or "新会话",
        mode=mode,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionInfo.model_validate(session)


def list_sessions(db: Session, user_id: int) -> list[SessionInfo]:
    """返回用户的所有会话，按最近更新倒序。"""
    rows = db.scalars(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    ).all()
    return [SessionInfo.model_validate(r) for r in rows]


def delete_session(db: Session, session_id: str) -> None:
    """删除会话及其所有消息和 trace 记录。"""
    db.query(AgentTrace).filter(AgentTrace.session_id == session_id).delete()
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    session = db.get(ChatSession, session_id)
    if session:
        db.delete(session)
    db.commit()


def list_messages(db: Session, session_id: str) -> list[MessageInfo]:
    rows = db.scalars(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.msg_id)
    ).all()
    return [MessageInfo.model_validate(r) for r in rows]


def _history_for_llm(db: Session, session_id: str) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in list_messages(db, session_id)]


def _save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    user_id: int | None = None,
    extra_data: str | None = None,
) -> ChatMessage:
    """保存消息并返回 ORM 对象（带 msg_id）。"""
    now = datetime.now()
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        user_id=user_id,
        extra_data=extra_data,
        created_at=now,
    )
    db.add(msg)
    db.flush()   # 获取自增 msg_id，不单独 commit
    # 同步更新会话的 updated_at（用 Python 时间，避免依赖 server_default 的延迟回填）
    db.query(ChatSession).filter(ChatSession.session_id == session_id).update(
        {"updated_at": now},
        synchronize_session=False,
    )
    db.commit()
    return msg


def _save_traces(db: Session, session_id: str, msg_id: int, pending: list[AgentEvent]) -> None:
    """将 step_type 非空的事件批量写入 agent_trace。"""
    if not pending:
        return
    db.bulk_save_objects([
        AgentTrace(
            session_id=session_id,
            msg_id=msg_id,
            step_type=e.step_type,
            input=e.trace_input or None,
            output=e.trace_output or None,
        )
        for e in pending
    ])
    db.commit()


def stream_message(
    db: Session, session_id: str, user_id: int | None, content: str
) -> Generator[AgentEvent, None, None]:
    """流式版本：保存消息后运行 Agent，每步 yield AgentEvent，结束后写 trace。"""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise BusinessError("会话不存在")

    _save_message(db, session_id, "user", content, user_id=user_id)
    history = _history_for_llm(db, session_id)
    llm = get_llm_provider()

    reply_text = ""
    recommendations_json: str | None = None
    trace_pending: list[AgentEvent] = []

    for event in run_agent_stream(db, llm, session_id, user_id, content, history):
        if event.type == "result":
            reply_text = event.data.get("reply", "")
            recs = event.data.get("recommendations")
            if recs:
                recommendations_json = json.dumps(recs, ensure_ascii=False)
        if event.step_type:
            trace_pending.append(event)
        yield event

    if reply_text:
        assistant_msg = _save_message(
            db, session_id, "assistant", reply_text,
            user_id=user_id, extra_data=recommendations_json,
        )
        _save_traces(db, session_id, assistant_msg.msg_id, trace_pending)


def post_message(db: Session, session_id: str, user_id: int | None, content: str) -> ChatReply:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise BusinessError("会话不存在")

    _save_message(db, session_id, "user", content, user_id=user_id)
    history = _history_for_llm(db, session_id)

    llm = get_llm_provider()
    result = run_agent(db, llm, session_id, user_id, content, history)

    recs_json = json.dumps([r.model_dump() for r in result.recommendations], ensure_ascii=False) if result.recommendations else None
    _save_message(db, session_id, "assistant", result.reply, user_id=user_id, extra_data=recs_json)

    return result
