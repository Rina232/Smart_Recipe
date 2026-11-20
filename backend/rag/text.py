import re

from .stemmer import stem

TOKEN_RE = re.compile(r"[a-zа-я0-9]+")

NORMALIZER_MODES = ("auto", "pymorphy3", "stem", "none")

FUNCTION_WORDS = """
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было вот от
меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь опять уж вам
ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без будто чего
раз тоже себе под будет ж тогда кто этот того потому этого какой какая какое какие каких совсем ним здесь этом
почти тем чтобы нее сейчас были куда зачем всех никогда можно при наконец об другой хоть после над больше тот
через эти нас про всего них много разве эту впрочем хорошо этой перед иногда лучше чуть нельзя такой им
более всегда конечно всю между это мой моя мое мои мою свой свою ваш вашей
"""

QUERY_WORDS = """
приготовить приготовлю приготовим готовить сделать сделаю рецепт рецепты рецепта блюдо блюда блюд хочу хочется
хотим подскажите подскажи посоветуйте посоветуй порекомендуйте нужно нужен нужна какую каким
"""

STOPWORDS = frozenset((FUNCTION_WORDS + QUERY_WORDS).split())


def simple_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower().replace("ё", "е"))


class Normalizer:
    def __init__(self, mode: str = "auto"):
        mode = (mode or "auto").lower()
        if mode not in NORMALIZER_MODES:
            raise ValueError(f"Неизвестный режим нормализации {mode!r}, допустимы: {', '.join(NORMALIZER_MODES)}")
        self.requested_mode = mode
        self._morph = None
        if mode in ("auto", "pymorphy3"):
            try:
                import pymorphy3
            except ImportError:
                if mode == "pymorphy3":
                    raise RuntimeError("Режим pymorphy3 выбран, но пакет не установлен: pip install pymorphy3") from None
                mode = "stem"
            else:
                self._morph = pymorphy3.MorphAnalyzer()
                mode = "pymorphy3"
        self.mode = mode
        self._cache: dict[str, str] = {}
        self.stopwords = frozenset(self.normalize_word(w) for w in STOPWORDS)

    def normalize_word(self, word: str) -> str:
        cached = self._cache.get(word)
        if cached is None:
            if self.mode == "pymorphy3":
                cached = self._morph.parse(word)[0].normal_form.replace("ё", "е")
            elif self.mode == "stem":
                cached = stem(word)
            else:
                cached = word
            self._cache[word] = cached
        return cached

    def tokens(self, text: str) -> list[str]:
        result = []
        for word in simple_tokens(text):
            if word.isdigit() or len(word) < 2:
                continue
            term = self.normalize_word(word)
            if len(term) < 2 or term in self.stopwords:
                continue
            result.append(term)
        return result

    def describe(self) -> dict:
        return {
            "requested_mode": self.requested_mode,
            "mode": self.mode,
            "lowercase": True,
            "yo_to_ye": True,
            "token_regex": TOKEN_RE.pattern,
            "drops_numbers": True,
            "min_token_length": 2,
            "stopwords_count": len(STOPWORDS),
        }
