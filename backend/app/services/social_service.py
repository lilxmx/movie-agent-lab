"""演员与评论业务逻辑。"""
from sqlalchemy.orm import Session

from app.repositories import social_repo
from app.schemas.movie import ActorBrief, CommentBrief


def movie_cast(db: Session, movie_id: int) -> list[ActorBrief]:
    actors = social_repo.movie_actors(db, movie_id)
    return [ActorBrief(actor_id=a.actor_id, actor_name=a.actor_name) for a in actors]


def list_comments(db: Session, movie_id: int, parent_id: int) -> list[CommentBrief]:
    rows = social_repo.comments_of_movie(db, movie_id, parent_id)
    return [
        CommentBrief(
            comment_id=c.comment_id,
            parent_id=c.parent_id,
            user_name=user_name,
            comment_title=c.comment_title,
            comment_info=c.comment_info,
            like_num=like_num or 0,
        )
        for c, user_name, like_num in rows
    ]


def publish_comment(
    db: Session, user_id: int, movie_id: int, parent_id: int, title: str | None, info: str, ctype: int
) -> None:
    social_repo.add_comment(db, user_id, movie_id, parent_id, title, info, ctype)


def like_comment(db: Session, user_id: int, comment_id: int) -> bool:
    return social_repo.toggle_like(db, user_id, comment_id)
