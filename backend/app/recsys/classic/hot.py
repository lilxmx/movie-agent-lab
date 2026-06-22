"""热门推荐，迁移自旧 MovieServiceImpl.getHotMovies。"""
from sqlalchemy.orm import Session

from app.recsys.classic.builder import build_items
from app.recsys.contracts import RecRequest, RecResult
from app.repositories import movie_repo


class HotRecommender:
    name = "hot"

    def recommend(self, db: Session, req: RecRequest) -> RecResult:
        movie_ids = movie_repo.hot_movie_ids(db, req.size)
        items = build_items(db, movie_ids, reason="当前热门高分电影", source="classic")
        return RecResult(mode="classic", items=items)
