"""Public API contract for the frontend and RAG integration."""
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str | None
    display_name: str
    role: str
    is_guest: bool
    created_at: int
    last_active_at: int


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    display_name: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def valid_display_name(cls, v: str) -> str:
        # Unicode letters, spaces, hyphens and apostrophes, as in interface.md.
        if not re.fullmatch(r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*", v, flags=re.UNICODE):
            raise ValueError("Имя: только буквы, пробелы, дефисы или апострофы")
        return v

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: int
    user: UserPublic


class ChatPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    is_deleted: bool
    created_at: int
    updated_at: int


class MessagePublic(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    sources: list[str]
    recipe: "RecipeCard | None" = None
    created_at: int


class ChatDetail(BaseModel):
    chat: ChatPublic
    messages: list[MessagePublic]


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)

    @field_validator("question")
    @classmethod
    def nonblank_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Напишите вопрос")
        return v


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def nonblank_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Напишите сообщение")
        return v


class RecipeCard(BaseModel):
    """Optional structured data for the recipe card described in docs/Product/interface.md.

    RAG may return just answer/sources during KT2; when recipe details are available,
    the card is saved and returned without changing the HTTP API later.
    """
    title: str = Field(min_length=1)
    image_url: str | None = None
    calories_kcal: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    carbs_g: float | None = Field(default=None, ge=0)
    cooking_time_minutes: int | None = Field(default=None, ge=0)
    ingredients: list[str] = Field(default_factory=list)


class RagAnswer(BaseModel):
    answer: str = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    recipe: RecipeCard | None = None


class MessagePair(BaseModel):
    user_message: MessagePublic
    assistant_message: MessagePublic


class AdminSummary(BaseModel):
    period: str
    total_users: int
    total_users_growth_percent: float | None
    active_users: int
    active_users_change_percent: float | None
    new_chats: int
    new_chats_change_percent: float | None
    messages: int
    messages_change_percent: float | None


class AdminUserRow(UserPublic):
    total_chats: int
    active_chats: int
    total_messages: int
    messages_in_period: int


class AdminUserDetail(BaseModel):
    user: AdminUserRow


class ActivityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    details: str
    created_at: int


class Page(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
