"""Read-only admin dashboard, user lists and per-user activity."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth_security import admin_user
from app.database import get_db
from app.helpers import paginate
from app.models import Activity, Chat, Message, User, utc_now
from app.schemas import ActivityPublic, AdminSummary, AdminUserDetail, AdminUserRow, ChatPublic, UserPublic

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(admin_user)])
Period = Literal["1d", "3d", "7d", "1m"]
PERIOD_SECONDS = {"1d": 86400, "3d": 259200, "7d": 604800, "1m": 2592000}


def percent_change(value: int, prior: int) -> float | None:
    if prior == 0:
        return 0.0 if value == 0 else None
    return round((value - prior) / prior * 100, 1)


def count_users(db: Session, start: int | None = None, end: int | None = None) -> int:
    query = select(func.count()).select_from(User).where(User.is_guest.is_(False))
    if start is not None:
        query = query.where(User.created_at >= start)
    if end is not None:
        query = query.where(User.created_at < end)
    return db.scalar(query) or 0


def count_active_users(db: Session, start: int, end: int) -> int:
    query = (
        select(func.count(func.distinct(Activity.user_id)))
        .select_from(Activity)
        .join(User, User.id == Activity.user_id)
        .where(User.is_guest.is_(False), Activity.created_at >= start, Activity.created_at < end)
    )
    return db.scalar(query) or 0


def count_chats(db: Session, start: int, end: int) -> int:
    query = (
        select(func.count()).select_from(Chat)
        .join(User, User.id == Chat.user_id)
        .where(User.is_guest.is_(False), Chat.created_at >= start, Chat.created_at < end)
    )
    return db.scalar(query) or 0


def count_messages(db: Session, start: int, end: int) -> int:
    query = (
        select(func.count()).select_from(Message)
        .join(Chat, Chat.id == Message.chat_id)
        .join(User, User.id == Chat.user_id)
        .where(User.is_guest.is_(False), Message.created_at >= start, Message.created_at < end)
    )
    return db.scalar(query) or 0


@router.get("/summary", response_model=AdminSummary)
def summary(period: Period = "7d", db: Session = Depends(get_db)):
    now = utc_now() + 1  # inclusive of activities created during this second
    secs = PERIOD_SECONDS[period]
    since, previous = now - secs, now - 2 * secs
    total = count_users(db)
    created_recently = count_users(db, since, now)
    previous_total = total - created_recently
    active = count_active_users(db, since, now)
    previous_active = count_active_users(db, previous, since)
    new_chats = count_chats(db, since, now)
    previous_chats = count_chats(db, previous, since)
    messages = count_messages(db, since, now)
    previous_messages = count_messages(db, previous, since)
    return AdminSummary(
        period=period,
        total_users=total,
        total_users_growth_percent=percent_change(total, previous_total),
        active_users=active,
        active_users_change_percent=percent_change(active, previous_active),
        new_chats=new_chats,
        new_chats_change_percent=percent_change(new_chats, previous_chats),
        messages=messages,
        messages_change_percent=percent_change(messages, previous_messages),
    )


def user_metrics(db: Session, user: User, period: Period = "7d") -> AdminUserRow:
    all_chat_ids = select(Chat.id).where(Chat.user_id == user.id)
    total_chats = db.scalar(select(func.count()).select_from(Chat).where(Chat.user_id == user.id)) or 0
    active_chats = db.scalar(
        select(func.count()).select_from(Chat).where(Chat.user_id == user.id, Chat.is_deleted.is_(False))
    ) or 0
    total_messages = db.scalar(
        select(func.count()).select_from(Message).where(Message.chat_id.in_(all_chat_ids))
    ) or 0
    since = utc_now() + 1 - PERIOD_SECONDS[period]
    in_period = db.scalar(
        select(func.count()).select_from(Message)
        .where(Message.chat_id.in_(all_chat_ids), Message.created_at >= since)
    ) or 0
    return AdminUserRow(
        **UserPublic.model_validate(user).model_dump(),
        total_chats=total_chats,
        active_chats=active_chats,
        total_messages=total_messages,
        messages_in_period=in_period,
    )


@router.get("/users")
def users(
    search: str = Query(default="", max_length=100),
    message_period: Period = "7d",
    sort_by: Literal[
        "display_name", "created_at", "last_active_at", "total_chats", "active_chats",
        "total_messages", "messages_in_period"
    ] = "display_name",
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Simple in-memory sorting is deliberate for this educational prototype.
    users_all = db.scalars(select(User).where(User.is_guest.is_(False))).all()
    query = search.casefold().strip()
    rows = [
        user_metrics(db, u, message_period)
        for u in users_all
        if query in u.display_name.casefold() or (u.username and query in u.username.casefold())
    ]
    rows.sort(key=lambda r: getattr(r, sort_by).casefold() if sort_by == "display_name" else getattr(r, sort_by), reverse=order == "desc")
    return paginate([r.model_dump() for r in rows], page, page_size)


def registered_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.is_guest:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def user_detail(user_id: int, db: Session = Depends(get_db)):
    user = registered_user(db, user_id)
    return AdminUserDetail(user=user_metrics(db, user))


@router.get("/users/{user_id}/chats")
def user_chats(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    registered_user(db, user_id)
    rows = db.scalars(
        select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc(), Chat.id.desc())
    ).all()
    return paginate([ChatPublic.model_validate(x).model_dump() for x in rows], page, page_size)


@router.get("/users/{user_id}/activities")
def user_activities(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    registered_user(db, user_id)
    rows = db.scalars(
        select(Activity).where(Activity.user_id == user_id).order_by(Activity.created_at.desc(), Activity.id.desc())
    ).all()
    return paginate([ActivityPublic.model_validate(x).model_dump() for x in rows], page, page_size)
