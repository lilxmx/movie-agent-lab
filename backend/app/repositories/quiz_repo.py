"""问答门槛数据访问层。"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Question, QuestionRank


def get_question(db: Session, question_id: int) -> Question | None:
    return db.get(Question, question_id)


def movie_questions(db: Session, movie_id: int, num: int) -> list[Question]:
    return list(
        db.scalars(select(Question).where(Question.to_id == movie_id).limit(num)).all()
    )


def save_question(
    db: Session,
    movie_id: int,
    question_info: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    answer: int,
) -> Question:
    q = Question(
        to_id=movie_id,
        question_info=question_info,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        answer=answer,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def correct_answer_count(db: Session, user_id: int, movie_id: int) -> int:
    """用户在该电影下答对的题数（questionRank.answer == question.answer）。"""
    return db.scalar(
        select(func.count())
        .select_from(QuestionRank)
        .join(Question, Question.question_id == QuestionRank.question_id)
        .where(
            Question.to_id == movie_id,
            QuestionRank.user_id == user_id,
            QuestionRank.answer == Question.answer,
        )
    ) or 0


def save_answer(db: Session, user_id: int, question_id: int, answer: int) -> None:
    existing = db.get(QuestionRank, (user_id, question_id))
    if existing:
        existing.answer = answer
        existing.answer_time = datetime.now()
    else:
        db.add(
            QuestionRank(
                user_id=user_id,
                question_id=question_id,
                answer=answer,
                answer_time=datetime.now(),
            )
        )
    db.commit()
