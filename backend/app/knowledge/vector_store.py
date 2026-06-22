"""向量库抽象层（Phase 8）。

定义统一接口，第一版提供内存实现；后续可无缝替换为 pgvector / Qdrant / Milvus。
collection 维度隔离：knowledge / memory / video 等可各用一个 collection。
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchHit:
    doc_id: str
    text: str
    score: float
    metadata: dict


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection: str, docs: list[Document]) -> None: ...

    @abstractmethod
    def search(self, collection: str, query: str, top_k: int = 5) -> list[SearchHit]: ...


def _tokenize(text: str) -> set[str]:
    """提取 token：英文单词 + 中文 bigram（相邻两字），兼顾中英文检索质量。"""
    tokens: set[str] = set()
    # 英文单词（含数字）
    tokens.update(re.findall(r"[a-z0-9]+", text.lower()))
    # 中文字符逐字 + bigram
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    tokens.update(cn_chars)
    for i in range(len(cn_chars) - 1):
        tokens.add(cn_chars[i] + cn_chars[i + 1])
    return tokens


class InMemoryVectorStore(VectorStore):
    """轻量内存实现，用 Jaccard 词集合相似度近似检索，免外部依赖。"""

    def __init__(self) -> None:
        self._collections: dict[str, list[Document]] = {}

    def upsert(self, collection: str, docs: list[Document]) -> None:
        store = self._collections.setdefault(collection, [])
        existing = {d.doc_id: i for i, d in enumerate(store)}
        for doc in docs:
            if doc.doc_id in existing:
                store[existing[doc.doc_id]] = doc
            else:
                store.append(doc)

    def search(self, collection: str, query: str, top_k: int = 5) -> list[SearchHit]:
        store = self._collections.get(collection, [])
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        hits: list[SearchHit] = []
        for doc in store:
            d_tokens = _tokenize(doc.text)
            union = q_tokens | d_tokens
            score = len(q_tokens & d_tokens) / len(union) if union else 0.0
            if score > 0:
                hits.append(SearchHit(doc.doc_id, doc.text, round(score, 4), doc.metadata))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
