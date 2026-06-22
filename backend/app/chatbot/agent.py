"""Conversational Recommendation Agent 主流程。

Pipeline:
  1. extract_intent  ─ LLM 解析用户意图
  2. recall          ─ 多路工具召回 30-50 部候选电影
  3. rerank          ─ LLM 从候选中选 Top-K 并生成自然语言解释
  4. update_memory   ─ 把本轮偏好写入 agent_memories 持久化
  5. 返回 (reply, rec_items)

提供两个入口：
  run_agent        ─ 普通同步调用，一次性返回 ChatReply
  run_agent_stream ─ 生成器，每步 yield AgentEvent，最后 yield 包含结果的 done 事件
                     用于 SSE 端点，让前端实时看到 Agent 在做什么。
"""
from __future__ import annotations

import json
import re
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.chatbot.intent import UserIntent, extract_intent
from app.chatbot.schemas import ChatReply
from app.chatbot.tools import (
    Candidate,
    recall_candidates,
    tool_genre_recall,
    tool_hot_fallback,
    tool_personalized_recall,
    tool_semantic_search,
    tool_similar_by_ref,
)
from app.core.llm_provider import LLMProvider, MockProvider
from app.models import AgentMemory
from app.repositories import movie_repo
from app.recsys.contracts import RecItem


# ---- 进度事件 ----

@dataclass
class AgentEvent:
    """SSE 进度事件，前端根据 type 决定展示方式。

    step_type 非空时，service 层会将该事件写入 agent_trace 表（追踪用）。
    step_type 取值：retrieve_memory / call_tool / recommend / reflect
    """
    type: str                    # step | tool | result | error
    message: str = ""            # 展示给用户的可读文字
    data: dict = field(default_factory=dict)   # type=result 时携带完整结果
    step_type: str | None = None  # 非空时写入 agent_trace
    trace_input: str = ""         # 该步骤的输入摘要
    trace_output: str = ""        # 该步骤的输出摘要


# ---- 重排与解释 ----

_TOP_K = 6

_RERANK_SYSTEM = "你是电影推荐助手，只输出 JSON，不要解释。"

_RERANK_PROMPT_TMPL = """\
用户需求：{query}

候选电影（JSON 数组，每条含 id/title/genres/avg_rating/sources）：
{candidates_json}

请从候选中选出最符合需求的至多 {top_k} 部，输出 JSON：
[
  {{"id": <movie_id>, "reason": "<一句话推荐理由>"}},
  ...
]
按推荐优先级排列，只输出 JSON 数组，不要其他文字。"""


def _rerank_with_llm(
    llm: LLMProvider,
    intent: UserIntent,
    candidates: list[Candidate],
) -> list[tuple[int, str]]:
    """让 LLM 对候选重排并生成理由。返回 [(movie_id, reason), ...]。"""
    if isinstance(llm, MockProvider) or not candidates:
        # Mock：按工具命中数 + 平均分排序，生成模板理由
        return _mock_rerank(intent, candidates)

    cand_json = json.dumps(
        [
            {
                "id": c.movie_id,
                "title": c.title,
                "genres": c.genres,
                "avg_rating": c.avg_rating,
                "sources": c.sources,
            }
            for c in candidates[:30]  # 最多传 30 条给 LLM，节省 token
        ],
        ensure_ascii=False,
    )
    prompt = _RERANK_PROMPT_TMPL.format(
        query=intent.raw_query,
        candidates_json=cand_json,
        top_k=_TOP_K,
    )
    try:
        raw = llm.chat(
            [{"role": "user", "content": prompt}],
            system=_RERANK_SYSTEM,
        )
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return _mock_rerank(intent, candidates)
        items = json.loads(match.group())
        return [(int(x["id"]), str(x.get("reason", "符合你的偏好"))) for x in items if "id" in x]
    except Exception:
        return _mock_rerank(intent, candidates)


def _mock_rerank(intent: UserIntent, candidates: list[Candidate]) -> list[tuple[int, str]]:
    """不依赖 LLM 的重排：按工具命中数降序，再按平均分排。"""
    scored = sorted(
        candidates,
        key=lambda c: (len(c.sources), c.avg_rating),
        reverse=True,
    )
    reasons = _build_mock_reasons(intent)
    return [(c.movie_id, reasons[i % len(reasons)]) for i, c in enumerate(scored[:_TOP_K])]


