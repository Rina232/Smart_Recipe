import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import config
from .generation import PROMPT_VERSION, SYSTEM_PROMPT, USER_REMINDER
from .corpus import CorpusError, file_sha256, load_corpus, load_questions, validate_benchmark
from .llm import LLMError, chat
from .metrics import first_relevant_rank, mean, recall_at_k, reciprocal_rank
from .pipeline import RagEngine, RagResult
from .text import Normalizer

Ask = Callable[[str], str]
Out = Callable[[str], None]


def check_facts(normalizer: Normalizer, answer: str, facts) -> list[str]:
    answer_terms = set(normalizer.tokens(answer))
    missing = []
    for alternatives in facts:
        satisfied = False
        for phrase in alternatives:
            terms = normalizer.tokens(phrase)
            if terms and set(terms) <= answer_terms:
                satisfied = True
                break
        if not satisfied:
            missing.append(" | ".join(alternatives))
    return missing


def grade_regular(result: RagResult, question, normalizer: Normalizer) -> tuple[bool, list[str]]:
    reasons = []
    if result.refusal:
        reasons.append(f"ответ — отказ ({result.refusal_reason})")
    else:
        missing = check_facts(normalizer, result.answer, question.required_facts)
        if missing:
            reasons.append("нет обязательных фактов: " + "; ".join(missing))
        if not set(result.sources) & set(question.relevant):
            reasons.append("среди sources нет ни одного эталонного релевантного документа")
    if result.invalid_sources:
        reasons.append("LLM сослалась на документы вне контекста: " + ", ".join(result.invalid_sources))
    return not reasons, reasons


def grade_trap(result: RagResult) -> tuple[bool, list[str]]:
    reasons = []
    if not result.refusal:
        reasons.append("система дала содержательный ответ вместо отказа")
    if result.sources:
        reasons.append("при отказе вернулись источники " + ", ".join(result.sources))
    if result.recipe is not None:
        reasons.append("при отказе вернулась карточка рецепта")
    return not reasons, reasons


def _hits_json(hits) -> list[dict]:
    return [{"rank": h.rank, "doc_id": h.doc_id, "score": round(h.score, 6)} for h in hits]


def _short(text: str, limit: int = 300) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _manual_grade(ask: Ask, out: Out, auto_ok: bool) -> bool:
    default = "y" if auto_ok else "n"
    while True:
        reply = ask(f"  Ответ полностью правильный? [y/n, Enter = {default}]: ").strip().lower()
        if reply == "":
            return auto_ok
        if reply in ("y", "yes", "д", "да"):
            return True
        if reply in ("n", "no", "н", "нет"):
            return False
        out("  Введите y или n.")


def _generation_error_category(item: dict, k: int) -> str:
    relevant = set(item["relevant"])
    if not item["retrieved"]:
        return "корпус/нормализация: у запроса нет общих термов с документами"
    if not relevant & set(item["context_ids"]):
        if relevant & set(item["top_k_ids"]):
            return "отбор контекста: релевантные документы есть в top-k, но не попали в контекст LLM"
        return "поиск: в контекст LLM не попал ни один релевантный документ"
    return "генерация: " + "; ".join(item["grade"]["reasons"])


