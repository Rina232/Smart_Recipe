"""Small helpers used by multiple routers."""
import json
import math

from app.models import Activity, Message, User, utc_now
from app.schemas import MessagePublic


def record_activity(db, user: User, action: str, details: str = "") -> None:
    timestamp = utc_now()
    user.last_active_at = timestamp
    db.add(Activity(user_id=user.id, action=action, details=details[:200], created_at=timestamp))


def serialize_message(message: Message) -> MessagePublic:
    return MessagePublic(
        id=message.id,
        role=message.role,
        content=message.content,
        sources=json.loads(message.sources_json),
        recipe=json.loads(message.recipe_json) if message.recipe_json else None,
        created_at=message.created_at,
    )


def paginate(items, page: int, page_size: int) -> dict:
    total = len(items)
    start = (page - 1) * page_size
    return {
        "items": items[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size),
    }
