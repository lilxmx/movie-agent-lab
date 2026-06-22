"""电影相关 schema。"""
from pydantic import BaseModel


class MovieBrief(BaseModel):
    movie_id: int
    movie_name: str
    movie_genres: str | None = None
    movie_released_year: str | None = None
    movie_avg_rating: float | None = None


class MovieDetail(BaseModel):
    movie_id: int
    movie_name: str
    movie_genres: str | None = None
    movie_released_year: str | None = None
    movie_summary: str | None = None
    movie_avg_rating: float | None = None


class ActorBrief(BaseModel):
    actor_id: int
    actor_name: str


class RatingRequest(BaseModel):
    movie_rating: float


class CommentCreate(BaseModel):
    parent_id: int = 0
    comment_title: str | None = None
    comment_info: str
    comment_type: int = 0


class CommentBrief(BaseModel):
    comment_id: int
    parent_id: int
    user_name: str | None = None
    comment_title: str | None = None
    comment_info: str | None = None
    like_num: int = 0


class QuizQuestion(BaseModel):
    question_id: int
    question_info: str
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None


class AnswerSubmit(BaseModel):
    question_id: int
    answer: int  # 1=A 2=B 3=C 4=D


class AnswerResult(BaseModel):
    correct: bool
