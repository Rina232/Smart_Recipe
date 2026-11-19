"""Core API features and access isolation."""
from sqlalchemy import select

from app.auth_security import hash_password
from app.database import get_db
from app.main import app
from app.models import User


def register(client, username="testuser", name="Тестовый Пользователь", password="secret123"):
    r = client.post("/auth/register", json={"username": username, "display_name": name, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_admin(client):
    # Inject an administrator using the isolated test DB; no admin HTTP endpoint exists.
    db = next(app.dependency_overrides[get_db]())
    admin = User(username="admin", display_name="Администратор", password_hash=hash_password("supersecret"), role="admin")
    db.add(admin)
    db.commit()
    db.close()
    r = client.post("/auth/login", json={"username": "admin", "password": "supersecret"})
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_docs(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200


def test_registration_login_logout_permissions(client):
    assert client.get("/chats").status_code == 401
    first = register(client)
    token = first["access_token"]
    assert client.get("/auth/me", headers=headers(token)).json()["username"] == "testuser"
    assert client.post("/auth/register", json={"username": "TESTUSER", "display_name": "Другой Пользователь", "password": "secret123"}).status_code == 409
    assert client.post("/auth/login", json={"username": "testuser", "password": "wrong"}).status_code == 401
    second = client.post("/auth/login", json={"username": "TESTUSER", "password": "secret123"})
    assert second.status_code == 200
    assert client.post("/auth/logout", headers=headers(token)).status_code == 204
    assert client.get("/auth/me", headers=headers(token)).status_code == 401
    assert client.get("/auth/me", headers=headers(second.json()["access_token"])).status_code == 200


def test_guest_one_chat_persists_and_others_forbidden(client):
    guest = client.post("/auth/guest")
    assert guest.status_code == 201, guest.text
    h = headers(guest.json()["access_token"])
    chats = client.get("/chats", headers=h).json()
    assert len(chats) == 1
    chat_id = chats[0]["id"]
    assert client.get("/chats", headers=h).json()[0]["id"] == chat_id
    assert client.post("/chats", headers=h).status_code == 403
    assert client.delete(f"/chats/{chat_id}", headers=h).status_code == 403
    post = client.post(f"/chats/{chat_id}/messages", headers=h, json={"content": "Ищу рецепт"})
    assert post.status_code == 201, post.text
    assert "ЗАГЛУШКА" in post.json()["assistant_message"]["content"]
    assert len(client.get(f"/chats/{chat_id}", headers=h).json()["messages"]) == 2


def test_chats_messages_ask_and_deletion(client):
    user1 = register(client)
    user2 = register(client, username="another", name="Другой Человек")
    a, b = headers(user1["access_token"]), headers(user2["access_token"])
    r = client.post("/chats", headers=a)
    assert r.status_code == 201
    chat_id = r.json()["id"]
    assert client.get(f"/chats/{chat_id}", headers=b).status_code == 404
    assert client.post(f"/chats/{chat_id}/messages", headers=b, json={"content": "Секрет"}).status_code == 404
    assert client.post("/ask", headers=a, json={"question": "  "}).status_code == 422
    assert client.post("/ask", headers=a, json={"question": "Грибы"}).json()["sources"] == []
    assert client.get(f"/chats/{chat_id}", headers=a).json()["messages"] == []
    messages = client.post(f"/chats/{chat_id}/messages", headers=a, json={"content": "  Паста с грибами   "})
    assert messages.status_code == 201, messages.text
    assert messages.json()["user_message"]["content"] == "Паста с грибами"
    assert client.get("/chats", headers=a).json()[0]["title"] == "Паста с грибами"
    assert client.delete(f"/chats/{chat_id}", headers=a).status_code == 204
    assert client.get(f"/chats/{chat_id}", headers=a).status_code == 404
    assert client.get("/chats", headers=a).json() == []


def test_admin_dashboard_users_periods_and_no_access_for_regular(client):
    regular = register(client)
    h = headers(regular["access_token"])
    assert client.get("/admin/summary", headers=h).status_code == 403
    admin = create_admin(client)
    admin_h = headers(admin["access_token"])
    summary = client.get("/admin/summary?period=7d", headers=admin_h)
    assert summary.status_code == 200, summary.text
    assert summary.json()["total_users"] == 2
    assert summary.json()["active_users"] == 2
    assert client.get("/admin/summary?period=bad", headers=admin_h).status_code == 422
    res = client.get("/admin/users?sort_by=created_at&order=desc&page_size=1", headers=admin_h)
    assert res.status_code == 200, res.text
    assert res.json()["total"] == 2
    assert res.json()["total_pages"] == 2
    uid = regular["user"]["id"]
    assert client.get(f"/admin/users/{uid}", headers=admin_h).json()["user"]["username"] == "testuser"
    assert client.get(f"/admin/users/{uid}/chats", headers=admin_h).status_code == 200
    assert client.get(f"/admin/users/{uid}/activities", headers=admin_h).json()["total"] >= 1
    assert client.get("/admin/users?sort_by=password_hash", headers=admin_h).status_code == 422


def test_validation(client):
    r = client.post("/auth/register", json={"username": "x", "display_name": "Нормальный", "password": "12345678"})
    assert r.status_code == 422
    r = client.post("/auth/register", json={"username": "validuser", "display_name": "A_!", "password": "12345678"})
    assert r.status_code == 422
