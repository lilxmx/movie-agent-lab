"""电影数据访问层，封装对 movie / movieStatistic / movieSummary 的查询。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Movie, MovieStatistic, MovieSummary


def get_by_id(db: Session, movie_id: int) -> Movie | None:
    return db.get(Movie, movie_id)


def get_statistic(db: Session, movie_id: int) -> MovieStatistic | None:
    return db.get(MovieStatistic, movie_id)


def get_summary(db: Session, movie_id: int) -> MovieSummary | None:
    return db.get(MovieSummary, movie_id)


def list_paged(db: Session, page: int, page_size: int) -> tuple[list[Movie], int]:
    total = db.scalar(select(func.count()).select_from(Movie)) or 0
    rows = db.scalars(
        select(Movie).order_by(Movie.movie_released_year.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def search(
    db: Session, page: int, page_size: int, info: str, search_type: int
) -> tuple[list[Movie], int]:
    column = Movie.movie_genres if search_type == 1 else Movie.movie_name
    stmt = select(Movie).where(column.like(f"%{info}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), total


def hot_movie_ids(db: Session, size: int) -> list[int]:
    rows = db.execute(
        select(MovieStatistic.movie_id)
        .order_by(MovieStatistic.movie_rating_count.desc(), MovieStatistic.movie_avg_rating.desc())
        .limit(size)
    ).all()
    return [r[0] for r in rows]


def avg_rating(db: Session, movie_id: int) -> float | None:
    stat = db.get(MovieStatistic, movie_id)
    return stat.movie_avg_rating if stat else None


def statistics_by_ids(db: Session, movie_ids: list[int]) -> dict[int, MovieStatistic]:
    if not movie_ids:
        return {}
    rows = db.scalars(
        select(MovieStatistic).where(MovieStatistic.movie_id.in_(movie_ids))
    ).all()
    return {r.movie_id: r for r in rows}


def movies_by_ids(db: Session, movie_ids: list[int]) -> dict[int, Movie]:
    if not movie_ids:
        return {}
    rows = db.scalars(select(Movie).where(Movie.movie_id.in_(movie_ids))).all()
    return {r.movie_id: r for r in rows}


def candidate_ids_by_genres_and_year(
    db: Session, genres_regexp: str, target_year: int, span: int
) -> list[int]:
    """按类型正则 + 上映年份邻域召回候选电影 id（迁移自旧 selectMovieIdsByGenresAndYear）。"""
    stmt = (
        select(Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .where(Movie.movie_genres.op("REGEXP")(genres_regexp))
        .where(func.abs(Movie.movie_released_year - target_year) < span)
        .order_by(MovieStatistic.movie_avg_rating.desc())
    )
    return [r[0] for r in db.execute(stmt).all()]


def rated_movie_ids(db: Session, user_id: int) -> list[int]:
    from app.models import Rating

    rows = db.execute(select(Rating.movie_id).where(Rating.user_id == user_id)).all()
    return [r[0] for r in rows]


def _ids_with_stat_order(db: Session, stmt) -> list[int]:
    return [r[0] for r in db.execute(stmt).all()]


def top_ids_by_genre(db: Session, genre: str, size: int) -> list[int]:
    stmt = (
        select(Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .where(Movie.movie_genres.like(f"%{genre}%"))
        .order_by(MovieStatistic.movie_avg_rating.desc())
        .limit(size)
    )
    return _ids_with_stat_order(db, stmt)


def top_ids_by_avg(db: Session, size: int) -> list[int]:
    stmt = (
        select(Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .order_by(MovieStatistic.movie_avg_rating.desc())
        .limit(size)
    )
    return _ids_with_stat_order(db, stmt)


def top_ids_by_released_year(db: Session, year: int, span: int, size: int) -> list[int]:
    stmt = (
        select(Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .where(func.abs(Movie.movie_released_year - year) < span)
        .order_by(MovieStatistic.movie_avg_rating.desc())
        .limit(size)
    )
    return _ids_with_stat_order(db, stmt)
