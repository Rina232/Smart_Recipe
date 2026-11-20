import sys
import types

import pytest

from rag.stemmer import stem
from rag.text import Normalizer, simple_tokens


def test_simple_tokens_lowercase_yo_and_punctuation():
    assert simple_tokens("Свёкла, КАРТОФЕЛЬ; по-деревенски! 200 г.") == ["свекла", "картофель", "по", "деревенски", "200", "г"]


@pytest.mark.parametrize("word, expected", [
    ("важная", "важн"),
    ("важнейшие", "важн"),
    ("грибами", "гриб"),
    ("грибы", "гриб"),
    ("курица", "куриц"),
    ("курицей", "куриц"),
    ("курицы", "куриц"),
    ("картофель", "картофел"),
    ("картофеля", "картофел"),
    ("сырники", "сырник"),
    ("сырников", "сырник"),
])
def test_snowball_stemmer_examples(word, expected):
    assert stem(word) == expected


def test_query_and_document_forms_match():
    normalizer = Normalizer("stem")
    assert normalizer.tokens("Курица с грибами") == normalizer.tokens("курицы и грибы")


def test_stopwords_digits_and_short_tokens_removed():
    normalizer = Normalizer("stem")
    assert normalizer.tokens("Что приготовить из 500 г творога?") == ["творог"]


def test_empty_and_punctuation_only():
    normalizer = Normalizer("stem")
    assert normalizer.tokens("") == []
    assert normalizer.tokens("?!.,") == []


def test_normalization_is_deterministic():
    first = Normalizer("stem").tokens("Запечённая треска с овощами")
    second = Normalizer("stem").tokens("Запечённая треска с овощами")
    assert first == second


def test_none_mode_keeps_word_forms():
    assert Normalizer("none").tokens("Грибами грибы") == ["грибами", "грибы"]


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        Normalizer("magic")


def test_pymorphy3_mode_uses_normal_form(monkeypatch):
    class Parse:
        def __init__(self, word):
            self.normal_form = {"грибами": "гриб", "курицы": "курица"}.get(word, word)

    class FakeAnalyzer:
        def parse(self, word):
            return [Parse(word)]

    monkeypatch.setitem(sys.modules, "pymorphy3", types.SimpleNamespace(MorphAnalyzer=FakeAnalyzer))
    normalizer = Normalizer("auto")
    assert normalizer.mode == "pymorphy3"
    assert normalizer.tokens("курицы с грибами") == ["курица", "гриб"]


def test_explicit_pymorphy3_without_package_fails(monkeypatch):
    monkeypatch.setitem(sys.modules, "pymorphy3", None)
    with pytest.raises(RuntimeError):
        Normalizer("pymorphy3")
    assert Normalizer("auto").mode == "stem"
