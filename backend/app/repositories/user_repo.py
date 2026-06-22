"""用户数据访问层。"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Config,
    Movie,
    MovieCollect,
    MovieStatistic,
    Rating,
    User,
    UserStatistic,
)


def get_by_name(db: Session, user_name: str) -> User | None:
    return db.scalar(select(User).where(User.user_name == user_name))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def rating_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(func.distinct(Rating.movie_id))).where(Rating.user_id == user_id)
    ) or 0


def create_user(db: Session, user_name: str, hashed: str, salt: str) -> User:
    user = User(
        user_name=user_name,
        user_password=hashed,
        user_salt=salt,
        user_is_origin=0,
        user_is_alive=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_statistic(db: Session, user_id: int) -> UserStatistic | None:
    return db.get(UserStatistic, user_id)


def get_ab_test_flag(db: Session) -> int:
    row = db.scalar(select(Config.ab_test))
    return row or 0


def get_rating(db: Session, user_id: int, movie_id: int) -> float | None:
    return db.scalar(
        select(Rating.rating).where(Rating.user_id == user_id, Rating.movie_id == movie_id)
    )


def upsert_rating(db: Session, user_id: int, movie_id: int, value: float) -> None:
    existing = db.get(Rating, (user_id, movie_id))
    if existing:
        existing.rating = value
        existing.rating_time = datetime.now()
    else:
        db.add(Rating(user_id=user_id, movie_id=movie_id, rating=value, rating_time=datetime.now()))
    db.commit()


def is_collected(db: Session, user_id: int, movie_id: int) -> bool:
    return db.get(MovieCollect, (user_id, movie_id)) is not None


def toggle_collect(db: Session, user_id: int, movie_id: int) -> bool:
    """切换收藏，返回最终是否已收藏。"""
    existing = db.get(MovieCollect, (user_id, movie_id))
    if existing:
        db.delete(existing)
        db.commit()
        return False
    db.add(MovieCollect(user_id=user_id, movie_id=movie_id, collect_date=datetime.now()))
    db.commit()
    return True


def list_collections(db: Session, user_id: int, page: int, page_size: int):
    stmt = (
        select(Movie, MovieStatistic.movie_avg_rating)
        .join(MovieCollect, MovieCollect.movie_id == Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .where(MovieCollect.user_id == user_id)
        .order_by(MovieCollect.collect_date.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, total


def list_rating_history(db: Session, user_id: int, page: int, page_size: int):
    stmt = (
        select(Movie, Rating.rating, MovieStatistic.movie_avg_rating)
        .join(Rating, Rating.movie_id == Movie.movie_id)
        .join(MovieStatistic, MovieStatistic.movie_id == Movie.movie_id, isouter=True)
        .where(Rating.user_id == user_id)
        .order_by(Rating.rating_time.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, total
