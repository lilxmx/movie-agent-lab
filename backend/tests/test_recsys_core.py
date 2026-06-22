"""推荐系统纯逻辑单元测试（不依赖数据库）。"""
from app.knowledge.vector_store import Document, InMemoryVectorStore
from app.recsys.classic.ab_test import model_by_user_id
from app.recsys.classic.embedding import cosine_similarity, parse_emb
from app.recsys.registry import RecommenderRegistry


def test_parse_emb():
    assert parse_emb("1.0 2.0 3.0") == [1.0, 2.0, 3.0]
    assert parse_emb("") is None
    assert parse_emb("a b c") is None


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert cosine_similarity([1, 0], [0, 1]) == 0.0
    assert cosine_similarity([1, 0], [1]) == -1.0  # 维度不一致


def test_ab_test_buckets():
    assert model_by_user_id(0) == "emb"
    assert model_by_user_id(1) == "NeuralCF"
    assert model_by_user_id(2) == "DeepCrossing"


def test_registry():
    reg = RecommenderRegistry()

    class Dummy:
        name = "dummy"

        def recommend(self, db, req):
            return None

    reg.register("dummy", Dummy())
    assert reg.get("dummy").name == "dummy"
    assert "dummy" in reg.modes()


def test_vector_store_search():
    store = InMemoryVectorStore()
    store.upsert(
        "knowledge",
        [
            Document("1", "a space adventure with robots"),
            Document("2", "a romantic love story in paris"),
        ],
    )
    hits = store.search("knowledge", "space robots adventure", top_k=1)
    assert hits and hits[0].doc_id == "1"
