"""SQLite database and a SQLAlchemy session per HTTP request."""
import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BACKEND_DIR / "data" / "smart_recipe.db"
DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("SMART_RECIPE_DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_fk_on(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as session:
        yield session


def init_db():
    # Import here so SQLAlchemy knows all of the models.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Forward-compatible, additive SQLite migration for databases created by the
    # earlier backend. This preserves existing users, chats, and message history.
    if engine.dialect.name == "sqlite":
        with engine.begin() as connection:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(messages)")}
            if "recipe_json" not in columns:
                connection.exec_driver_sql("ALTER TABLE messages ADD COLUMN recipe_json TEXT")
