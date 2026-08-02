from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.dependencies import get_current_user
from app.guardrails import screen_user_query
from app.models import User
from app.schemas import ChatRequest, ChatResponse
from app.services.rag_engine import answer_query
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def chat(
    request: Request,  # required by slowapi's rate-limit decorator
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    screen_user_query(payload.query)
    result = await answer_query(db, current_user.id, payload.query, payload.document_ids)
    return result
