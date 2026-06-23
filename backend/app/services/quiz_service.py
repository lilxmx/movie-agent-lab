"""问答门槛业务逻辑：答题达标才能评分。

每次评分前由 LLM 实时生成题目，生成后保存到数据库作为缓存。
"""
import json
import re

from sqlalchemy.orm import Session

from app.core.llm_provider import get_llm_provider
from app.repositories import movie_repo, quiz_repo
from app.schemas.movie import QuizQuestion

PASS_THRESHOLD = 1  # 至少答对题数达标即可评分

QUIZ_SYSTEM_PROMPT = """你是一个电影问答出题助手。根据给定的电影信息，生成一道单选题。
题目要求：考察用户是否真的看过这部电影，题目应涉及电影剧情细节、角色关系或经典场景。

请只返回 JSON，格式如下：
{
  "question": "题目内容",
  "A": "选项A",
  "B": "选项B",
  "C": "选项C",
  "D": "选项D",
  "answer": 1
}
answer 字段为正确答案的序号（1=A, 2=B, 3=C, 4=D）。
"""


def _generate_quiz_with_llm(db: Session, movie_id: int, num: int) -> list[QuizQuestion]:
    """调用 LLM 为指定电影生成题目，保存到数据库并返回。"""
    movie = movie_repo.get_by_id(db, movie_id)
    if movie is None:
        return []

    movie_info = f"电影名：{movie.movie_name}"
    if movie.movie_genres:
        movie_info += f"\n类型：{movie.movie_genres}"
    if movie.movie_released_year:
        movie_info += f"\n上映年份：{movie.movie_released_year}"

    results: list[QuizQuestion] = []
    llm = get_llm_provider()

    for _ in range(num):
        try:
            raw = llm.chat(
                messages=[{"role": "user", "content": movie_info}],
                system=QUIZ_SYSTEM_PROMPT,
            )
            # 提取 JSON（LLM 可能输出带 markdown 代码块）
            json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if not json_match:
                continue
            data = json.loads(json_match.group(0))

            question_info = data.get("question", "")
            option_a = data.get("A", "")
            option_b = data.get("B", "")
            option_c = data.get("C", "")
            option_d = data.get("D", "")
            answer = data.get("answer", 1)

            if not question_info or not all([option_a, option_b, option_c, option_d]):
                continue

            # 保存到数据库，以便 check_and_save_answer 验证答案
            saved = quiz_repo.save_question(
                db, movie_id, question_info, option_a, option_b, option_c, option_d, answer
            )
            results.append(
                QuizQuestion(
                    question_id=saved.question_id,
                    question_info=question_info,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                )
            )
        except Exception:
            # LLM 调用失败，跳过继续尝试下一道
            continue

    return results


def get_questions(db: Session, movie_id: int, num: int) -> list[QuizQuestion]:
    """获取题目：每次调 LLM 实时生成，生成后保存到数据库。"""
    # 每次都调 LLM 生成新题
    generated = _generate_quiz_with_llm(db, movie_id, num)
    if generated:
        return generated

    # LLM 生成失败，兜底尝试从数据库读取已有题目
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
