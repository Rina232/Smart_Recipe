from typing import Iterable, Sequence


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        raise ValueError("Для Recall@k нужен хотя бы один релевантный документ")
    if k < 1:
        raise ValueError("k должен быть >= 1")
    return len(relevant & set(ranked_ids[:k])) / len(relevant)


def first_relevant_rank(ranked_ids: Sequence[str], relevant_ids: Iterable[str], depth: int) -> int | None:
    relevant = set(relevant_ids)
    for position, doc_id in enumerate(ranked_ids[:depth], 1):
        if doc_id in relevant:
            return position
    return None


def reciprocal_rank(ranked_ids: Sequence[str], relevant_ids: Iterable[str], depth: int) -> float:
    if depth < 1:
        raise ValueError("Глубина MRR должна быть >= 1")
    rank = first_relevant_rank(ranked_ids, relevant_ids, depth)
    return 0.0 if rank is None else 1.0 / rank


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None
