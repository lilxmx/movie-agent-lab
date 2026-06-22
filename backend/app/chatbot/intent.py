"""用户意图解析：将自然语言转成结构化意图。

优先调用 LLM 返回 JSON；LLM 为 mock 或解析失败时，
用正则关键词提取作为兜底，保证 Agent 流程始终可运行。

多轮对话支持：extract_intent 会将最近几轮历史作为上下文传给 LLM，
让 LLM 能理解"不要太长的""换一种风格"等精炼/追加需求。
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from app.core.llm_provider import LLMProvider, MockProvider

logger = logging.getLogger(__name__)

# ---- 类型定义 ----

@dataclass
class UserIntent:
    raw_query: str
    intent_type: str = "recommend"                              # recommend / chat
    reference_movies: list[str] = field(default_factory=list)   # 参考电影
    preferred_genres: list[str] = field(default_factory=list)   # 偏好类型
    preferred_mood: list[str] = field(default_factory=list)     # 情感/风格词
    constraints: dict = field(default_factory=dict)             # 约束条件
    need_clarification: bool = False                            # 是否需要追问

    @property
    def is_recommend(self) -> bool:
        return self.intent_type == "recommend"

    @property
    def has_signal(self) -> bool:
        """是否有足够的信号可以召回候选。"""
        return bool(
            self.reference_movies or self.preferred_genres or self.preferred_mood
        )


# ---- LLM 意图解析 ----

# 作为 system 角色传入，给 LLM 明确的任务定义
_INTENT_SYSTEM = """\
你是一个电影对话助手。请结合对话历史，分析用户最新输入的意图。
只输出 JSON，不要包含其他文字。

