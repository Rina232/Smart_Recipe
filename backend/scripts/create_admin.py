"""Create or promote a local administrator without a default password.

Run from backend/: python -m scripts.create_admin
"""
import getpass

from sqlalchemy import select

from app.auth_security import hash_password
from app.database import SessionLocal, init_db
from app.models import User
from app.schemas import RegisterRequest


def main():
    init_db()
    print("Создание администратора Smart Recipe")
    username = input("Логин (3–30 символов): ").strip()
    display_name = input("Отображаемое имя: ").strip()
    password = getpass.getpass("Пароль (от 8 символов): ")
    try:
        data = RegisterRequest(username=username, display_name=display_name, password=password)
    except ValueError as exc:
        print(f"Некорректные данные: {exc}")
        raise SystemExit(1) from None
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == data.username))
        if user:
            print("Логин занят. Уже существующую учётную запись нельзя повысить через этот скрипт.")
            raise SystemExit(1)
        user = User(
            username=data.username,
            display_name=data.display_name,
            password_hash=hash_password(data.password),
            role="admin",
            is_guest=False,
        )
        db.add(user)
        db.commit()
    print("Администратор создан. Теперь можно войти через POST /auth/login.")


if __name__ == "__main__":
    main()
