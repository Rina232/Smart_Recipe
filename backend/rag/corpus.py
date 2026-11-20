import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import DEFAULT_CORPUS_PATH, DEFAULT_QUESTIONS_PATH

NUTRITION_KEYS = ("calories_kcal", "protein_g", "fat_g", "carbs_g")


class CorpusError(ValueError):
    pass


@dataclass(frozen=True)
class RecipeDoc:
    id: str
    title: str
    ingredients: tuple[tuple[str, str], ...] = ()
    steps: tuple[str, ...] = ()
    text: str = ""
    servings: int | None = None
    cooking_time_minutes: int | None = None
    nutrition: dict | None = None
    image_url: str | None = None
    source: dict = field(default_factory=dict)

    def index_text(self) -> str:
        parts = [self.title]
        parts.extend(name for name, _ in self.ingredients)
        parts.extend(self.steps)
        if self.text:
            parts.append(self.text)
        return "\n".join(parts)

    def ingredient_lines(self) -> list[str]:
        return [f"{name} — {amount}" if amount else name for name, amount in self.ingredients]

    def context_text(self) -> str:
        lines = [f"Название: {self.title}"]
        if self.servings is not None:
            lines.append(f"Порций: {self.servings}")
        if self.cooking_time_minutes is not None:
            lines.append(f"Время приготовления: {self.cooking_time_minutes} мин")
        if self.nutrition:
            known = {k: v for k, v in self.nutrition.items() if v is not None}
            if known:
                labels = {"calories_kcal": "ккал", "protein_g": "белки, г", "fat_g": "жиры, г", "carbs_g": "углеводы, г"}
                lines.append("Пищевая ценность на порцию: " + ", ".join(f"{labels[k]}: {v}" for k, v in known.items()))
        if self.ingredients:
            lines.append("Ингредиенты:")
            lines.extend(f"- {line}" for line in self.ingredient_lines())
        if self.steps:
            lines.append("Приготовление:")
            lines.extend(f"{i}. {step}" for i, step in enumerate(self.steps, 1))
        if self.text:
            lines.append(self.text)
        return "\n".join(lines)

    def to_card(self) -> dict | None:
        if not self.ingredients:
            return None
        nutrition = self.nutrition or {}
        card = {
            "title": self.title,
            "image_url": self.image_url,
            "cooking_time_minutes": self.cooking_time_minutes,
            "ingredients": self.ingredient_lines(),
        }
        for key in NUTRITION_KEYS:
            value = nutrition.get(key)
            card[key] = float(value) if value is not None else None
        return card


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path: Path) -> object:
    path = Path(path)
    if not path.is_file():
        raise CorpusError(f"Файл не найден: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise CorpusError(f"{path.name}: ошибка JSON в строке {exc.lineno}, столбце {exc.colno}: {exc.msg}") from None


def _optional_number(raw: dict, key: str, doc_id: str, integer: bool) -> int | float | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (integer and not isinstance(value, int)):
        raise CorpusError(f"{doc_id}: поле {key} должно быть {'целым ' if integer else ''}числом или null")
    if value < 0:
        raise CorpusError(f"{doc_id}: поле {key} не может быть отрицательным")
    return value


def _parse_doc(raw: object, position: int) -> RecipeDoc:
    if not isinstance(raw, dict):
        raise CorpusError(f"Документ №{position}: ожидается объект JSON")
    doc_id = raw.get("id")
    if not isinstance(doc_id, str) or not doc_id.strip():
        raise CorpusError(f"Документ №{position}: нет строкового поля id")
    doc_id = doc_id.strip()
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise CorpusError(f"{doc_id}: нет непустого поля title")

    ingredients = []
    for item in raw.get("ingredients") or []:
        if isinstance(item, str) and item.strip():
            ingredients.append((item.strip(), ""))
        elif isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip():
            amount = item.get("amount") or ""
            if not isinstance(amount, str):
                raise CorpusError(f"{doc_id}: amount ингредиента должен быть строкой")
            ingredients.append((item["name"].strip(), amount.strip()))
        else:
            raise CorpusError(f"{doc_id}: ингредиент должен быть строкой или объектом с полем name")

    steps = raw.get("steps") or []
    if not isinstance(steps, list) or not all(isinstance(s, str) and s.strip() for s in steps):
        raise CorpusError(f"{doc_id}: steps должен быть списком непустых строк")
    text = raw.get("text") or ""
    if not isinstance(text, str):
        raise CorpusError(f"{doc_id}: text должен быть строкой")
    if not ingredients and not steps and not text.strip():
        raise CorpusError(f"{doc_id}: нужен хотя бы один из блоков ingredients, steps или text")

    nutrition = raw.get("nutrition")
    if nutrition is not None:
        if not isinstance(nutrition, dict):
            raise CorpusError(f"{doc_id}: nutrition должен быть объектом или null")
        unknown = set(nutrition) - set(NUTRITION_KEYS)
        if unknown:
            raise CorpusError(f"{doc_id}: неизвестные поля nutrition: {', '.join(sorted(unknown))}")
        nutrition = {k: _optional_number(nutrition, k, doc_id, integer=False) for k in NUTRITION_KEYS}

    image_url = raw.get("image_url")
    if image_url is not None and not isinstance(image_url, str):
        raise CorpusError(f"{doc_id}: image_url должен быть строкой или null")
    source = raw.get("source") or {}
    if not isinstance(source, dict):
        raise CorpusError(f"{doc_id}: source должен быть объектом")

    return RecipeDoc(
        id=doc_id,
        title=title.strip(),
        ingredients=tuple(ingredients),
        steps=tuple(s.strip() for s in steps),
        text=text.strip(),
        servings=_optional_number(raw, "servings", doc_id, integer=True),
        cooking_time_minutes=_optional_number(raw, "cooking_time_minutes", doc_id, integer=True),
        nutrition=nutrition,
        image_url=image_url,
        source=source,
    )


def load_corpus(path: Path | str = DEFAULT_CORPUS_PATH) -> list[RecipeDoc]:
    data = _read_json(Path(path))
    raw_docs = data.get("documents") if isinstance(data, dict) else data
    if not isinstance(raw_docs, list):
        raise CorpusError("Корпус должен быть списком документов или объектом с полем documents")
    docs = [_parse_doc(raw, i) for i, raw in enumerate(raw_docs, 1)]
    seen = set()
    for doc in docs:
        if doc.id in seen:
            raise CorpusError(f"Повторяющийся ID документа: {doc.id}")
        seen.add(doc.id)
    return docs


@dataclass(frozen=True)
class RegularQuestion:
    id: str
    question: str
    relevant: tuple[str, ...]
    reference_answer: str
    required_facts: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class TrapQuestion:
    id: str
    question: str
    why_unanswerable: str


@dataclass(frozen=True)
class BenchmarkSet:
    regular: tuple[RegularQuestion, ...]
    traps: tuple[TrapQuestion, ...]


def load_questions(path: Path | str = DEFAULT_QUESTIONS_PATH) -> BenchmarkSet:
    data = _read_json(Path(path))
    if not isinstance(data, dict):
        raise CorpusError("Файл вопросов должен быть объектом с полями regular и traps")
    regular, traps = [], []
    for raw in data.get("regular") or []:
        if not isinstance(raw, dict):
            raise CorpusError("Каждый обычный вопрос должен быть объектом")
        facts = raw.get("required_facts") or []
        if not isinstance(facts, list) or not all(
            isinstance(f, list) and f and all(isinstance(x, str) and x.strip() for x in f) for f in facts
        ):
            raise CorpusError(f"{raw.get('id')}: required_facts должен быть списком непустых списков строк")
        relevant = raw.get("relevant") or []
        if not isinstance(relevant, list) or not all(isinstance(x, str) for x in relevant):
            raise CorpusError(f"{raw.get('id')}: relevant должен быть списком строк")
        regular.append(RegularQuestion(
            id=str(raw.get("id") or "").strip(),
            question=str(raw.get("question") or "").strip(),
            relevant=tuple(relevant),
            reference_answer=str(raw.get("reference_answer") or "").strip(),
            required_facts=tuple(tuple(f) for f in facts),
        ))
    for raw in data.get("traps") or []:
        if not isinstance(raw, dict):
            raise CorpusError("Каждый вопрос-ловушка должен быть объектом")
        traps.append(TrapQuestion(
            id=str(raw.get("id") or "").strip(),
            question=str(raw.get("question") or "").strip(),
            why_unanswerable=str(raw.get("why_unanswerable") or "").strip(),
        ))
    return BenchmarkSet(regular=tuple(regular), traps=tuple(traps))


def validate_benchmark(
    docs: list[RecipeDoc],
    questions: BenchmarkSet,
    expected_docs: int = 30,
    expected_regular: int = 10,
    expected_traps: int = 5,
    min_relevant: int = 3,
) -> list[str]:
    problems = []
    doc_ids = {d.id for d in docs}
    if len(docs) != expected_docs:
        problems.append(f"В корпусе {len(docs)} документов, ожидается {expected_docs}")
    if len(questions.regular) != expected_regular:
        problems.append(f"Обычных вопросов {len(questions.regular)}, ожидается {expected_regular}")
    if len(questions.traps) != expected_traps:
        problems.append(f"Вопросов-ловушек {len(questions.traps)}, ожидается {expected_traps}")
    seen = set()
    for q in (*questions.regular, *questions.traps):
        if not q.id:
            problems.append("Есть вопрос без ID")
        elif q.id in seen:
            problems.append(f"Повторяющийся ID вопроса: {q.id}")
        seen.add(q.id)
        if not q.question:
            problems.append(f"{q.id}: пустой текст вопроса")
    for q in questions.regular:
        unique = set(q.relevant)
        if len(unique) != len(q.relevant):
            problems.append(f"{q.id}: в relevant есть повторы")
        if len(unique) < min_relevant:
            problems.append(f"{q.id}: релевантных документов {len(unique)}, нужно минимум {min_relevant}")
        missing = sorted(unique - doc_ids)
        if missing:
            problems.append(f"{q.id}: в корпусе нет документов {', '.join(missing)}")
        if not q.reference_answer:
            problems.append(f"{q.id}: нет эталонного ответа reference_answer")
        if not q.required_facts:
            problems.append(f"{q.id}: нет чек-листа required_facts")
    for q in questions.traps:
        if not q.why_unanswerable:
            problems.append(f"{q.id}: не объяснено, почему ответа нет в корпусе")
    return problems
