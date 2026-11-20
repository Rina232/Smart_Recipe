import re

import pytest

from rag import config
from rag.corpus import load_corpus, load_questions, validate_benchmark
from rag.generation import parse_llm_output
from rag.llm import LLMError
from rag.pipeline import RagEngine

try:
    from app.schemas import RagAnswer
except ImportError:
    RagAnswer = None


@pytest.fixture(scope="module")
def engine():
    return RagEngine(normalizer_mode="stem")


def fake_llm(reply):
    calls = []

    def call(messages):
        calls.append(messages)
        return reply(messages) if callable(reply) else reply

    call.calls = calls
    return call


def context_ids_from(messages):
    return re.findall(r"^\[(D\d+)\]$", messages[-1]["content"], flags=re.MULTILINE)


def assert_contract(result: dict, corpus_ids: set[str]):
    assert set(result) <= {"answer", "sources", "recipe"}
    assert isinstance(result["answer"], str) and result["answer"].strip()
    assert isinstance(result["sources"], list)
    assert all(isinstance(s, str) and s in corpus_ids for s in result["sources"])
    if RagAnswer is not None:
        RagAnswer.model_validate(result)


def test_corpus_has_30_documents_with_stable_ids():
    docs = load_corpus()
    assert [d.id for d in docs] == [f"D{i:02d}" for i in range(1, 31)]
    assert all(d.title and d.ingredients and d.steps for d in docs)


def test_benchmark_dataset_is_valid():
    assert validate_benchmark(load_corpus(), load_questions()) == []


def test_retrieve_finds_chicken_and_mushrooms(engine):
    top3 = [h.doc_id for h in engine.retrieve("Что приготовить из курицы и грибов?", 3)]
    assert set(top3) == {"D01", "D02", "D03"}


def test_answer_uses_context_and_returns_valid_contract(engine):
    llm = fake_llm(lambda m: f"Подойдёт паста с курицей и грибами [{context_ids_from(m)[0]}].\nИСТОЧНИКИ: {context_ids_from(m)[0]}")
    result = engine.answer("Что приготовить из курицы и грибов?", context_k=3, llm_call=llm)
    contract = result.to_contract()
    assert_contract(contract, set(engine.docs_by_id))
    assert contract["sources"] == [result.context_ids[0]]
    assert len(llm.calls) == 1
    user_prompt = llm.calls[0][-1]["content"]
    assert "КОНТЕКСТ" in user_prompt and "Что приготовить из курицы и грибов?" in user_prompt
    assert len(context_ids_from(llm.calls[0])) == 3
    card = contract["recipe"]
    assert card["title"] == engine.docs_by_id[contract["sources"][0]].title
    assert card["calories_kcal"] is None and card["protein_g"] is None
    assert card["ingredients"]


def test_hallucinated_source_ids_are_dropped(engine):
    llm = fake_llm(lambda m: f"Жюльен [{context_ids_from(m)[0]}] и суши [D99].\nИСТОЧНИКИ: {context_ids_from(m)[0]}, D99, D30")
    result = engine.answer("Что приготовить из курицы и грибов?", context_k=3, llm_call=llm)
    assert result.sources == [result.context_ids[0]]
    assert "D99" in result.invalid_sources and "D30" in result.invalid_sources
    assert_contract(result.to_contract(), set(engine.docs_by_id))


def test_llm_refusal_marker_gives_empty_sources(engine):
    result = engine.answer("Сколько калорий в одной порции борща?", llm_call=fake_llm("НЕТ_ОТВЕТА"))
    contract = result.to_contract()
    assert result.refusal and result.refusal_reason == "llm_no_answer"
    assert contract == {"answer": config.REFUSAL_TEXT, "sources": []}
    assert_contract(contract, set(engine.docs_by_id))


def test_no_retrieval_hits_refuses_without_calling_llm(engine):
    llm = fake_llm("не должна вызываться")
    result = engine.answer("Как приготовить суши с угрём?", llm_call=llm)
    assert llm.calls == []
    assert result.refusal_reason == "no_retrieval_hits"
    assert result.to_contract() == {"answer": config.REFUSAL_TEXT, "sources": []}


def test_answer_without_valid_citations_is_rejected(engine):
    result = engine.answer("Что приготовить с гречкой?", llm_call=fake_llm("Сварите плов с бараниной.\nИСТОЧНИКИ: D77"))
    assert result.refusal and result.refusal_reason == "ungrounded_answer"
    assert result.to_contract() == {"answer": config.REFUSAL_TEXT, "sources": []}


def test_llm_error_is_not_masked(engine):
    def broken(messages):
        raise LLMError("сервер недоступен")

    with pytest.raises(LLMError):
        engine.answer("Что приготовить с гречкой?", llm_call=broken)


def test_parse_sources_variants():
    parsed = parse_llm_output("Шарлотка [Д28], оладьи [D 30].\n**Источники:** d28, D30", ["D28", "D29", "D30"])
    assert parsed.sources == ["D28", "D30"]
    assert parsed.answer == "Шарлотка [Д28], оладьи [D 30]."
    parsed = parse_llm_output("<think>размышления D05</think>НЕТ_ОТВЕТА", ["D05"])
    assert parsed.refusal


def test_public_answer_question_signature():
    import inspect

    from rag import pipeline

    params = list(inspect.signature(pipeline.answer_question).parameters)
    assert params == ["question"]


def test_inline_sources_and_title_label_are_cleaned():
    parsed = parse_llm_output("Подойдёт Название: Сырники [D10]: творог, яйцо. ИСТОЧНИКИ: D10, D12", ["D10", "D11", "D12"])
    assert parsed.answer == "Подойдёт Сырники [D10]: творог, яйцо."
    assert parsed.sources == ["D10", "D12"]


def test_refusal_with_empty_sources_line():
    assert parse_llm_output("НЕТ_ОТВЕТА ИСТОЧНИКИ:", ["D13"]).refusal
