from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=2)
    message: str = Field(..., min_length=1)
    model_provider: Literal["qwen", "deepseek", "mock"] = "mock"


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    answer: str
    logs: list[str]
    used_tools: list[str]
    agent_path: list[str]
    provider_used: str
    structured_result: dict[str, Any]
    confidence: float
    routing_reason: str
    memory_used: dict[str, bool]
    restored_fields: list[str]
    tool_details: list[dict[str, Any]]


class SessionHistoryResponse(BaseModel):
    session_id: str
    history: list[dict]
    last_result: dict | None = None

