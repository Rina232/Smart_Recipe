import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .config import BM25_B, BM25_K1


@dataclass(frozen=True)
class SearchHit:
    doc_id: str
    score: float
    rank: int


class BM25Index:
    def __init__(self, documents: Iterable[tuple[str, list[str]]], k1: float = BM25_K1, b: float = BM25_B):
        if k1 < 0:
            raise ValueError("k1 должен быть >= 0")
        if not 0 <= b <= 1:
            raise ValueError("b должен быть в диапазоне [0, 1]")
        self.k1 = k1
        self.b = b
        self.index: dict[str, dict[str, int]] = {}
        self.doc_len: dict[str, int] = {}
        for doc_id, tokens in documents:
            if not isinstance(doc_id, str) or not doc_id:
                raise ValueError("ID документа должен быть непустой строкой")
            if doc_id in self.doc_len:
                raise ValueError(f"Повторяющийся ID документа: {doc_id}")
            counts = Counter(tokens)
            self.doc_len[doc_id] = len(tokens)
            for term, tf in counts.items():
                self.index.setdefault(term, {})[doc_id] = tf
        self.N = len(self.doc_len)
        self.avgdl = sum(self.doc_len.values()) / self.N if self.N else 0.0
        self.df = {term: len(postings) for term, postings in self.index.items()}

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def _term_score(self, term: str, doc_id: str) -> float:
        tf = self.index.get(term, {}).get(doc_id, 0)
        if tf == 0 or self.avgdl == 0:
            return 0.0
        length_norm = 1 - self.b + self.b * self.doc_len[doc_id] / self.avgdl
        return self.idf(term) * tf * (self.k1 + 1) / (tf + self.k1 * length_norm)

    def contributions(self, query_tokens: list[str], doc_id: str) -> dict[str, float]:
        return {term: self._term_score(term, doc_id) for term in dict.fromkeys(query_tokens)}

    def score(self, query_tokens: list[str], doc_id: str) -> float:
        return sum(self.contributions(query_tokens, doc_id).values())

    def search(self, query_tokens: list[str], top_k: int | None = None, min_score: float = 0.0) -> list[SearchHit]:
        if self.N == 0 or not query_tokens or (top_k is not None and top_k <= 0):
            return []
        scores: dict[str, float] = {}
        for term in dict.fromkeys(query_tokens):
            for doc_id in self.index.get(term, {}):
                scores[doc_id] = scores.get(doc_id, 0.0) + self._term_score(term, doc_id)
        ranked = sorted(
            ((doc_id, score) for doc_id, score in scores.items() if score > min_score),
            key=lambda item: (-round(item[1], 12), item[0]),
        )
        if top_k is not None:
            ranked = ranked[:top_k]
        return [SearchHit(doc_id=doc_id, score=score, rank=i + 1) for i, (doc_id, score) in enumerate(ranked)]
