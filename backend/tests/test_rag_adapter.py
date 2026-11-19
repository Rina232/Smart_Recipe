"""The adapter supports both sync and async RAG implementations."""
from unittest.mock import patch


def test_bad_rag_result_not_saved(client):
    token = client.post("/auth/guest").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    chat_id = client.get("/chats", headers=headers).json()[0]["id"]
    with patch("app.rag_adapter.answer_question", lambda q: {"answer": "", "sources": []}):
        response = client.post(f"/chats/{chat_id}/messages", headers=headers, json={"content": "Курица"})
        assert response.status_code == 502
    assert client.get(f"/chats/{chat_id}", headers=headers).json()["messages"] == []


def test_async_rag(client):
    async def custom_rag(question):
        return {"answer": f"Ответ для {question}", "sources": ["D01", "D09"]}

    token = client.post("/auth/guest").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.rag_adapter.answer_question", custom_rag):
        result = client.post("/ask", headers=headers, json={"question": "Суп"})
    assert result.status_code == 200
    assert result.json() == {"answer": "Ответ для Суп", "sources": ["D01", "D09"]}


def test_recipe_card_roundtrip(client):
    """Structured recipe details are returned by the API and saved in SQLite."""
    token = client.post("/auth/guest").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    chat_id = client.get("/chats", headers=headers).json()[0]["id"]
    fake = lambda q: {"answer": "Паста с грибами", "sources": ["D01"], "recipe": {
        "title": "Паста с грибами", "cooking_time_minutes": 20,
        "ingredients": ["Паста — 200 г", "Грибы — 150 г"]}}
    with patch("app.rag_adapter.answer_question", fake):
        result = client.post(f"/chats/{chat_id}/messages", headers=headers,
                             json={"content": "Что приготовить?"})
    assert result.status_code == 201, result.text
    card = result.json()["assistant_message"]["recipe"]
    assert card["title"] == "Паста с грибами"
    assert card["ingredients"] == ["Паста — 200 г", "Грибы — 150 г"]
    saved = client.get(f"/chats/{chat_id}", headers=headers).json()["messages"][-1]
    assert saved["recipe"] == card


def test_old_rag_response_without_card_is_compatible(client):
    token = client.post("/auth/guest").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    result = client.post("/ask", headers=headers, json={"question": "Что приготовить?"})
    assert result.status_code == 200
    assert "recipe" not in result.json()
