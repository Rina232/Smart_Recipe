"""Chat lists, persistence and message exchange with Katya's RAG."""
import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_security import current_user
from app.database import get_db
from app.helpers import record_activity, serialize_message
from app.models import Chat, Message, User, utc_now
from app.rag_adapter import invoke_rag
from app.schemas import ChatDetail, ChatPublic, MessagePair, MessageRequest, QuestionRequest, RagAnswer

router = APIRouter(tags=["Chats & RAG"])


def owned_chat(db: Session, user: User, chat_id: int) -> Chat:
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != user.id or chat.is_deleted:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat


@router.get("/chats", response_model=list[ChatPublic])
def get_chats(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Chat).where(Chat.user_id == user.id, Chat.is_deleted.is_(False))
        .order_by(Chat.updated_at.desc(), Chat.id.desc())
    ).all()


@router.post("/chats", response_model=ChatPublic, status_code=201)
def new_chat(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Гостю доступен только один чат")
    chat = Chat(user_id=user.id)
    db.add(chat)
    db.flush()
    record_activity(db, user, "create_chat", f"Создан чат №{chat.id}")
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/chats/{chat_id}", response_model=ChatDetail)
def chat_details(chat_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    chat = owned_chat(db, user, chat_id)
    messages = db.scalars(select(Message).where(Message.chat_id == chat_id).order_by(Message.id)).all()
    return ChatDetail(chat=ChatPublic.model_validate(chat), messages=[serialize_message(m) for m in messages])


@router.delete("/chats/{chat_id}", status_code=204)
def delete_chat(chat_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Гостевой чат нельзя удалить")
    chat = owned_chat(db, user, chat_id)
    chat.is_deleted = True  # Keep history for the admin user detail screen.
    chat.updated_at = utc_now()
    record_activity(db, user, "delete_chat", f"Удалён чат №{chat.id}")
    db.commit()
    return Response(status_code=204)


@router.post("/ask", response_model=RagAnswer, response_model_exclude_none=True)
async def ask(
    body: QuestionRequest,
    user: User = Depends(current_user),
):
    """Simple lecture endpoint: does not save anything to chat history."""
    return await invoke_rag(body.question)


@router.post("/chats/{chat_id}/messages", response_model=MessagePair, status_code=201)
async def send_message(
    chat_id: int,
    body: MessageRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    chat = owned_chat(db, user, chat_id)
    # Run the RAG first: if it fails, the database is not polluted with half a dialogue.
    result = await invoke_rag(body.content)
    now = utc_now()
    user_message = Message(chat_id=chat.id, role="user", content=body.content, sources_json="[]", created_at=now)
    assistant_message = Message(
        chat_id=chat.id, role="assistant", content=result.answer,
        sources_json=json.dumps(result.sources, ensure_ascii=False),
        recipe_json=result.recipe.model_dump_json() if result.recipe else None,
        created_at=now,
    )
    db.add_all([user_message, assistant_message])
    if chat.title == "Новый чат":
        chat.title = body.content[:60] + ("…" if len(body.content) > 60 else "")
    chat.updated_at = now
    record_activity(db, user, "send_message", f"Сообщение в чате №{chat.id}")
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return MessagePair(user_message=serialize_message(user_message), assistant_message=serialize_message(assistant_message))
