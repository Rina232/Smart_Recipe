"""Fresh SQLite DB per test. All tables and all sessions are isolated."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.database import Base, get_db
from app.main import app
from app import models  # noqa: F401


@pytest.fixture(autouse=True)
def fake_rag_for_tests():
    """API tests must NEVER contact a real LLM or depend on Katya's corpus."""
    with patch("app.rag_adapter.answer_question", lambda question: {
        "answer": "[ЗАГЛУШКА RAG] Тестовый ответ", "sources": []
    }):
        yield


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def enable_fks(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def test_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
