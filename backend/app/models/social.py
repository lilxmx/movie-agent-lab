"""演员与评论相关 ORM，映射旧表 actor / movieActor / comment / comment_like。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Actor(Base):
    __tablename__ = "actor"

    actor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_name: Mapped[str] = mapped_column(String(128))
    gender: Mapped[str | None] = mapped_column(String(8))
    birthdate: Mapped[str | None] = mapped_column(String(32))
    introduction: Mapped[str | None] = mapped_column(String(2048))


class MovieActor(Base):
    __tablename__ = "movieActor"

    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order: Mapped[int | None] = mapped_column("order", Integer)


class Comment(Base):
    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    to_id: Mapped[int] = mapped_column(Integer)  # 关联 movie_id
    parent_id: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[int] = mapped_column(Integer)
    comment_title: Mapped[str | None] = mapped_column(String(255))
    comment_info: Mapped[str | None] = mapped_column(Text)
    comment_type: Mapped[int | None] = mapped_column(Integer)
    publish_date: Mapped[datetime | None] = mapped_column(DateTime)


class CommentLike(Base):
    __tablename__ = "comment_like"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    like_num: Mapped[int | None] = mapped_column(Integer, default=1)
    action_date: Mapped[datetime | None] = mapped_column(DateTime)
