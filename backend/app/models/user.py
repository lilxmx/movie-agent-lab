"""用户与交互相关 ORM，映射旧表 user / userStatistic / rating / movieCollect。"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(64))
    user_password: Mapped[str] = mapped_column(String(64))
    user_salt: Mapped[str | None] = mapped_column(String(64))
    user_is_origin: Mapped[int | None] = mapped_column(Integer, default=0)
    user_is_alive: Mapped[int] = mapped_column(Integer, default=1)


class UserStatistic(Base):
    __tablename__ = "userStatistic"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_rated_movies: Mapped[str | None] = mapped_column(String(2048))
    user_rating_count: Mapped[int | None] = mapped_column(Integer)
    user_avg_released_year: Mapped[int | None] = mapped_column(Integer)
    user_released_year_stddev: Mapped[float | None] = mapped_column(Float)
    user_avg_rating: Mapped[float | None] = mapped_column(Float)
    user_rating_stddev: Mapped[float | None] = mapped_column(Float)
    # 旧库格式：Drama|Action|Comedy
    user_like_genres: Mapped[str | None] = mapped_column(String(255))


class Rating(Base):
    __tablename__ = "rating"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating: Mapped[float] = mapped_column(Float)
    rating_time: Mapped[datetime | None] = mapped_column(DateTime)
    is_origin: Mapped[int | None] = mapped_column(Integer, default=0)


class MovieCollect(Base):
    __tablename__ = "movieCollect"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collect_date: Mapped[datetime | None] = mapped_column(DateTime)
