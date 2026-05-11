from pydantic import BaseModel, Field

from app.db.enums import ChatChannel


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    tenant_slug: str = Field(default="demo", min_length=1, max_length=64)
    session_id: str | None = Field(default=None, max_length=128)
    channel: ChatChannel = ChatChannel.WIDGET
    external_user_id: str | None = Field(default=None, max_length=255)


class ChatMessageResponse(BaseModel):
    session_id: str
    answer: str
    tenant_slug: str
