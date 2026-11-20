import math

import pytest

from rag.bm25 import BM25Index
from rag.text import simple_tokens

LECTURE_DOCS = {
    "A": "Возврат оплаты на карту",
    "B": "Статус оплаты в приложении",
    "C": "Возврат билета через кассу",
}


def lecture_index(order=("A", "B", "C")) -> BM25Index:
    return BM25Index([(doc_id, simple_tokens(LECTURE_DOCS[doc_id])) for doc_id in order], k1=1.2, b=0.75)


def test_lecture_example_scores_and_order():
    hits = lecture_index().search(simple_tokens("Как происходит возврат оплаты?"))
    assert [h.doc_id for h in hits] == ["A", "B", "C"]
    assert [h.rank for h in hits] == [1, 2, 3]
    assert hits[0].score == pytest.approx(0.940, abs=1e-3)
    assert hits[1].score == pytest.approx(0.470, abs=1e-3)
    assert hits[2].score == pytest.approx(0.470, abs=1e-3)


def test_lecture_example_top_k_two():
    hits = lecture_index().search(simple_tokens("Как происходит возврат оплаты?"), top_k=2)
    assert [h.doc_id for h in hits] == ["A", "B"]


def test_ties_sorted_by_id_regardless_of_insertion_order():
    hits = lecture_index(order=("C", "B", "A")).search(simple_tokens("возврат оплаты"))
    assert [h.doc_id for h in hits] == ["A", "B", "C"]


def test_idf_formula():
    index = lecture_index()
    assert index.idf("возврат") == pytest.approx(math.log(1 + (3 - 2 + 0.5) / (2 + 0.5)))
    assert index.idf("неизвестное") == pytest.approx(math.log(1 + 3.5 / 0.5))


def test_score_is_sum_of_term_contributions():
    index = BM25Index([("d1", ["a", "a", "b", "c"]), ("d2", ["a", "d"]), ("d3", ["e", "e", "e"])])
    query = ["a", "b", "z"]
    parts = index.contributions(query, "d1")
    assert parts["z"] == 0.0
    assert index.score(query, "d1") == pytest.approx(sum(parts.values()))
    hit = index.search(query)[0]
    assert hit.doc_id == "d1"
    assert hit.score == pytest.approx(index.score(query, "d1"))


def test_manual_bm25_value():
    index = BM25Index([("d1", ["a", "a", "b"]), ("d2", ["b"])], k1=1.2, b=0.75)
    avgdl = 2.0
    idf_a = math.log(1 + (2 - 1 + 0.5) / (1 + 0.5))
    expected = idf_a * 2 * 2.2 / (2 + 1.2 * (1 - 0.75 + 0.75 * 3 / avgdl))
    assert index.score(["a"], "d1") == pytest.approx(expected)


def test_repeated_query_terms_count_once():
    index = lecture_index()
    once = index.search(["возврат"])
    twice = index.search(["возврат", "возврат"])
    assert [(h.doc_id, h.score) for h in once] == [(h.doc_id, h.score) for h in twice]


def test_unknown_terms_empty_query_and_empty_corpus():
    index = lecture_index()
    assert index.search(["абракадабра"]) == []
    assert index.search([]) == []
    assert index.search(["возврат"], top_k=0) == []
    empty = BM25Index([])
    assert empty.N == 0 and empty.avgdl == 0
    assert empty.search(["возврат"]) == []


def test_documents_without_tokens_do_not_divide_by_zero():
    index = BM25Index([("d1", []), ("d2", [])])
    assert index.search(["a"]) == []
    assert index.score(["a"], "d1") == 0.0


def test_duplicate_ids_and_bad_params_rejected():
    with pytest.raises(ValueError):
        BM25Index([("d1", ["a"]), ("d1", ["b"])])
    with pytest.raises(ValueError):
        BM25Index([("d1", ["a"])], b=1.5)
    with pytest.raises(ValueError):
        BM25Index([("d1", ["a"])], k1=-1)


def test_search_is_stable_between_runs():
    query = simple_tokens("возврат оплаты")
    assert lecture_index().search(query) == lecture_index().search(query)
