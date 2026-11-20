import re
from dataclasses import dataclass, field

from .corpus import RecipeDoc

NO_ANSWER_MARKER = "НЕТ_ОТВЕТА"

PROMPT_VERSION = "v3"

SYSTEM_PROMPT = f"""Ты — помощник сервиса Smart Recipe. Пользователь спрашивает, что приготовить. В разделе КОНТЕКСТ даны рецепты из базы: у каждого есть ID в квадратных скобках и строка «Название: ...». Выбери подходящие рецепты и расскажи о них на русском языке.

Как отвечать:
- Описание каждого подходящего рецепта начинай с его настоящего названия из строки «Название:» (само слово «Название» не пиши) и ID в квадратных скобках.
- Затем кратко перечисли главные ингредиенты и основные шаги из этого же документа.
- Каждый рецепт упоминай один раз.
- Рецепт подходит, если в нём есть продукт из вопроса или он относится к нужному виду блюда (суп, салат, десерт и т. п.). Это обычная ситуация — в ней нужно отвечать.
- Если в вопросе есть условие (например, без мяса или на завтрак), проверь его по ингредиентам и шагам и выбери рецепты, которые ему соответствуют.
- Используй только сведения из контекста. Не придумывай ингредиенты, время, калорийность, БЖУ и шаги, которых нет в документах.
- Последней строкой напиши: ИСТОЧНИКИ: ID через запятую.

Отказ: только если ни один рецепт из контекста не отвечает на вопрос (например, спрашивают про блюдо или продукт, которого в контексте нет) или нужны сведения, которых в документах нет (например, калорийность, когда она не указана), напиши одно слово {NO_ANSWER_MARKER} и больше ничего."""

USER_REMINDER = (
    "Ответь по правилам: назови подходящие блюда их настоящими названиями из контекста с [ID] и добавь строку ИСТОЧНИКИ. "
    f"Если подходящих рецептов в контексте нет — одно слово {NO_ANSWER_MARKER}."
)

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
MARKER_RE = re.compile(r"НЕТ[_\s]ОТВЕТА", re.IGNORECASE)
SOURCES_LINE_RE = re.compile(r"^[ \t>*_#-]*источники[ \t*_]*:(.*)$", re.IGNORECASE | re.MULTILINE)
TRAILING_SOURCES_RE = re.compile(r"[ \t]*\**источники\**[ \t]*:([^\n]*)$", re.IGNORECASE)
TITLE_LABEL_RE = re.compile(r"Название:\s*", re.IGNORECASE)
ID_RE = re.compile(r"(?<![A-Za-zА-Яа-я0-9])([A-Za-zА-Яа-я]{1,3})\s?-?(\d{1,4})(?![0-9])")
CYRILLIC_TO_LATIN = str.maketrans("ДдАаВвСсЕеКкМмНнОоРрТтХх", "DdAaBbCcEeKkMmHhOoPpTtXx")


def build_messages(question: str, docs: list[RecipeDoc]) -> list[dict]:
    blocks = [f"[{doc.id}]\n{doc.context_text()}" for doc in docs]
    user = "КОНТЕКСТ:\n\n" + "\n\n".join(blocks) + f"\n\nВОПРОС: {question}\n\n{USER_REMINDER}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


@dataclass
class ParsedAnswer:
    refusal: bool
    answer: str
    sources: list[str] = field(default_factory=list)
    invalid_sources: list[str] = field(default_factory=list)
    refusal_reason: str | None = None


def _candidate_ids(text: str, known_ids: set[str]) -> list[str]:
    found = []
    for prefix, number in ID_RE.findall(text):
        raw = prefix + number
        variants = [raw, raw.upper(), raw.translate(CYRILLIC_TO_LATIN).upper()]
        if number.isdigit():
            latin_prefix = prefix.translate(CYRILLIC_TO_LATIN).upper()
            variants.append(f"{latin_prefix}{int(number):02d}")
        match = next((v for v in variants if v in known_ids), None)
        if match is not None:
            found.append(match)
        elif prefix.translate(CYRILLIC_TO_LATIN).upper() == "D":
            found.append(raw.translate(CYRILLIC_TO_LATIN).upper())
    return list(dict.fromkeys(found))


def parse_llm_output(text: str, context_ids: list[str], corpus_ids: set[str] | None = None) -> ParsedAnswer:
    cleaned = THINK_RE.sub("", text).strip()
    if MARKER_RE.search(cleaned):
        return ParsedAnswer(refusal=True, answer="", refusal_reason="llm_no_answer")

    line_ids: list[str] = []
    known = set(context_ids) | (corpus_ids or set())
    for match in SOURCES_LINE_RE.finditer(cleaned):
        line_ids.extend(_candidate_ids(match.group(1), known))
    for match in TRAILING_SOURCES_RE.finditer(cleaned):
        line_ids.extend(_candidate_ids(match.group(1), known))
    body = SOURCES_LINE_RE.sub("", cleaned)
    body = TRAILING_SOURCES_RE.sub("", body)
    body = TITLE_LABEL_RE.sub("", body).strip()
    inline_ids = _candidate_ids(body, known)

    cited = list(dict.fromkeys(line_ids + inline_ids))
    allowed = set(context_ids)
    valid = [doc_id for doc_id in cited if doc_id in allowed]
    invalid = [doc_id for doc_id in cited if doc_id not in allowed]

    if not body:
        return ParsedAnswer(refusal=True, answer="", invalid_sources=invalid, refusal_reason="empty_answer")
    if not valid:
        return ParsedAnswer(refusal=True, answer=body, invalid_sources=invalid, refusal_reason="ungrounded_answer")
    order = {doc_id: i for i, doc_id in enumerate(context_ids)}
    valid.sort(key=lambda d: (d not in line_ids, order[d]))
    return ParsedAnswer(refusal=False, answer=body, sources=valid, invalid_sources=invalid)
