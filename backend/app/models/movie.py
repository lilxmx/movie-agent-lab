"""电影相关 ORM，映射旧表 movie / movieStatistic / movieSummary。"""
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Movie(Base):
    __tablename__ = "movie"

    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_name: Mapped[str] = mapped_column(String(255))
    # 旧库格式：Adventure|Children|Fantasy
    movie_genres: Mapped[str | None] = mapped_column(String(255))
    movie_released_year: Mapped[str | None] = mapped_column(String(16))
    movie_photo_url: Mapped[str | None] = mapped_column(String(512))
    movie_run_time: Mapped[int | None] = mapped_column(Integer)


class MovieStatistic(Base):
    __tablename__ = "movieStatistic"

    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_rating_count: Mapped[int | None] = mapped_column(Integer)
    movie_avg_rating: Mapped[float | None] = mapped_column(Float)
    movie_rating_stddev: Mapped[float | None] = mapped_column(Float)


class MovieSummary(Base):
    __tablename__ = "movieSummary"

    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_summary: Mapped[str | None] = mapped_column(Text)
