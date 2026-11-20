VOWELS = frozenset("аеиоуыэюя")

PERFECTIVE_GERUND_1 = ("в", "вши", "вшись")
PERFECTIVE_GERUND_2 = ("ив", "ивши", "ившись", "ыв", "ывши", "ывшись")
ADJECTIVE = (
    "ее", "ие", "ые", "ое", "ими", "ыми", "ей", "ий", "ый", "ой", "ем", "им", "ым", "ом",
    "его", "ого", "ему", "ому", "их", "ых", "ую", "юю", "ая", "яя", "ою", "ею",
)
PARTICIPLE_1 = ("ем", "нн", "вш", "ющ", "щ")
PARTICIPLE_2 = ("ивш", "ывш", "ующ")
REFLEXIVE = ("ся", "сь")
VERB_1 = ("ла", "на", "ете", "йте", "ли", "й", "л", "ем", "н", "ло", "но", "ет", "ют", "ны", "ть", "ешь", "нно")
VERB_2 = (
    "ила", "ыла", "ена", "ейте", "уйте", "ите", "или", "ыли", "ей", "уй", "ил", "ыл", "им", "ым", "ен",
    "ило", "ыло", "ено", "ят", "ует", "уют", "ит", "ыт", "ены", "ить", "ыть", "ишь", "ую", "ю",
)
NOUN = (
    "а", "ев", "ов", "ие", "ье", "е", "иями", "ями", "ами", "еи", "ии", "и", "ией", "ей", "ой", "ий", "й",
    "иям", "ям", "ием", "ем", "ам", "ом", "о", "у", "ах", "иях", "ях", "ы", "ь", "ию", "ью", "ю", "ия", "ья", "я",
)
SUPERLATIVE = ("ейш", "ейше")
DERIVATIONAL = ("ост", "ость")


def _next_region(word: str, start: int) -> int:
    for i in range(start + 1, len(word)):
        if word[i] not in VOWELS and word[i - 1] in VOWELS:
            return i + 1
    return len(word)


def regions(word: str) -> tuple[int, int, int]:
    rv = len(word)
    for i, ch in enumerate(word):
        if ch in VOWELS:
            rv = i + 1
            break
    r1 = _next_region(word, 0)
    r2 = _next_region(word, r1)
    return rv, r1, r2


def _longest(word: str, limit: int, suffixes) -> str | None:
    best = None
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) >= limit:
            if best is None or len(suffix) > len(best):
                best = suffix
    return best


def _remove(word: str, rv: int, group1, group2) -> str | None:
    best1 = _longest(word, rv, group1)
    best2 = _longest(word, rv, group2)
    if best1 is None and best2 is None:
        return None
    if best2 is not None and (best1 is None or len(best2) >= len(best1)):
        return word[: len(word) - len(best2)]
    pos = len(word) - len(best1)
    if pos - 1 >= rv and word[pos - 1] in "ая":
        return word[:pos]
    return None


def _adjectival(word: str, rv: int) -> str | None:
    stripped = _remove(word, rv, (), ADJECTIVE)
    if stripped is None:
        return None
    without_participle = _remove(stripped, rv, PARTICIPLE_1, PARTICIPLE_2)
    return stripped if without_participle is None else without_participle


def stem(word: str) -> str:
    word = word.lower().replace("ё", "е")
    rv, _r1, r2 = regions(word)
    if rv >= len(word):
        return word

    result = _remove(word, rv, PERFECTIVE_GERUND_1, PERFECTIVE_GERUND_2)
    if result is not None:
        word = result
    else:
        reflexive = _remove(word, rv, (), REFLEXIVE)
        if reflexive is not None:
            word = reflexive
        result = _adjectival(word, rv)
        if result is None:
            result = _remove(word, rv, VERB_1, VERB_2)
        if result is None:
            result = _remove(word, rv, (), NOUN)
        if result is not None:
            word = result

    if word.endswith("и") and len(word) - 1 >= rv:
        word = word[:-1]

    derivational = _longest(word, rv, DERIVATIONAL)
    if derivational is not None and len(word) - len(derivational) >= r2:
        word = word[: len(word) - len(derivational)]

    superlative = _longest(word, rv, SUPERLATIVE)
    if superlative is not None:
        word = word[: len(word) - len(superlative)]
        if word.endswith("нн") and len(word) - 2 >= rv:
            word = word[:-1]
    elif word.endswith("нн") and len(word) - 2 >= rv:
        word = word[:-1]
    elif word.endswith("ь") and len(word) - 1 >= rv:
        word = word[:-1]
    return word
