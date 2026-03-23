import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

import app.core.database as database
from app.core.redis_client import redis_store
from app.models.session import ChatSession
from app.models.task_log import TaskLog


logger = logging.getLogger(__name__)


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

    def update_memories(
        self,
        session_id: str,
        result: dict[str, Any],
        requested_provider: str,
    ) -> None:
        current_short_term = redis_store.get_short_term_memory(session_id)
        current_preference = redis_store.get_preference_memory(session_id)

        current_short_term.update(
            {
                "recent_product_name": result.get("product_name"),
                "recent_subject_name": result.get("subject_name") or result.get("product_name"),
                "recent_intent": result.get("intent"),
                "recent_campaign_theme": result.get("campaign_theme"),
                "recent_audience": result.get("audience"),
            }
        )

        if result.get("needs_clarification"):
            current_short_term["pending_task"] = {
                "intent": result.get("intent"),
                "missing_fields": result.get("missing_fields", []),
                "product_name": result.get("product_name"),
                "subject_name": result.get("subject_name"),
                "campaign_theme": result.get("campaign_theme"),
                "audience": result.get("audience"),
                "routing_reason": result.get("routing_reason"),
            }
        else:
            current_short_term.pop("pending_task", None)

        current_preference.update(
            {
                "preferred_provider": requested_provider,
                "preferred_audience": result.get("audience") or current_preference.get("preferred_audience"),
            }
        )

        redis_store.set_short_term_memory(session_id, current_short_term)
        redis_store.set_preference_memory(session_id, current_preference)

    def save_task_log(self, payload: dict[str, Any], db: Session | None = None) -> None:
        redis_store.set_last_result(payload["session_id"], payload)

        log_record = self._build_task_log_record(payload)
        if database.db_available and db is not None:
            try:
                db.add(log_record)
                db.commit()
                return
            except Exception as exc:
                db.rollback()
                logger.warning("Failed to persist task log to database, falling back to memory mode: %s", exc)

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

    def delete_session(self, session_id: str, db: Session | None = None) -> None:
        redis_store.delete_session_data(session_id)

        if database.db_available and db is not None:
            db.execute(delete(TaskLog).where(TaskLog.session_id == session_id))
            db.execute(delete(ChatSession).where(ChatSession.session_id == session_id))
            db.commit()
        else:
            self._memory_sessions.pop(session_id, None)
            self._memory_task_logs.pop(session_id, None)

    @staticmethod
    def _build_task_log_record(payload: dict[str, Any]) -> TaskLog:
        tool_details = payload.get("tool_details", [])
        primary_tool = ""
        duration_ms = 0
        error_message = None

        if tool_details:
            primary_tool = tool_details[-1].get("tool_name", "")
            for detail in tool_details:
                duration_ms += SessionService._extract_latency(detail)
                if error_message is None:
                    error_message = SessionService._extract_error(detail)

        status = "success" if error_message is None else "error"
        agent_name = SessionService._resolve_agent_name(payload.get("agent_path", []))

        return TaskLog(
            session_id=payload["session_id"],
            intent=payload["intent"],
            provider=payload["provider_used"],
            agent_name=agent_name,
            tool_name=primary_tool or None,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            answer=payload["answer"],
            used_tools=payload["used_tools"],
            agent_path=payload["agent_path"],
            logs=payload["logs"],
        )

    @staticmethod
    def _resolve_agent_name(agent_path: list[str]) -> str:
        for node_name in reversed(agent_path):
            if "Agent" in node_name:
                return node_name
        return agent_path[-1] if agent_path else "unknown"

    @staticmethod
    def _extract_latency(detail: dict[str, Any]) -> int:
        if isinstance(detail.get("latency_ms"), int):
            return detail["latency_ms"]
        tool_output = detail.get("tool_output")
        if isinstance(tool_output, dict):
            latency = tool_output.get("latency_ms")
            if isinstance(latency, int):
                return latency
        return 0

    @staticmethod
    def _extract_error(detail: dict[str, Any]) -> str | None:
        if detail.get("error"):
            return str(detail["error"])
        tool_output = detail.get("tool_output")
        if isinstance(tool_output, dict) and tool_output.get("error"):
            return str(tool_output["error"])
        return None


session_service = SessionService()
