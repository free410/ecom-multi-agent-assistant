from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.core.database as database
from app.core.redis_client import redis_store
from app.models.session import ChatSession
from app.models.task_log import TaskLog


class SessionService:
    def __init__(self) -> None:
        self._memory_sessions: dict[str, dict[str, Any]] = {}
        self._memory_task_logs: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    def ensure_session(self, session_id: str, first_message: str, db: Session | None = None) -> None:
        title = first_message[:30]
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if database.db_available and db is not None:
            record = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
            if record is None:
                db.add(
                    ChatSession(
                        session_id=session_id,
                        title=title or "新会话",
                        history=[],
                        created_at=now,
                        updated_at=now,
                    )
                )
                db.commit()
            return

        self._memory_sessions.setdefault(
            session_id,
            {
                "session_id": session_id,
                "title": title or "新会话",
                "history": [],
                "last_intent": None,
                "updated_at": now.isoformat(),
            },
        )

    def append_history(self, session_id: str, role: str, content: str, db: Session | None = None) -> None:
        history = redis_store.append_message(session_id, role, content)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if database.db_available and db is not None:
            record = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
            if record is None:
                record = ChatSession(session_id=session_id, title=content[:30], history=history)
                db.add(record)
            else:
                record.history = history
                record.updated_at = now
            db.commit()
            return

        session = self._memory_sessions.setdefault(
            session_id,
            {"session_id": session_id, "title": content[:30], "history": [], "last_intent": None},
        )
        session["history"] = history
        session["updated_at"] = now.isoformat()

    def update_last_intent(self, session_id: str, intent: str, db: Session | None = None) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if database.db_available and db is not None:
            record = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
            if record:
                record.last_intent = intent
                record.updated_at = now
                db.commit()
            return

        session = self._memory_sessions.get(session_id)
        if session:
            session["last_intent"] = intent
            session["updated_at"] = now.isoformat()

    def save_task_log(self, payload: dict[str, Any], db: Session | None = None) -> None:
        redis_store.set_last_result(payload["session_id"], payload)
        if database.db_available and db is not None:
            db.add(
                TaskLog(
                    session_id=payload["session_id"],
                    intent=payload["intent"],
                    provider=payload["provider_used"],
                    answer=payload["answer"],
                    used_tools=payload["used_tools"],
                    agent_path=payload["agent_path"],
                    logs=payload["logs"],
                )
            )
            db.commit()
            return

        self._memory_task_logs[payload["session_id"]].append(payload)

    def get_session_detail(self, session_id: str, db: Session | None = None) -> dict[str, Any]:
        history = redis_store.get_history(session_id)
        last_result = redis_store.get_last_result(session_id)

        if database.db_available and db is not None:
            record = db.scalar(select(ChatSession).where(ChatSession.session_id == session_id))
            if record is not None:
                history = record.history or history
        else:
            session = self._memory_sessions.get(session_id)
            if session:
                history = session.get("history", history)

        return {
            "session_id": session_id,
            "history": history,
            "last_result": last_result,
        }

    def list_sessions(self, db: Session | None = None) -> list[dict[str, Any]]:
        if database.db_available and db is not None:
            records = db.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc())).all()
            return [
                {
                    "session_id": item.session_id,
                    "title": item.title,
                    "last_intent": item.last_intent,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
                for item in records
            ]

        sessions = []
        for value in self._memory_sessions.values():
            sessions.append(
                {
                    "session_id": value["session_id"],
                    "title": value.get("title", "新会话"),
                    "last_intent": value.get("last_intent"),
                    "updated_at": value.get("updated_at"),
                }
            )
        return sorted(sessions, key=lambda item: item.get("updated_at") or "", reverse=True)


session_service = SessionService()
