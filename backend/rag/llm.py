import json
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .config import LLMSettings, get_llm_settings

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class LLMError(RuntimeError):
    pass


class LLMNotConfiguredError(LLMError):
    pass


def _endpoint(settings: LLMSettings) -> str:
    base = settings.base_url.rstrip("/")
    if settings.provider == "ollama":
        return base + "/api/chat"
    return base + "/chat/completions"


def _payload(settings: LLMSettings, messages: list[dict]) -> dict:
    if settings.provider == "ollama":
        options = {"temperature": settings.temperature, "num_ctx": settings.num_ctx, "num_predict": settings.max_tokens}
        if settings.seed is not None:
            options["seed"] = settings.seed
        return {"model": settings.model, "messages": messages, "stream": False, "options": options}
    payload = {
        "model": settings.model,
        "messages": messages,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }
    if settings.seed is not None:
        payload["seed"] = settings.seed
    return payload


def _extract_text(settings: LLMSettings, data: object) -> str:
    try:
        if settings.provider == "ollama":
            content = data["message"]["content"]
        else:
            content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LLMError("Ответ LLM имеет неожиданную структуру") from None
    if not isinstance(content, str) or not content.strip():
        raise LLMError("LLM вернула пустой ответ")
    return content


def _open(request: urllib.request.Request, url: str, timeout: float):
    if urlparse(url).hostname in LOCAL_HOSTS:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        return opener.open(request, timeout=timeout)
    return urllib.request.urlopen(request, timeout=timeout)


def chat(messages: list[dict], settings: LLMSettings | None = None) -> str:
    settings = settings or get_llm_settings()
    if not settings.configured:
        raise LLMNotConfiguredError("LLM не настроена: " + "; ".join(settings.problems))
    url = _endpoint(settings)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    body = json.dumps(_payload(settings, messages), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with _open(request, url, settings.timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:300].decode("utf-8", errors="replace").strip()
        raise LLMError(f"LLM ответила HTTP {exc.code} ({url}): {detail}") from None
    except urllib.error.URLError as exc:
        raise LLMError(f"Нет соединения с LLM по адресу {url}: {exc.reason}") from None
    except (TimeoutError, OSError) as exc:
        raise LLMError(f"Ошибка соединения с LLM по адресу {url}: {exc}") from None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise LLMError("LLM вернула не JSON") from None
    return _extract_text(settings, data)
