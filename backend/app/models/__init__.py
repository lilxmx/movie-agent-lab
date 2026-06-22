"""ORM 模型聚合导出，方便 Alembic 与各处统一引用。"""
from app.models.ai import AgentMemory, AgentTrace, ChatMessage, ChatSession, RecommendationRun
from app.models.movie import Movie, MovieStatistic, MovieSummary
from app.models.quiz import Question, QuestionRank
from app.models.social import Actor, Comment, CommentLike, MovieActor
from app.models.system import Config, Manager
from app.models.user import MovieCollect, Rating, User, UserStatistic

__all__ = [
    "Movie",
    "MovieStatistic",
    "MovieSummary",
    "User",
    "UserStatistic",
    "Rating",
    "MovieCollect",
    "Actor",
    "MovieActor",
    "Comment",
    "CommentLike",
    "Question",
    "QuestionRank",
    "Config",
    "Manager",
    "RecommendationRun",
    "ChatSession",
    "ChatMessage",
    "AgentTrace",
    "AgentMemory",
]
