"""演员与评论数据访问层。"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Actor, Comment, CommentLike, MovieActor, User


def movie_actors(db: Session, movie_id: int) -> list[Actor]:
    return list(
        db.scalars(
            select(Actor)
            .join(MovieActor, MovieActor.actor_id == Actor.actor_id)
            .where(MovieActor.movie_id == movie_id)
            .order_by(MovieActor.order)
        ).all()
    )


def comments_of_movie(db: Session, movie_id: int, parent_id: int):
    like_count = (
        select(func.count())
        .select_from(CommentLike)
        .where(CommentLike.comment_id == Comment.comment_id)
        .scalar_subquery()
    )
    stmt = (
        select(Comment, User.user_name, like_count.label("like_num"))
        .join(User, User.user_id == Comment.user_id, isouter=True)
        .where(Comment.to_id == movie_id, Comment.parent_id == parent_id)
        .order_by(Comment.publish_date.desc())
    )
    return db.execute(stmt).all()


def add_comment(
    db: Session, user_id: int, movie_id: int, parent_id: int, title: str | None, info: str, ctype: int
) -> None:
    db.add(
        Comment(
            to_id=movie_id,
            parent_id=parent_id,
            user_id=user_id,
            comment_title=title,
            comment_info=info,
            comment_type=ctype,
            publish_date=datetime.now(),
        )
    )
    db.commit()


def toggle_like(db: Session, user_id: int, comment_id: int) -> bool:
    existing = db.get(CommentLike, (comment_id, user_id))
    if existing:
        db.delete(existing)
        db.commit()
        return False
    db.add(
        CommentLike(comment_id=comment_id, user_id=user_id, like_num=1, action_date=datetime.now())
    )
    db.commit()
    return True
