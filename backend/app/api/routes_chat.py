from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session | None = Depends(get_db)) -> ChatResponse:
    try:
        return chat_service.run_chat(payload, db=db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {exc}") from exc

