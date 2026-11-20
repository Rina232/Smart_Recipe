import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import config
from .bm25 import BM25Index, SearchHit
from .corpus import RecipeDoc, load_corpus
from .generation import build_messages, parse_llm_output
from .llm import chat
from .text import Normalizer

LLMCall = Callable[[list[dict]], str]


@dataclass
class RagResult:
    question: str
    query_terms: list[str]
    retrieved: list[SearchHit]
    context_ids: list[str]
    answer: str
    sources: list[str]
    recipe: dict | None
    refusal: bool
    refusal_reason: str | None = None
    raw_llm_output: str | None = None
    invalid_sources: list[str] = field(default_factory=list)
    llm_called: bool = False

    def to_contract(self) -> dict:
        result = {"answer": self.answer, "sources": list(self.sources)}
        if self.recipe is not None:
            result["recipe"] = self.recipe
        return result


class RagEngine:
    def __init__(
        self,
        corpus_path: Path | str | None = None,
        normalizer_mode: str | None = None,
        k1: float = config.BM25_K1,
        b: float = config.BM25_B,
        documents: list[RecipeDoc] | None = None,
    ):
        self.documents = documents if documents is not None else load_corpus(corpus_path or config.DEFAULT_CORPUS_PATH)
        self.docs_by_id = {doc.id: doc for doc in self.documents}
        self.normalizer = Normalizer(normalizer_mode or config.get_normalizer_mode())
        self.index = BM25Index(((doc.id, self.normalizer.tokens(doc.index_text())) for doc in self.documents), k1=k1, b=b)

    def retrieve(self, question: str, k: int | None = None) -> list[SearchHit]:
        return self.index.search(self.normalizer.tokens(question), top_k=k, min_score=config.MIN_SCORE)

    def answer(self, question: str, context_k: int | None = None, llm_call: LLMCall | None = None) -> RagResult:
        question = (question or "").strip()
        context_k = context_k or config.get_context_top_k()
        query_terms = self.normalizer.tokens(question)
        hits = self.index.search(query_terms, min_score=config.MIN_SCORE)
        context_ids = [hit.doc_id for hit in hits[:context_k]]

        if not context_ids:
            return RagResult(
                question=question, query_terms=query_terms, retrieved=hits, context_ids=[],
                answer=config.REFUSAL_TEXT, sources=[], recipe=None, refusal=True,
                refusal_reason="no_retrieval_hits",
            )

        docs = [self.docs_by_id[doc_id] for doc_id in context_ids]
        messages = build_messages(question, docs)
        raw = (llm_call or chat)(messages)
        parsed = parse_llm_output(raw, context_ids, set(self.docs_by_id))

        if parsed.refusal:
            return RagResult(
                question=question, query_terms=query_terms, retrieved=hits, context_ids=context_ids,
                answer=config.REFUSAL_TEXT, sources=[], recipe=None, refusal=True,
                refusal_reason=parsed.refusal_reason, raw_llm_output=raw,
                invalid_sources=parsed.invalid_sources, llm_called=True,
            )

        recipe = self.docs_by_id[parsed.sources[0]].to_card()
        return RagResult(
            question=question, query_terms=query_terms, retrieved=hits, context_ids=context_ids,
            answer=parsed.answer, sources=parsed.sources, recipe=recipe, refusal=False,
            raw_llm_output=raw, invalid_sources=parsed.invalid_sources, llm_called=True,
        )


_engine: RagEngine | None = None
_engine_lock = threading.Lock()


def get_engine() -> RagEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = RagEngine()
    return _engine


def retrieve(question: str, k: int | None = 10) -> list[SearchHit]:
    return get_engine().retrieve(question, k)


def answer_question(question: str) -> dict:
    return get_engine().answer(question).to_contract()
