"""问答门槛业务逻辑：答题达标才能评分。"""
from sqlalchemy.orm import Session

from app.repositories import quiz_repo
from app.schemas.movie import QuizQuestion

PASS_THRESHOLD = 1  # 至少答对题数达标即可评分


def get_questions(db: Session, movie_id: int, num: int) -> list[QuizQuestion]:
    questions = quiz_repo.movie_questions(db, movie_id, num)
    return [
        QuizQuestion(
            question_id=q.question_id,
            question_info=q.question_info,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
        )
        for q in questions
    ]


def check_and_save_answer(db: Session, user_id: int, question_id: int, answer: int) -> bool:
    """保存答案并返回是否答对。"""
    question = quiz_repo.get_question(db, question_id)
    correct = question is not None and question.answer == answer
    quiz_repo.save_answer(db, user_id, question_id, answer)
    return correct


def is_rating_qualified(db: Session, user_id: int, movie_id: int) -> bool:
    return quiz_repo.correct_answer_count(db, user_id, movie_id) >= PASS_THRESHOLD
