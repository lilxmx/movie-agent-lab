"""将电影 id 列表组装为统一的 RecItem 列表，供各 classic 策略复用。"""
from sqlalchemy.orm import Session

from app.recsys.contracts import RecItem
from app.repositories import movie_repo


def build_items(
    db: Session,
    movie_ids: list[int],
    scores: dict[int, float] | None = None,
    reason: str = "",
    source: str = "classic",
) -> list[RecItem]:
    movies = movie_repo.movies_by_ids(db, movie_ids)
    stats = movie_repo.statistics_by_ids(db, movie_ids)
    items: list[RecItem] = []
    for mid in movie_ids:
        movie = movies.get(mid)
        if movie is None:
            continue
        score = scores.get(mid) if scores else None
        if score is None:
            stat = stats.get(mid)
            score = float(stat.movie_avg_rating) if stat and stat.movie_avg_rating else 0.0
        items.append(
            RecItem(
                movie_id=mid,
                title=movie.movie_name,
                score=round(float(score), 4),
                reason=reason,
                source=source,
            )
        )
    return items
