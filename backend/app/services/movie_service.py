"""电影业务逻辑：列表、搜索、详情、评分、收藏。"""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.memory.scan_history import record_scan
from app.models import Movie
from app.repositories import movie_repo, user_repo
from app.schemas.common import Paged
from app.schemas.movie import MovieBrief, MovieDetail
from app.services import stat_service


def _to_brief(db: Session, movie: Movie) -> MovieBrief:
    return MovieBrief(
        movie_id=movie.movie_id,
        movie_name=movie.movie_name,
        movie_genres=movie.movie_genres,
        movie_released_year=movie.movie_released_year,
        movie_avg_rating=movie_repo.avg_rating(db, movie.movie_id),
    )


def list_movies(db: Session, page: int, page_size: int) -> Paged[MovieBrief]:
    if page <= 0 or page_size > 100:
        raise BusinessError("分页参数超出范围")
    rows, total = movie_repo.list_paged(db, page, page_size)
    return Paged(items=[_to_brief(db, m) for m in rows], total=total)


def search_movies(
    db: Session, page: int, page_size: int, info: str, search_type: int
) -> Paged[MovieBrief]:
    if not info:
        return list_movies(db, page, page_size)
    rows, total = movie_repo.search(db, page, page_size, info, search_type)
    return Paged(items=[_to_brief(db, m) for m in rows], total=total)


def get_detail(db: Session, movie_id: int, user_id: int | None) -> MovieDetail:
    movie = movie_repo.get_by_id(db, movie_id)
    if movie is None:
        raise BusinessError("电影不存在")
    if user_id is not None:
        record_scan(user_id, movie_id)
    summary = movie_repo.get_summary(db, movie_id)
    return MovieDetail(
        movie_id=movie.movie_id,
        movie_name=movie.movie_name,
        movie_genres=movie.movie_genres,
        movie_released_year=movie.movie_released_year,
        movie_summary=summary.movie_summary if summary else None,
        movie_avg_rating=movie_repo.avg_rating(db, movie_id),
    )


def rate_movie(db: Session, user_id: int, movie_id: int, value: float) -> None:
    from app.services import quiz_service  # 延迟导入避免循环依赖

    if movie_repo.get_by_id(db, movie_id) is None:
        raise BusinessError("电影不存在")
    if not quiz_service.is_rating_qualified(db, user_id, movie_id):
        raise BusinessError("请先回答答题问卷获得评分资格")
    is_update = user_repo.get_rating(db, user_id, movie_id) is not None
    user_repo.upsert_rating(db, user_id, movie_id, value)
    # 评分后刷新统计特征（迁移自旧 ThreadService 异步更新）
    stat_service.refresh_after_rating(db, user_id, movie_id, value, is_update)


def my_rating(db: Session, user_id: int, movie_id: int) -> float:
    return user_repo.get_rating(db, user_id, movie_id) or 0.0


def toggle_collect(db: Session, user_id: int, movie_id: int) -> str:
    collected = user_repo.toggle_collect(db, user_id, movie_id)
    return "收藏成功" if collected else "取消收藏"


def is_collected(db: Session, user_id: int, movie_id: int) -> bool:
    return user_repo.is_collected(db, user_id, movie_id)
