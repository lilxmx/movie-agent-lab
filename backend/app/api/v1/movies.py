"""电影路由：列表、搜索、详情、评分、收藏、演员、评论、问答门槛。"""
from fastapi import APIRouter, Query

from app.core.deps import CurrentUserDep, DbDep, OptionalUserDep
from app.core.response import ApiResponse
from app.schemas.movie import AnswerResult, AnswerSubmit, CommentCreate, RatingRequest
from app.services import movie_service, quiz_service, social_service

router = APIRouter(prefix="/movies", tags=["电影"])


@router.get("", response_model=ApiResponse)
def list_movies(db: DbDep, page: int = 1, page_size: int = 10, q: str = "", type: int = 0):
    if q:
        return ApiResponse.ok(movie_service.search_movies(db, page, page_size, q, type))
    return ApiResponse.ok(movie_service.list_movies(db, page, page_size))


@router.get("/{movie_id}", response_model=ApiResponse)
def get_detail(movie_id: int, db: DbDep, user_id: OptionalUserDep):
    return ApiResponse.ok(movie_service.get_detail(db, movie_id, user_id))


@router.get("/{movie_id}/cast", response_model=ApiResponse)
def get_cast(movie_id: int, db: DbDep):
    return ApiResponse.ok(social_service.movie_cast(db, movie_id))


@router.post("/{movie_id}/rating", response_model=ApiResponse)
def rate(movie_id: int, body: RatingRequest, db: DbDep, user_id: CurrentUserDep):
    movie_service.rate_movie(db, user_id, movie_id, body.movie_rating)
    return ApiResponse.ok(message="评分成功")


@router.get("/{movie_id}/my-rating", response_model=ApiResponse)
def my_rating(movie_id: int, db: DbDep, user_id: CurrentUserDep):
    return ApiResponse.ok(movie_service.my_rating(db, user_id, movie_id))


@router.post("/{movie_id}/collect", response_model=ApiResponse)
def collect(movie_id: int, db: DbDep, user_id: CurrentUserDep):
    return ApiResponse.ok(message=movie_service.toggle_collect(db, user_id, movie_id))


@router.get("/{movie_id}/is-collected", response_model=ApiResponse)
def is_collected(movie_id: int, db: DbDep, user_id: CurrentUserDep):
    return ApiResponse.ok(movie_service.is_collected(db, user_id, movie_id))


@router.get("/{movie_id}/comments", response_model=ApiResponse)
def comments(movie_id: int, db: DbDep, parent_id: int = 0):
    return ApiResponse.ok(social_service.list_comments(db, movie_id, parent_id))


@router.post("/{movie_id}/comments", response_model=ApiResponse)
def add_comment(movie_id: int, body: CommentCreate, db: DbDep, user_id: CurrentUserDep):
    social_service.publish_comment(
        db, user_id, movie_id, body.parent_id, body.comment_title, body.comment_info, body.comment_type
    )
    return ApiResponse.ok(message="评论成功")


@router.get("/{movie_id}/quiz", response_model=ApiResponse)
def quiz(movie_id: int, db: DbDep, num: int = Query(default=3, ge=1, le=20)):
    return ApiResponse.ok(quiz_service.get_questions(db, movie_id, num))


@router.post("/{movie_id}/quiz/submit", response_model=ApiResponse[AnswerResult])
def submit_answer(movie_id: int, body: AnswerSubmit, db: DbDep, user_id: CurrentUserDep):
    correct = quiz_service.check_and_save_answer(db, user_id, body.question_id, body.answer)
    return ApiResponse.ok(AnswerResult(correct=correct))


@router.get("/{movie_id}/rating-qualified", response_model=ApiResponse)
def rating_qualified(movie_id: int, db: DbDep, user_id: CurrentUserDep):
    return ApiResponse.ok(quiz_service.is_rating_qualified(db, user_id, movie_id))
