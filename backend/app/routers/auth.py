"""Account creation, login, guest session, logout and /me."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth_security import (
    bearer_scheme, current_user, hash_password, new_session, token_digest, verify_password,
)
from app.database import get_db
from app.helpers import record_activity
from app.models import AuthSession, Chat, User, utc_now
from app.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.username == body.username)) is not None:
        raise HTTPException(status_code=409, detail="Логин уже занят")
    user = User(
        username=body.username,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        role="user",
        is_guest=False,
    )
    db.add(user)
    try:
        db.flush()
        record_activity(db, user, "register", "Регистрация")
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Логин уже занят") from None
    token, expiry = new_session(db, user)
    return AuthResponse(access_token=token, expires_at=expiry, user=UserPublic.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username.lower()))
    if user is None or user.is_guest or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    record_activity(db, user, "login", "Вход в аккаунт")
    db.commit()
    token, expiry = new_session(db, user)
    return AuthResponse(access_token=token, expires_at=expiry, user=UserPublic.model_validate(user))


@router.post("/guest", response_model=AuthResponse, status_code=201)
def guest(db: Session = Depends(get_db)):
    user = User(username=None, display_name="Гость", password_hash=None, role="guest", is_guest=True)
    db.add(user)
    db.flush()
    chat = Chat(user_id=user.id, title="Гостевой чат")
    db.add(chat)
    record_activity(db, user, "guest_login", "Вход в гостевой чат")
    db.commit()
    token, expiry = new_session(db, user, days=30)
    return AuthResponse(access_token=token, expires_at=expiry, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    record = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(credentials.credentials)))
    if record is not None:
        db.delete(record)
    record_activity(db, user, "logout", "Выход из аккаунта")
    db.commit()
    return Response(status_code=204)
