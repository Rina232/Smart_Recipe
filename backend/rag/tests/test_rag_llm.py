import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from rag.config import LLMSettings, get_llm_settings, load_env_file
from rag.llm import LLMError, LLMNotConfiguredError, chat


class FakeServer:
    def __init__(self, status=200, body=None):
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                outer.requests.append({
                    "path": self.path,
                    "headers": dict(self.headers),
                    "json": json.loads(self.rfile.read(length).decode("utf-8")),
                })
                payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def settings(provider, url, api_key=None):
    return LLMSettings(provider=provider, base_url=url, model="test-model", api_key=api_key, timeout=5,
                       temperature=0.0, seed=42, num_ctx=8192, max_tokens=100)


MESSAGES = [{"role": "system", "content": "s"}, {"role": "user", "content": "Вопрос"}]


def test_ollama_native_api():
    server = FakeServer(body={"message": {"role": "assistant", "content": "Ответ [D01]"}})
    try:
        assert chat(MESSAGES, settings("ollama", server.url)) == "Ответ [D01]"
        request = server.requests[0]
        assert request["path"] == "/api/chat"
        assert request["json"]["stream"] is False
        assert request["json"]["options"]["num_ctx"] == 8192
        assert request["json"]["messages"][1]["content"] == "Вопрос"
    finally:
        server.close()


def test_openai_compatible_api_sends_key_in_header_only():
    server = FakeServer(body={"choices": [{"message": {"role": "assistant", "content": "Ответ"}}]})
    try:
        assert chat(MESSAGES, settings("openai", server.url + "/v1", api_key="secret-key")) == "Ответ"
        request = server.requests[0]
        assert request["path"] == "/v1/chat/completions"
        assert request["headers"]["Authorization"] == "Bearer secret-key"
        assert "secret-key" not in json.dumps(request["json"])
    finally:
        server.close()


def test_http_error_raises_without_leaking_key():
    server = FakeServer(status=500, body={"error": "boom"})
    try:
        with pytest.raises(LLMError) as exc:
            chat(MESSAGES, settings("openai", server.url, api_key="secret-key"))
        assert "500" in str(exc.value) and "secret-key" not in str(exc.value)
    finally:
        server.close()


def test_empty_or_malformed_response_raises():
    server = FakeServer(body={"message": {"content": "  "}})
    try:
        with pytest.raises(LLMError):
            chat(MESSAGES, settings("ollama", server.url))
    finally:
        server.close()
    server = FakeServer(body={"unexpected": True})
    try:
        with pytest.raises(LLMError):
            chat(MESSAGES, settings("ollama", server.url))
    finally:
        server.close()


def test_connection_refused_raises():
    with pytest.raises(LLMError):
        chat(MESSAGES, settings("ollama", "http://127.0.0.1:9"))


def test_not_configured(monkeypatch, tmp_path):
    for name in ("RAG_LLM_PROVIDER", "RAG_LLM_MODEL", "RAG_LLM_BASE_URL", "RAG_LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("rag.config.ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setattr("rag.config.load_env_file", lambda path=None: None)
    current = get_llm_settings()
    assert not current.configured
    with pytest.raises(LLMNotConfiguredError):
        chat(MESSAGES, current)


def test_env_file_does_not_override_real_environment(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("# пример\nRAG_LLM_PROVIDER=ollama\nRAG_LLM_MODEL=\"qwen\"\nexport RAG_LLM_TIMEOUT=30\n", encoding="utf-8")
    monkeypatch.setenv("RAG_LLM_MODEL", "from-env")
    monkeypatch.delenv("RAG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("RAG_LLM_TIMEOUT", raising=False)
    load_env_file(env)
    import os

    assert os.environ["RAG_LLM_PROVIDER"] == "ollama"
    assert os.environ["RAG_LLM_MODEL"] == "from-env"
    assert os.environ["RAG_LLM_TIMEOUT"] == "30"
