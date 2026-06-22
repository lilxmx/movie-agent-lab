"""评分后刷新用户与电影统计特征，替代旧 ThreadService 的异步更新。

旧实现按增量更新易产生精度漂移（旧 readme 已记录该问题）。此处直接基于
rating 表做聚合重算，逻辑简单且准确，函数小、可复用。
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Movie, MovieStatistic, Rating, UserStatistic


def _round(value: float | None, ndigits: int = 2) -> float:
    return round(value or 0.0, ndigits)


def refresh_movie_stat(db: Session, movie_id: int) -> None:
    count, avg, std = db.execute(
        select(func.count(), func.avg(Rating.rating), func.stddev(Rating.rating)).where(
            Rating.movie_id == movie_id
        )
    ).one()
    stat = db.get(MovieStatistic, movie_id)
    if stat is None:
        stat = MovieStatistic(movie_id=movie_id)
        db.add(stat)
    stat.movie_rating_count = count or 0
    stat.movie_avg_rating = _round(avg)
    stat.movie_rating_stddev = _round(std)
    db.commit()


def refresh_user_stat(db: Session, user_id: int) -> None:
    count, avg_rating, std_rating = db.execute(
        select(func.count(), func.avg(Rating.rating), func.stddev(Rating.rating)).where(
            Rating.user_id == user_id
        )
    ).one()
    avg_year, std_year = db.execute(
        select(func.avg(Movie.movie_released_year), func.stddev(Movie.movie_released_year))
        .select_from(Rating)
        .join(Movie, Movie.movie_id == Rating.movie_id)
        .where(Rating.user_id == user_id)
    ).one()

    stat = db.get(UserStatistic, user_id)
    if stat is None:
        stat = UserStatistic(user_id=user_id)
        db.add(stat)
    stat.user_rating_count = count or 0
    stat.user_avg_rating = _round(avg_rating)
    stat.user_rating_stddev = _round(std_rating)
    stat.user_avg_released_year = int(avg_year) if avg_year else None
    stat.user_released_year_stddev = _round(std_year)
    stat.user_like_genres = _compute_like_genres(db, user_id)
    db.commit()


def _compute_like_genres(db: Session, user_id: int, top_n: int = 5) -> str:
    """统计用户评分电影的高频类型，竖线拼接（保持旧库 user_like_genres 格式）。"""
    rows = db.execute(
        select(Movie.movie_genres)
        .select_from(Rating)
        .join(Movie, Movie.movie_id == Rating.movie_id)
        .where(Rating.user_id == user_id)
    ).all()
    counter: dict[str, int] = {}
    for (genres,) in rows:
        for genre in (genres or "").split("|"):
            if genre:
                counter[genre] = counter.get(genre, 0) + 1
    ranked = sorted(counter, key=counter.get, reverse=True)[:top_n]
    return "|".join(ranked)


def refresh_after_rating(
    db: Session, user_id: int, movie_id: int, value: float, is_update: bool
) -> None:
    refresh_user_stat(db, user_id)
    refresh_movie_stat(db, movie_id)
