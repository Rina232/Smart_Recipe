import json
import re

import pytest

from rag.benchmark import check_facts, main, run_benchmark
from rag.corpus import BenchmarkSet, RecipeDoc, RegularQuestion, TrapQuestion
from rag.metrics import first_relevant_rank, mean, recall_at_k, reciprocal_rank
from rag.pipeline import RagEngine
from rag.text import Normalizer


def test_recall_at_k_formula():
    assert recall_at_k(["a", "x", "b", "c"], ["a", "b", "c"], 2) == pytest.approx(1 / 3)
    assert recall_at_k(["a", "x", "b", "c"], ["a", "b", "c"], 4) == 1.0
    assert recall_at_k([], ["a"], 5) == 0.0
    with pytest.raises(ValueError):
        recall_at_k(["a"], [], 5)


def test_reciprocal_rank_and_depth():
    assert reciprocal_rank(["x", "y", "a"], ["a"], 10) == pytest.approx(1 / 3)
    assert reciprocal_rank(["x", "y", "a"], ["a"], 2) == 0.0
    assert first_relevant_rank(["a"], ["a"], 1) == 1
    assert mean([1.0, 0.5, 0.0]) == pytest.approx(0.5)
    assert mean([]) is None


def test_fact_checklist_uses_normalization():
    normalizer = Normalizer("stem")
    assert check_facts(normalizer, "Подойдут сырники [D10]", [["сырники", "запеканка"]]) == []
    assert check_facts(normalizer, "Сделайте творожную запеканку", [["запеканка"]]) == []
    assert check_facts(normalizer, "Пирог с вишней", [["сырники", "запеканка"]]) == ["сырники | запеканка"]


def tiny_setup():
    docs = [
        RecipeDoc(id="D01", title="Омлет", ingredients=(("Яйца", "3 шт."), ("Молоко", "50 мл")), steps=("Взбейте яйца и пожарьте.",)),
        RecipeDoc(id="D02", title="Яичница", ingredients=(("Яйца", "2 шт."),), steps=("Пожарьте яйца.",)),
        RecipeDoc(id="D03", title="Борщ", ingredients=(("Свёкла", "1 шт."),), steps=("Сварите борщ.",)),
        RecipeDoc(id="D04", title="Сырники", ingredients=(("Творог", "300 г"), ("Яйца", "1 шт.")), steps=("Пожарьте сырники.",)),
    ]
    dataset = BenchmarkSet(
        regular=(RegularQuestion(id="Q1", question="Что сделать из яйца?", relevant=("D01", "D02"),
                                 reference_answer="Омлет [D01] или яичница [D02].", required_facts=(("омлет", "яичница"),)),),
        traps=(TrapQuestion(id="T1", question="Как сварить борщ на 1000 человек?", why_unanswerable="нет данных"),
               TrapQuestion(id="T2", question="Как приготовить суши?", why_unanswerable="нет суши")),
    )
    return RagEngine(documents=docs, normalizer_mode="stem"), dataset


def scripted_llm(messages):
    ids = re.findall(r"^\[(D\d+)\]$", messages[-1]["content"], flags=re.MULTILINE)
    if "борщ" in messages[-1]["content"].split("ВОПРОС:")[1]:
        return "Возьмите 100 кастрюль [D03].\nИСТОЧНИКИ: D03"
    return f"Приготовьте омлет [{ids[0]}].\nИСТОЧНИКИ: {ids[0]}"


def test_run_benchmark_separates_retrieval_and_generation_metrics():
    engine, dataset = tiny_setup()
    report = run_benchmark(engine, dataset, k=1, mrr_depth=10, context_k=2, llm_call=scripted_llm, out=lambda s: None)
    m = report["metrics"]
    assert m["recall_at_k"]["value"] == pytest.approx(0.5)
    assert m["mrr"]["value"] == pytest.approx(1.0)
    assert m["accuracy"]["value"] == 1.0
    assert m["correct_rejection_rate"]["value"] == pytest.approx(0.5)
    trap_by_id = {t["id"]: t for t in report["traps"]}
    assert trap_by_id["T2"]["refusal_reason"] == "no_retrieval_hits"
    assert trap_by_id["T1"]["grade"]["correct"] is False
    assert report["regular"][0]["retrieved"][0]["doc_id"] in {"D01", "D02"}
    assert any(e["stage"] == "retrieval" for e in report["errors"])
    assert report["status"] == "complete"


def test_run_without_llm_does_not_report_generation_metrics():
    engine, dataset = tiny_setup()
    report = run_benchmark(engine, dataset, k=2, mrr_depth=10, context_k=2, llm_call=None, out=lambda s: None)
    assert report["metrics"]["recall_at_k"]["value"] == 1.0
    assert report["metrics"]["accuracy"]["value"] is None
    assert report["metrics"]["correct_rejection_rate"]["value"] is None
    assert report["status"] == "retrieval_only"


def test_manual_grading_overrides_auto():
    engine, dataset = tiny_setup()
    answers = iter(["n", "", ""])
    report = run_benchmark(engine, dataset, k=2, mrr_depth=10, context_k=2, llm_call=scripted_llm,
                           manual=True, ask=lambda prompt: next(answers), out=lambda s: None)
    assert report["metrics"]["accuracy"]["value"] == 0.0
    assert report["regular"][0]["grade"]["grader"] == "manual"


def test_cli_retrieval_only_writes_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("rag.config.load_env_file", lambda path=None: None)
    for name in ("RAG_LLM_PROVIDER", "RAG_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    output = tmp_path / "results.json"
    code = main(["--no-llm", "--normalizer", "stem", "--output", str(output)])
    assert code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["dataset"]["documents"] == 30
    assert len(report["regular"]) == 10 and len(report["traps"]) == 5
    assert report["metrics"]["recall_at_k"]["k"] == 5
    assert 0 <= report["metrics"]["recall_at_k"]["value"] <= 1
    assert report["metrics"]["accuracy"]["value"] is None
    assert "Recall@5" in capsys.readouterr().out


def test_cli_rejects_invalid_dataset(tmp_path):
    bad = tmp_path / "questions.json"
    bad.write_text(json.dumps({"regular": [], "traps": []}), encoding="utf-8")
    assert main(["--no-llm", "--questions", str(bad), "--output", str(tmp_path / "r.json")]) == 2


def test_template_placeholder_answer_fails_q01_checklist():
    from rag.corpus import load_questions

    q01 = load_questions().regular[0]
    answer = "Подойдёт <название блюда> [D02]: паста, куриное филе, шампиньоны, сливки [D02]."
    assert check_facts(Normalizer("stem"), answer, q01.required_facts) != []
    assert check_facts(Normalizer("stem"), "Паста с курицей и грибами [D02]", q01.required_facts) == []
