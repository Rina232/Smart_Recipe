"""Existing SQLite database must keep its chats when the optional recipe field is added."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_legacy_messages_table_migrates_without_losing_rows(tmp_path):
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as con:
        con.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY, chat_id INTEGER NOT NULL,
            role VARCHAR(10) NOT NULL, content TEXT NOT NULL,
            sources_json TEXT NOT NULL, created_at INTEGER NOT NULL
        )""")
        con.execute("INSERT INTO messages (id,chat_id,role,content,sources_json,created_at) VALUES (1,1,'user','Тест','[]',1)")
    env = dict(os.environ)
    env["SMART_RECIPE_DATABASE_URL"] = "sqlite:///" + database.as_posix()
    backend_dir = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-c", "from app.database import init_db; init_db()"],
        cwd=backend_dir, env=env, capture_output=True, text=True, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    with sqlite3.connect(database) as con:
        columns = {row[1] for row in con.execute("PRAGMA table_info(messages)")}
        assert "recipe_json" in columns
        assert con.execute("SELECT content FROM messages WHERE id=1").fetchone() == ("Тест",)
