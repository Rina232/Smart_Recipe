"""Opaque bearer sessions (revocable on logout), Argon2id password hashes."""
import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthSession, User, utc_now

password_hasher = PasswordHasher()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(raw: str) -> str:
    return password_hasher.hash(raw)


def verify_password(raw: str, stored: str) -> bool:
    try:
        return password_hasher.verify(stored, raw)
    except (VerifyMismatchError, VerificationError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_session(db: Session, user: User, days: int = 7) -> tuple[str, int]:
    token = secrets.token_urlsafe(32)
    expiry = utc_now() + int(timedelta(days=days).total_seconds())
    db.add(AuthSession(user_id=user.id, token_hash=token_digest(token), expires_at=expiry))
    db.commit()
    return token, expiry


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется вход в приложение",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    record = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(credentials.credentials)))
    if record is None or record.expires_at <= utc_now():
        raise _unauthorized()
    user = db.get(User, record.user_id)
    if user is None:
        raise _unauthorized()
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin" or user.is_guest:
        raise HTTPException(status_code=403, detail="Доступно только администратору")
    return user
