from fastapi import APIRouter, HTTPException

from app.core.dependencies import DBSession
from app.modules.chat.memory import InMemoryStore
from app.modules.chat.schemas import ChatMessageRequest, ChatMessageResponse
from app.modules.chat.service import ChatService, TenantNotFoundError

router = APIRouter()
_chat_service = ChatService(InMemoryStore())


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest, session: DBSession) -> ChatMessageResponse:
    try:
        return await _chat_service.handle_message(session=session, request=request)
    except TenantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
