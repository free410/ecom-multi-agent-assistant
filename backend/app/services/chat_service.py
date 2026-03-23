from typing import Any

from sqlalchemy.orm import Session

from app.graph.workflow import workflow_app
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session_service import session_service


class ChatService:
    def run_chat(self, payload: ChatRequest, db: Session | None = None) -> ChatResponse:
        session_service.ensure_session(payload.session_id, payload.message, db=db)
        session_service.append_history(payload.session_id, "user", payload.message, db=db)

        state: dict[str, Any] = {
            "session_id": payload.session_id,
            "message": payload.message,
            "model_provider": payload.model_provider,
            "db_session": db,
            "logs": [],
            "used_tools": [],
            "agent_path": [],
            "tool_outputs": {},
            "tool_details": [],
            "memory_used": {
                "short_term_memory": False,
                "preference_memory": False,
            },
            "restored_fields": [],
        }
        result = workflow_app.invoke(state)

        session_service.append_history(payload.session_id, "assistant", result["answer"], db=db)
        session_service.update_last_intent(payload.session_id, result["intent"], db=db)
        session_service.update_memories(payload.session_id, result, requested_provider=payload.model_provider)

        response_payload = {
            "session_id": payload.session_id,
            "intent": result["intent"],
            "answer": result["answer"],
            "logs": result.get("logs", []),
            "used_tools": result.get("used_tools", []),
            "agent_path": result.get("agent_path", []),
            "provider_used": result.get("provider_used", payload.model_provider),
            "structured_result": result.get("structured_result", {}),
            "confidence": result.get("confidence", 0.0),
            "routing_reason": result.get("routing_reason", ""),
            "memory_used": result.get(
                "memory_used",
                {"short_term_memory": False, "preference_memory": False},
            ),
            "restored_fields": result.get("restored_fields", []),
            "tool_details": result.get("tool_details", []),
        }
        session_service.save_task_log(response_payload, db=db)
        return ChatResponse(**response_payload)


chat_service = ChatService()