def _build_mock_reasons(intent: UserIntent) -> list[str]:
    parts: list[str] = []
    if intent.preferred_genres:
        parts.append(f"{'、'.join(intent.preferred_genres)}题材")
    if intent.preferred_mood:
        parts.append(f"{'、'.join(intent.preferred_mood)}风格")
    if intent.reference_movies:
        parts.append(f"与《{'》《'.join(intent.reference_movies)}》风格相近")
    base = "、".join(parts) if parts else "热门推荐"
    return [
        f"符合你对{base}的偏好",
        f"口碑上乘，{base}爱好者推荐",
        f"节奏紧凑，适合喜欢{base}的观众",
        f"经典之作，{base}必看",
        f"评分较高，{base}中的佼佼者",
        f"与你的口味匹配，{base}代表作",
    ]


_MAX_HISTORY_TURNS = 3

# ---- 普通对话回复（非推荐意图）----

_CHAT_SYSTEM = "你是一个友好的电影对话助手，用简洁自然的中文回答用户的问题，不超过 200 字。"


def _generate_chat_reply(llm: LLMProvider, history: list[dict], query: str) -> str:
    """非推荐意图时，直接用 LLM 生成普通对话回复。"""
    if isinstance(llm, MockProvider):
        return "你好！有什么我可以帮你的吗？如果想看电影推荐，告诉我你的偏好吧。"
    messages = history[-(2 * _MAX_HISTORY_TURNS):]
    messages = messages + [{"role": "user", "content": query}]
    try:
        return llm.chat(messages, system=_CHAT_SYSTEM)
    except Exception:
        return "你好！有什么我可以帮你的吗？如果想看电影推荐，告诉我你的偏好吧。"

# ---- 生成回复文本 ----

_REPLY_SYSTEM = "你是电影推荐助手，用简洁自然的中文给出推荐说明，不超过 120 字。"

_REPLY_PROMPT_TMPL = """\
用户说："{query}"

你为他推荐了：{titles}

请用一段话自然地介绍为什么推荐这几部（不要列清单，不要重复片名太多次）。"""


def _generate_reply(
    llm: LLMProvider,
    intent: UserIntent,
    top_items: list[tuple[int, str]],
    candidates: list[Candidate],
) -> str:
    if isinstance(llm, MockProvider) or not top_items:
        return _mock_reply(intent, top_items, candidates)

    id_map = {c.movie_id: c.title for c in candidates}
    titles = "、".join(f"《{id_map.get(mid, str(mid))}》" for mid, _ in top_items[:3])
    prompt = _REPLY_PROMPT_TMPL.format(query=intent.raw_query, titles=titles)
    try:
        return llm.chat([{"role": "user", "content": prompt}], system=_REPLY_SYSTEM)
    except Exception:
        return _mock_reply(intent, top_items, candidates)


def _mock_reply(
    intent: UserIntent,
    top_items: list[tuple[int, str]],
    candidates: list[Candidate],
) -> str:
    if not top_items:
        return "暂时没有找到完全符合的电影，右侧是一些热门推荐，希望对你有帮助。"
    id_map = {c.movie_id: c.title for c in candidates}
    titles = "、".join(f"《{id_map.get(mid, str(mid))}》" for mid, _ in top_items[:2])
    moods = "、".join(intent.preferred_mood[:2]) if intent.preferred_mood else ""
    genres = "、".join(intent.preferred_genres[:2]) if intent.preferred_genres else ""
    desc = moods or genres or "你的偏好"
    need_more = "\n\n还有其他要求吗？比如想要更轻松的，或者不喜欢某种风格？" if not intent.has_signal else ""
    return f"根据你的需求，我推荐了{titles}等几部{desc}风格的电影，详细推荐理由可以在右侧查看。{need_more}"


# ---- Memory 更新 ----

