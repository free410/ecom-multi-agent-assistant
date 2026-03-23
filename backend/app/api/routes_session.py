from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import APIMessage
from app.schemas.chat import SessionHistoryResponse
from app.services.session_service import session_service


router = APIRouter(prefix="/api", tags=["session"])


@router.get("/session/{session_id}", response_model=SessionHistoryResponse)
def get_session(session_id: str, db: Session | None = Depends(get_db)) -> SessionHistoryResponse:
    payload = session_service.get_session_detail(session_id, db=db)
    return SessionHistoryResponse(**payload)


@router.get("/sessions")
def list_sessions(db: Session | None = Depends(get_db)) -> list[dict]:
    return session_service.list_sessions(db=db)


@router.delete("/session/{session_id}", response_model=APIMessage)
def delete_session(session_id: str, db: Session | None = Depends(get_db)) -> APIMessage:
    session_service.delete_session(session_id, db=db)
    return APIMessage(message="会话已删除")