JSON 结构：
{
  "intent_type": "recommend",    // "recommend"=电影推荐请求, "chat"=普通对话（问好/感谢/问知识等）
  "reference_movies": [],        // 用户提到的参考电影（中文名）
  "preferred_genres": [],        // 偏好类型，如 科幻、爱情、悬疑、动作、喜剧、恐怖、动画、剧情
  "preferred_mood": [],          // 风格/情感词，如 烧脑、治愈、轻松、反转、紧张、催泪、热血
  "constraints": {},             // 约束，如 {"duration": "short"}（short<100min, long>150min）
  "need_clarification": false    // 信息不足需要追问时为 true（仅 intent_type=recommend 时有效）
}"""

# 多轮对话时传给 LLM 的最大历史轮数（每轮 = user + assistant 各 1 条）
_MAX_HISTORY_TURNS = 3


def extract_intent(llm: LLMProvider, query: str, history: list[dict]) -> UserIntent:
    """调用 LLM 解析意图，并将最近几轮历史作为上下文传入；mock 或失败时退回关键词匹配。

    history 此时已包含本轮用户消息（service 层先存后读），
    因此取 history[:-1] 作为对话上文，再追加当前 query。
    这样 LLM 能理解"不要太长"/"再换种风格"等多轮精炼需求。
    """
    if isinstance(llm, MockProvider):
        return _keyword_fallback(query)

    # 取最近 N 轮上文（去掉 history 末尾的当前 user 消息，避免重复）
    prev_turns = history[:-1]
    context = prev_turns[-(2 * _MAX_HISTORY_TURNS):]   # 最多 6 条（3轮）

    # 拼接：上文历史 + 当前 query
    messages = context + [{"role": "user", "content": query}]

    try:
        raw = llm.chat(messages, system=_INTENT_SYSTEM)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return _keyword_fallback(query)
        data = json.loads(match.group())
        raw_intent_type = data.get("intent_type", "recommend")
        intent_type = raw_intent_type if raw_intent_type in ("recommend", "chat") else "recommend"
        return UserIntent(
            raw_query=query,
            intent_type=intent_type,
            reference_movies=data.get("reference_movies") or [],
            preferred_genres=data.get("preferred_genres") or [],
            preferred_mood=data.get("preferred_mood") or [],
            constraints=data.get("constraints") or {},
            need_clarification=bool(data.get("need_clarification")),
        )
    except Exception as e:
        logger.warning("LLM intent extraction failed (%s: %s), falling back to keyword extraction", type(e).__name__, e)
        return _keyword_fallback(query)


# ---- 关键词兜底解析 ----

_GENRE_KEYWORDS: dict[str, list[str]] = {
    "科幻": ["科幻", "宇宙", "太空", "外星", "未来", "赛博", "机器人", "科技", "space", "sci-fi"],
    "悬疑": ["悬疑", "推理", "侦探", "谜", "凶手", "murder", "mystery", "惊悚", "thriller"],
    "爱情": ["爱情", "浪漫", "romance", "love", "恋爱", "情感", "感情", "感情戏", "爱", "情侣", "约会"],
    "冒险": ["冒险", "探险", "adventure", "寻宝", "旅途", "征途", "探索"],
    "动作": ["动作", "打斗", "战斗", "爆炸", "追车", "action", "格斗", "枪战", "武打"],
    "喜剧": ["喜剧", "搞笑", "幽默", "轻松", "comedy", "funny", "笑", "逗"],
    "恐怖": ["恐怖", "惊吓", "鬼", "horror", "scary", "吓", "灵异", "鬼片"],
    "动画": ["动画", "卡通", "animation", "anime", "漫画", "动漫"],
    "剧情": ["剧情", "人性", "感人", "drama", "故事", "人生", "成长", "情感"],
    "战争": ["战争", "二战", "军事", "战场", "war", "历史战争"],
    "奇幻": ["奇幻", "魔法", "幻想", "fantasy", "magic", "魔幻", "神话", "传说"],
    "家庭": ["家庭", "亲情", "父子", "母女", "family", "温馨", "亲子", "儿童", "children"],
    "犯罪": ["犯罪", "黑帮", "警匪", "crime", "黑道", "警察", "破案"],
    "音乐": ["音乐", "歌舞", "musical", "歌剧", "舞台"],
    "西部": ["西部", "牛仔", "western"],
    "纪录": ["纪录片", "documentary", "真实", "纪录"],
    "黑色": ["黑色电影", "film noir", "film-noir", "黑色"],
}

# ---- 中文类型 → 数据库实际 genre 标签的映射 ----
# 数据库中 movie_genres 字段使用英文标签，用 | 分隔
# 此映射在召回时把用户说的中文类型翻译成数据库可以 LIKE 匹配的英文词

GENRE_CN_TO_DB: dict[str, str] = {
    "科幻": "Sci-Fi",
    "悬疑": "Mystery",
    "惊悚": "Thriller",
    "爱情": "Romance",
    "冒险": "Adventure",
    "动作": "Action",
    "喜剧": "Comedy",
    "恐怖": "Horror",
    "动画": "Animation",
    "剧情": "Drama",
    "战争": "War",
    "奇幻": "Fantasy",
    "家庭": "Children",
    "儿童": "Children",
    "犯罪": "Crime",
    "音乐": "Musical",
    "西部": "Western",
    "纪录": "Documentary",
    "黑色": "Film-Noir",
}

_MOOD_KEYWORDS = ["烧脑", "治愈", "轻松", "反转", "紧张", "催泪", "热血", "励志",
                   "暗黑", "温暖", "孤独", "史诗", "小清新", "cult", "感动", "刺激",
                   "压抑", "欢快", "悲伤", "甜蜜", "虐心", "爽", "震撼", "温情"]

# 《电影名》/ 【电影名】 直接提取
_BRACKET_MOVIE_PATTERN = re.compile(r"[《<【]([^》>\]【】]{1,20})[》>\]】]")
# 像X一样 / 类似X 非括号形式
_LIKE_MOVIE_PATTERN = re.compile(
    r"(?:像|类似于?|参考)([^\s《》【】，。！？、\u300c\u300d]{2,10})(?:一样|那样|似的|的风格|的类型)"
)


def _keyword_fallback(query: str) -> UserIntent:
    genres: list[str] = []
    for genre, kws in _GENRE_KEYWORDS.items():
        if any(kw in query for kw in kws):
            genres.append(genre)

    mood = [m for m in _MOOD_KEYWORDS if m in query]

    ref_movies: list[str] = []
    for m in _BRACKET_MOVIE_PATTERN.finditer(query):
        ref_movies.append(m.group(1).strip())
    for m in _LIKE_MOVIE_PATTERN.finditer(query):
        title = m.group(1).strip()
        if title and title not in ref_movies:
            ref_movies.append(title)

    has_signal = bool(ref_movies or genres or mood)
    return UserIntent(
        raw_query=query,
        intent_type="recommend" if has_signal else "chat",
        reference_movies=ref_movies,
        preferred_genres=genres,
        preferred_mood=mood,
        need_clarification=not has_signal,
    )
