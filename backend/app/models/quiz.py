"""问答门槛相关 ORM，映射旧表 question / questionRank（答题才能评分）。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Question(Base):
    __tablename__ = "question"

    question_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    to_id: Mapped[int] = mapped_column(Integer)  # 关联 movie_id
    question_info: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str | None] = mapped_column(String(255))
    option_b: Mapped[str | None] = mapped_column(String(255))
    option_c: Mapped[str | None] = mapped_column(String(255))
    option_d: Mapped[str | None] = mapped_column(String(255))
    answer: Mapped[int | None] = mapped_column(Integer)
    analysis: Mapped[str | None] = mapped_column(Text)


class QuestionRank(Base):
    __tablename__ = "questionRank"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    answer: Mapped[int | None] = mapped_column(Integer)
    answer_time: Mapped[datetime | None] = mapped_column(DateTime)
