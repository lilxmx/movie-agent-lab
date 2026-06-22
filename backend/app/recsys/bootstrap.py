"""注册所有推荐策略。在应用启动时调用一次。"""
from app.recsys.agentic.mock_pipeline import AgentRecommender
from app.recsys.classic.hot import HotRecommender
from app.recsys.classic.personalized import PersonalizedRecommender
from app.recsys.classic.similar import SimilarRecommender
from app.recsys.registry import registry


def register_recommenders() -> None:
    registry.register("hot", HotRecommender())
    registry.register("similar", SimilarRecommender())
    registry.register("personalized", PersonalizedRecommender())
    registry.register("agent", AgentRecommender())