def _update_memory(db: Session, user_id: int, intent: UserIntent) -> None:
    """把本次对话中提取的偏好写入 agent_memories 表。"""
    entries: list[dict] = []
    if intent.preferred_genres:
        entries.append({"type": "preference", "content": f"喜欢类型：{'、'.join(intent.preferred_genres)}"})
    if intent.preferred_mood:
        entries.append({"type": "preference", "content": f"风格偏好：{'、'.join(intent.preferred_mood)}"})
    if intent.reference_movies:
        entries.append({"type": "preference", "content": f"参考电影：{'、'.join(intent.reference_movies)}"})
    if intent.constraints:
        for k, v in intent.constraints.items():
            entries.append({"type": "preference", "content": f"{k}：{v}"})

    for e in entries:
        db.add(AgentMemory(
            user_id=user_id,
            memory_type=e["type"],
            content=e["content"],
            created_at=datetime.now(),
        ))
    if entries:
        db.commit()


# ---- 工具名称到中文描述的映射 ----

def _intent_summary(intent: UserIntent) -> str:
    parts = []
    if intent.reference_movies:
        parts.append(f"参考《{'》《'.join(intent.reference_movies)}》")
    if intent.preferred_genres:
        parts.append("、".join(intent.preferred_genres) + "题材")
    if intent.preferred_mood:
        parts.append("、".join(intent.preferred_mood) + "风格")
    if intent.constraints:
        for k, v in intent.constraints.items():
            parts.append(f"{k}={v}")
    return "，".join(parts) if parts else "通用偏好"


def _build_rec_items(top_items: list[tuple[int, str]], candidates: list[Candidate]) -> list[RecItem]:
    id_map = {c.movie_id: c for c in candidates}
    result: list[RecItem] = []
    for movie_id, reason in top_items:
        c = id_map.get(movie_id)
        if c:
            result.append(RecItem(
                movie_id=c.movie_id,
                title=c.title,
                score=round(c.avg_rating, 2),
                reason=reason,
                source="agent",
            ))
    return result


# ---- Agent 主入口（普通同步版，保持兼容）----

def run_agent(
    db: Session,
    llm: LLMProvider,
    session_id: str,
    user_id: int | None,
    query: str,
    history: list[dict],
) -> ChatReply:
    """完整 Agent pipeline，一次性返回 ChatReply（非流式）。"""
    intent = extract_intent(llm, query, history)

    if not intent.is_recommend:
        reply_text = _generate_chat_reply(llm, history, query)
        return ChatReply(session_id=session_id, reply=reply_text, recommendations=[])

    candidates = recall_candidates(db, intent, user_id, max_candidates=40)
    top_items = _rerank_with_llm(llm, intent, candidates)
    reply_text = _generate_reply(llm, intent, top_items, candidates)
    if user_id and intent.has_signal:
        try:
            _update_memory(db, user_id, intent)
        except Exception:
            pass
    return ChatReply(
        session_id=session_id,
        reply=reply_text,
        recommendations=_build_rec_items(top_items, candidates),
    )


# ---- Agent 流式入口（SSE 版）----

