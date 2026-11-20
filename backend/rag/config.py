import os
from dataclasses import dataclass
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
DATA_DIR = RAG_DIR / "data"
DEFAULT_CORPUS_PATH = DATA_DIR / "corpus.json"
DEFAULT_QUESTIONS_PATH = DATA_DIR / "benchmark_questions.json"
DEFAULT_RESULTS_PATH = RAG_DIR / "results" / "benchmark_results.json"
ENV_FILE = RAG_DIR / ".env"

BM25_K1 = 1.2
BM25_B = 0.75
DEFAULT_CONTEXT_TOP_K = 3
DEFAULT_BENCHMARK_K = 5
DEFAULT_MRR_DEPTH = 10
MIN_SCORE = 0.0

REFUSAL_TEXT = "В корпусе рецептов нет достаточной информации для ответа на этот вопрос."

PROVIDERS = ("ollama", "openai")
DEFAULT_OLLAMA_URL = "http://localhost:11434"


def load_env_file(path: Path = ENV_FILE) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_float(name: str, default: float) -> float:
    value = _env(name)
    return default if value is None else float(value)


def _env_int(name: str, default: int | None) -> int | None:
    value = _env(name)
    return default if value is None else int(value)


@dataclass(frozen=True)
class LLMSettings:
    provider: str | None
    base_url: str | None
    model: str | None
    api_key: str | None
    timeout: float
    temperature: float
    seed: int | None
    num_ctx: int
    max_tokens: int

    @property
    def problems(self) -> list[str]:
        found = []
        if self.provider is None:
            found.append("не задан RAG_LLM_PROVIDER (ollama или openai)")
        elif self.provider not in PROVIDERS:
            found.append(f"RAG_LLM_PROVIDER={self.provider!r} не поддерживается, нужен ollama или openai")
        if not self.model:
            found.append("не задан RAG_LLM_MODEL")
        if self.provider == "openai" and not self.base_url:
            found.append("для provider=openai нужен RAG_LLM_BASE_URL")
        return found

    @property
    def configured(self) -> bool:
        return not self.problems

    def public_dict(self) -> dict:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "api_key_set": bool(self.api_key),
            "timeout": self.timeout,
            "temperature": self.temperature,
            "seed": self.seed,
            "num_ctx": self.num_ctx if self.provider == "ollama" else None,
            "max_tokens": self.max_tokens,
        }


def get_llm_settings() -> LLMSettings:
    load_env_file()
    provider = _env("RAG_LLM_PROVIDER")
    provider = provider.lower() if provider else None
    base_url = _env("RAG_LLM_BASE_URL")
    if provider == "ollama" and base_url is None:
        base_url = DEFAULT_OLLAMA_URL
    return LLMSettings(
        provider=provider,
        base_url=base_url,
        model=_env("RAG_LLM_MODEL"),
        api_key=_env("RAG_LLM_API_KEY"),
        timeout=_env_float("RAG_LLM_TIMEOUT", 600.0),
        temperature=_env_float("RAG_LLM_TEMPERATURE", 0.0),
        seed=_env_int("RAG_LLM_SEED", 42 if provider == "ollama" else None),
        num_ctx=_env_int("RAG_LLM_NUM_CTX", 8192),
        max_tokens=_env_int("RAG_LLM_MAX_TOKENS", 800),
    )


def get_normalizer_mode() -> str:
    load_env_file()
    return (_env("RAG_NORMALIZER", "auto") or "auto").lower()


def get_context_top_k() -> int:
    load_env_file()
    value = _env_int("RAG_CONTEXT_TOP_K", DEFAULT_CONTEXT_TOP_K)
    if value is None or value < 1:
        raise ValueError("RAG_CONTEXT_TOP_K должен быть целым числом >= 1")
    return value
