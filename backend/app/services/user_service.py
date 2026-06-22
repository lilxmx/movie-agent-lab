"""用户中心业务逻辑：收藏列表、评分历史。"""
from sqlalchemy.orm import Session

from app.repositories import user_repo
from app.schemas.common import Paged
from app.schemas.movie import MovieBrief


def collections(db: Session, user_id: int, page: int, page_size: int) -> Paged[MovieBrief]:
    rows, total = user_repo.list_collections(db, user_id, page, page_size)
    items = [
        MovieBrief(
            movie_id=movie.movie_id,
            movie_name=movie.movie_name,
            movie_genres=movie.movie_genres,
            movie_released_year=movie.movie_released_year,
            movie_avg_rating=avg,
        )
        for movie, avg in rows
    ]
    return Paged(items=items, total=total)


def rating_history(db: Session, user_id: int, page: int, page_size: int) -> Paged[MovieBrief]:
    rows, total = user_repo.list_rating_history(db, user_id, page, page_size)
    items = [
        MovieBrief(
            movie_id=movie.movie_id,
            movie_name=movie.movie_name,
            movie_genres=movie.movie_genres,
            movie_released_year=movie.movie_released_year,
            movie_avg_rating=avg,
        )
        for movie, _rating, avg in rows
    ]
    return Paged(items=items, total=total)