def run_agent_stream(
    db: Session,
    llm: LLMProvider,
    session_id: str,
    user_id: int | None,
    query: str,
    history: list[dict],
) -> Generator[AgentEvent, None, None]:
    """流式 Agent pipeline，每步 yield AgentEvent，最后 yield type=result 携带完整数据。"""

    # Step 1: 意图解析
    yield AgentEvent(type="step", message="🔍 正在解析你的意图...")
    intent = extract_intent(llm, query, history)

    # 普通对话（非推荐），跳过召回/重排流程
    if not intent.is_recommend:
        yield AgentEvent(type="step", message="💬 识别为普通对话，直接回复...")
        reply_text = _generate_chat_reply(llm, history, query)
        reply = ChatReply(session_id=session_id, reply=reply_text, recommendations=[])
        yield AgentEvent(type="result", message="done", data=reply.model_dump())
        return

    yield AgentEvent(
        type="step",
        message=f"✅ 意图识别：{_intent_summary(intent)}",
        step_type="retrieve_memory",
        trace_input=query,
        trace_output=json.dumps(
            {"genres": intent.preferred_genres, "mood": intent.preferred_mood,
             "refs": intent.reference_movies, "constraints": intent.constraints},
            ensure_ascii=False,
        ),
    )

    # Step 2: 逐工具召回，边召回边报告
    yield AgentEvent(type="step", message="📡 多路召回候选电影...")
    id_sources: dict[int, list[str]] = {}

    def add(ids: list[int], source: str) -> None:
        for mid in ids:
            id_sources.setdefault(mid, []).append(source)

    if intent.reference_movies:
        yield AgentEvent(type="tool", message=f"🔧 相似召回：《{'》《'.join(intent.reference_movies)}》相关...")
        ids = tool_similar_by_ref(db, intent.reference_movies, 20)
        add(ids, "相似召回")
        yield AgentEvent(type="tool", message=f"   └ 找到 {len(set(ids))} 部相似电影")

    if intent.preferred_genres:
        genres_str = "、".join(intent.preferred_genres)
        yield AgentEvent(type="tool", message=f"🔧 类型召回：{genres_str}...")
        ids = tool_genre_recall(db, intent.preferred_genres, 15)
        add(ids, "类型召回")
        yield AgentEvent(type="tool", message=f"   └ 找到 {len(set(ids))} 部{genres_str}电影")

    if intent.preferred_mood or intent.preferred_genres:
        kws = intent.preferred_genres + intent.preferred_mood
        yield AgentEvent(type="tool", message=f"🔧 语义检索：{' '.join(kws[:3])}...")
        ids = tool_semantic_search(db, kws, 15)
        add(ids, "语义检索")
        yield AgentEvent(type="tool", message=f"   └ 语义匹配 {len(set(ids))} 部")

    if user_id:
        yield AgentEvent(type="tool", message="🔧 个性化召回：基于你的观影历史...")
        ids = tool_personalized_recall(db, user_id, 20)
        add(ids, "个性化")
        yield AgentEvent(type="tool", message=f"   └ 个性化召回 {len(set(ids))} 部")

    if len(id_sources) < 10:
        yield AgentEvent(type="tool", message="🔧 热门兜底召回...")
        ids = tool_hot_fallback(db, 20)
        add(ids, "热门")
        yield AgentEvent(type="tool", message=f"   └ 补充 {len(set(ids))} 部热门电影")

    total = len(id_sources)
    tools_used = list({s for sources in id_sources.values() for s in sources})
    yield AgentEvent(
        type="step",
        message=f"📋 合并去重，共 {total} 部候选",
        step_type="call_tool",
        trace_input=json.dumps({"tools": tools_used}, ensure_ascii=False),
        trace_output=f"共 {total} 部候选电影",
    )

    # 构建 Candidate 列表（同 recall_candidates 的后半部分）
    ranked_ids = sorted(id_sources, key=lambda mid: len(id_sources[mid]), reverse=True)[:40]
    movies = movie_repo.movies_by_ids(db, ranked_ids)
    stats = movie_repo.statistics_by_ids(db, ranked_ids)
    candidates: list[Candidate] = []
    for mid in ranked_ids:
        m = movies.get(mid)
        if not m:
            continue
        c = Candidate(m, id_sources[mid])
        stat = stats.get(mid)
        c.avg_rating = round(stat.movie_avg_rating or 0.0, 2) if stat else 0.0
        candidates.append(c)

    # Step 3: LLM 重排
    is_mock = isinstance(llm, MockProvider)
    yield AgentEvent(
        type="step",
        message="🤖 LLM 重排候选电影..." if not is_mock else "📊 按相关度排序（关键词模式）...",
    )
    top_items = _rerank_with_llm(llm, intent, candidates)

    # Step 4: 生成回复
    yield AgentEvent(
        type="step",
        message="✍️ 生成推荐说明..." if not is_mock else "✍️ 组装推荐结果...",
    )
    reply_text = _generate_reply(llm, intent, top_items, candidates)
    yield AgentEvent(
        type="step",
        message=f"✨ 推荐完成，共 {len(top_items)} 部",
        step_type="recommend",
        trace_input=f"候选 {len(candidates)} 部",
        trace_output=json.dumps(
            [{"id": mid, "reason": r} for mid, r in top_items],
            ensure_ascii=False,
        ),
    )

    # Step 5: Memory
    if user_id and intent.has_signal:
        try:
            _update_memory(db, user_id, intent)
            pref_summary = _intent_summary(intent)
            yield AgentEvent(
                type="step",
                message="💾 偏好已更新到你的画像",
                step_type="reflect",
                trace_input=pref_summary,
                trace_output="偏好写入 agent_memories",
            )
        except Exception:
            pass

    # 最终结果
    reply = ChatReply(
        session_id=session_id,
        reply=reply_text,
        recommendations=_build_rec_items(top_items, candidates),
    )
    yield AgentEvent(type="result", message="done", data=reply.model_dump())