def run_benchmark(
    engine: RagEngine,
    dataset,
    k: int,
    mrr_depth: int,
    context_k: int,
    llm_call: Callable[[list[dict]], str] | None,
    manual: bool = False,
    ask: Ask = input,
    out: Out = print,
) -> dict:
    depth = max(k, mrr_depth)
    regular_items, trap_items, errors = [], [], []
    llm_failures = 0

    out(f"\n=== Обычные вопросы ({len(dataset.regular)}) ===")
    for q in dataset.regular:
        hits = engine.retrieve(q.question, depth)
        ranked = [h.doc_id for h in hits]
        item = {
            "id": q.id,
            "question": q.question,
            "relevant": list(q.relevant),
            "reference_answer": q.reference_answer,
            "required_facts": [list(f) for f in q.required_facts],
            "query_terms": engine.normalizer.tokens(q.question),
            "retrieved": _hits_json(hits),
            "top_k_ids": ranked[:k],
            "recall_at_k": recall_at_k(ranked, q.relevant, k),
            "first_relevant_rank": first_relevant_rank(ranked, q.relevant, mrr_depth),
            "reciprocal_rank": reciprocal_rank(ranked, q.relevant, mrr_depth),
        }
        missing = [d for d in q.relevant if d not in ranked[:k]]
        if missing:
            ranks = {h.doc_id: h.rank for h in hits}
            detail = ", ".join(f"{d} (ранг {ranks[d]})" if d in ranks else f"{d} (не найден в top-{depth})" for d in missing)
            errors.append({"question_id": q.id, "stage": "retrieval", "category": "поиск",
                           "details": f"не попали в top-{k}: {detail}"})

        top_line = " ".join(f"{h.doc_id}{'*' if h.doc_id in q.relevant else ''}({h.score:.2f})" for h in hits[:k])
        out(f"\n{q.id}. {q.question}")
        out(f"  BM25 top-{k}: {top_line or '— нет совпадений'}")
        out(f"  Recall@{k} = {item['recall_at_k']:.2f}   RR = {item['reciprocal_rank']:.2f}")

        if llm_call is not None:
            started = time.perf_counter()
            try:
                result = engine.answer(q.question, context_k=context_k, llm_call=llm_call)
            except LLMError as exc:
                llm_failures += 1
                item.update({"llm_error": str(exc), "grade": None})
                errors.append({"question_id": q.id, "stage": "generation", "category": "LLM недоступна",
                               "details": str(exc)})
                out(f"  ОШИБКА LLM: {exc}")
            else:
                ok, reasons = grade_regular(result, q, engine.normalizer)
                item.update({
                    "seconds": round(time.perf_counter() - started, 2),
                    "context_ids": result.context_ids,
                    "answer": result.answer,
                    "sources": result.sources,
                    "recipe_title": result.recipe["title"] if result.recipe else None,
                    "refusal": result.refusal,
                    "refusal_reason": result.refusal_reason,
                    "invalid_sources": result.invalid_sources,
                    "raw_llm_output": result.raw_llm_output,
                    "auto_grade": {"correct": ok, "reasons": reasons},
                })
                out(f"  Контекст LLM: {', '.join(result.context_ids)}   sources: {', '.join(result.sources) or '—'}")
                out(f"  Ответ: {_short(result.answer)}")
                out(f"  Эталон: {_short(q.reference_answer)}")
                out(f"  Авто-проверка: {'ВЕРНО' if ok else 'НЕВЕРНО — ' + '; '.join(reasons)}")
                final = _manual_grade(ask, out, ok) if manual else ok
                item["grade"] = {"correct": final, "grader": "manual" if manual else "auto-checklist", "reasons": reasons}
                if not final:
                    errors.append({"question_id": q.id, "stage": "generation",
                                   "category": _generation_error_category(item, k).split(":")[0],
                                   "details": _generation_error_category(item, k)})
        regular_items.append(item)

    out(f"\n=== Вопросы-ловушки ({len(dataset.traps)}) ===")
    for q in dataset.traps:
        hits = engine.retrieve(q.question, depth)
        item = {
            "id": q.id,
            "question": q.question,
            "why_unanswerable": q.why_unanswerable,
            "query_terms": engine.normalizer.tokens(q.question),
            "retrieved": _hits_json(hits),
        }
        out(f"\n{q.id}. {q.question}")
        out(f"  BM25: {' '.join(f'{h.doc_id}({h.score:.2f})' for h in hits[:k]) or '— нет совпадений'}")
        if llm_call is not None:
            try:
                result = engine.answer(q.question, context_k=context_k, llm_call=llm_call)
            except LLMError as exc:
                llm_failures += 1
                item.update({"llm_error": str(exc), "grade": None})
                errors.append({"question_id": q.id, "stage": "generation", "category": "LLM недоступна",
                               "details": str(exc)})
                out(f"  ОШИБКА LLM: {exc}")
            else:
                ok, reasons = grade_trap(result)
                item.update({
                    "context_ids": result.context_ids,
                    "answer": result.answer,
                    "sources": result.sources,
                    "refusal": result.refusal,
                    "refusal_reason": result.refusal_reason,
                    "llm_called": result.llm_called,
                    "raw_llm_output": result.raw_llm_output,
                    "auto_grade": {"correct": ok, "reasons": reasons},
                })
                how = {"no_retrieval_hits": "BM25 ничего не нашёл, LLM не вызывалась",
                       "llm_no_answer": "LLM ответила НЕТ_ОТВЕТА",
                       "ungrounded_answer": "ответ LLM без ссылок на контекст отброшен",
                       "empty_answer": "пустой ответ LLM"}.get(result.refusal_reason, "")
                out(f"  Ответ: {_short(result.answer)}" + (f"   [{how}]" if how else ""))
                if result.raw_llm_output and not ok:
                    out(f"  Сырой ответ LLM: {_short(result.raw_llm_output)}")
                out(f"  Авто-проверка: {'КОРРЕКТНЫЙ ОТКАЗ' if ok else 'ОШИБКА — ' + '; '.join(reasons)}")
                final = _manual_grade(ask, out, ok) if manual else ok
                item["grade"] = {"correct": final, "grader": "manual" if manual else "auto-rule", "reasons": reasons}
                if not final:
                    errors.append({"question_id": q.id, "stage": "generation", "category": "генерация",
                                   "details": "ответ вместо отказа; контекст: " + ", ".join(result.context_ids)})
        trap_items.append(item)

    recall_values = [i["recall_at_k"] for i in regular_items]
    rr_values = [i["reciprocal_rank"] for i in regular_items]
    metrics = {
        "recall_at_k": {"k": k, "value": mean(recall_values), "n": len(recall_values)},
        "mrr": {"depth": mrr_depth, "value": mean(rr_values), "n": len(rr_values)},
    }
    graded_regular = [i["grade"]["correct"] for i in regular_items if i.get("grade")]
    graded_traps = [i["grade"]["correct"] for i in trap_items if i.get("grade")]
    if llm_call is None:
        note = "не посчитано: генерация не запускалась (LLM не настроена или указан --no-llm)"
        metrics["accuracy"] = {"value": None, "n": 0, "note": note}
        metrics["correct_rejection_rate"] = {"value": None, "n": 0, "note": note}
    else:
        grader = "ручная оценка" if manual else "авто-чек-лист (предварительно, подтвердите вручную через --manual)"
        if len(graded_regular) == len(regular_items) and regular_items:
            metrics["accuracy"] = {"value": sum(graded_regular) / len(graded_regular), "n": len(graded_regular),
                                   "correct": sum(graded_regular), "grader": grader}
        else:
            metrics["accuracy"] = {"value": None, "n": len(graded_regular),
                                   "note": f"не посчитано: {len(regular_items) - len(graded_regular)} ответов не получено из-за ошибок LLM"}
        if len(graded_traps) == len(trap_items) and trap_items:
            metrics["correct_rejection_rate"] = {"value": sum(graded_traps) / len(graded_traps), "n": len(graded_traps),
                                                 "correct": sum(graded_traps), "grader": grader}
        else:
            metrics["correct_rejection_rate"] = {"value": None, "n": len(graded_traps),
                                                 "note": f"не посчитано: {len(trap_items) - len(graded_traps)} ответов не получено из-за ошибок LLM"}

    if llm_call is None:
        status = "retrieval_only"
    elif llm_failures:
        status = "llm_errors"
    else:
        status = "complete"
    return {"status": status, "llm_failures": llm_failures, "metrics": metrics,
            "regular": regular_items, "traps": trap_items, "errors": errors}


def _fmt(metric: dict) -> str:
    return "—  (" + metric.get("note", "нет данных") + ")" if metric["value"] is None else f"{metric['value']:.3f}"


def print_summary(report: dict, out: Out = print) -> None:
    m = report["metrics"]
    out("\n=== Итоговые метрики ===")
    out(f"Recall@{m['recall_at_k']['k']:<3} (10 обычных вопросов): {_fmt(m['recall_at_k'])}")
    out(f"MRR, глубина {m['mrr']['depth']:<3} (10 обычных вопросов): {_fmt(m['mrr'])}")
    acc = m["accuracy"]
    out(f"Accuracy  (обычные вопросы):           {_fmt(acc)}" + (f"  [{acc['correct']}/{acc['n']}, {acc['grader']}]" if acc["value"] is not None else ""))
    crr = m["correct_rejection_rate"]
    out(f"Correct Rejection Rate (ловушки):      {_fmt(crr)}" + (f"  [{crr['correct']}/{crr['n']}, {crr['grader']}]" if crr["value"] is not None else ""))
    out("\n=== Разбор ошибок ===")
    if not report["errors"]:
        out("Ошибок не обнаружено.")
    for err in report["errors"]:
        out(f"- {err['question_id']} [{err['stage']}] {err['details']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m rag.benchmark", description="Бенчмарк КТ2 для RAG Smart Recipe")
    parser.add_argument("--k", type=int, default=config.DEFAULT_BENCHMARK_K, help="k для Recall@k")
    parser.add_argument("--mrr-depth", type=int, default=config.DEFAULT_MRR_DEPTH, help="глубина поиска первого релевантного для MRR")
    parser.add_argument("--context-k", type=int, default=None, help="сколько документов BM25 передавать в LLM")
    parser.add_argument("--no-llm", action="store_true", help="только поисковые метрики, без генерации")
    parser.add_argument("--manual", action="store_true", help="ручная оценка каждого ответа")
    parser.add_argument("--corpus", type=Path, default=config.DEFAULT_CORPUS_PATH)
    parser.add_argument("--questions", type=Path, default=config.DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--output", type=Path, default=config.DEFAULT_RESULTS_PATH)
    parser.add_argument("--normalizer", choices=["auto", "pymorphy3", "stem", "none"], default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    if args.k < 1 or args.mrr_depth < 1:
        print("k и --mrr-depth должны быть >= 1", file=sys.stderr)
        return 2

    try:
        docs = load_corpus(args.corpus)
        dataset = load_questions(args.questions)
    except CorpusError as exc:
        print(f"Ошибка данных: {exc}", file=sys.stderr)
        return 2
    problems = validate_benchmark(docs, dataset)
    if problems:
        print("Набор для бенчмарка некорректен:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    context_k = args.context_k or config.get_context_top_k()
    engine = RagEngine(documents=docs, normalizer_mode=args.normalizer)
    settings = config.get_llm_settings()

    print("Smart Recipe — бенчмарк КТ2 (каждый запуск заново выполняет поиск и генерацию)")
    print(f"Корпус: {len(docs)} документов, обычных вопросов: {len(dataset.regular)}, ловушек: {len(dataset.traps)}")
    print(f"BM25: k1={engine.index.k1}, b={engine.index.b}; нормализация: {engine.normalizer.mode}")
    print(f"Recall@k: k={args.k}; MRR: глубина {args.mrr_depth}; документов в контексте LLM: {context_k}")
    print("ВНИМАНИЕ: k и глубина MRR выбраны по умолчанию и требуют подтверждения преподавателем.")

    llm_call = None
    if args.no_llm:
        print("LLM: отключена флагом --no-llm — будут посчитаны только Recall@k и MRR.")
    elif not settings.configured:
        print("LLM: НЕ НАСТРОЕНА — " + "; ".join(settings.problems))
        print("Accuracy и Correct Rejection Rate не будут посчитаны: нет реальных ответов LLM. См. rag/README.md.")
    else:
        print(f"LLM: {settings.provider}, модель {settings.model}, {settings.base_url}, temperature={settings.temperature}, seed={settings.seed}, промпт {PROMPT_VERSION}")
        llm_call = lambda messages: chat(messages, settings)

    started = datetime.now(timezone.utc)
    try:
        report = run_benchmark(engine, dataset, args.k, args.mrr_depth, context_k, llm_call, manual=args.manual)
    except KeyboardInterrupt:
        print("\nБенчмарк прерван (Ctrl+C). Результаты не сохранены, метрики не посчитаны.", file=sys.stderr)
        return 130
    report = {
        "generated_at": started.isoformat(timespec="seconds"),
        "status": report.pop("status"),
        "settings": {
            "k": args.k,
            "k_confirmed_by_teacher": False,
            "mrr_depth": args.mrr_depth,
            "context_top_k": context_k,
            "bm25": {"k1": engine.index.k1, "b": engine.index.b, "min_score": config.MIN_SCORE},
            "normalizer": engine.normalizer.describe(),
            "llm": settings.public_dict() if llm_call else None,
            "prompt": {
                "version": PROMPT_VERSION,
                "sha256": hashlib.sha256((SYSTEM_PROMPT + USER_REMINDER).encode("utf-8")).hexdigest(),
            },
            "grading": "manual" if args.manual else "auto",
        },
        "dataset": {
            "corpus_path": str(args.corpus),
            "corpus_sha256": file_sha256(args.corpus),
            "questions_path": str(args.questions),
            "questions_sha256": file_sha256(args.questions),
            "documents": len(docs),
            "regular_questions": len(dataset.regular),
            "trap_questions": len(dataset.traps),
        },
        **report,
    }
    print_summary(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nПодробные результаты: {args.output}")
    if report["status"] == "complete" or args.no_llm:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
