from typing import Any, Literal, TypedDict


IntentType = Literal[
    "general_chat",
    "product_qa",
    "campaign_copy",
    "customer_support",
    "review_summary",
    "competitor_compare",
    "daily_report",
]


class WorkflowState(TypedDict, total=False):
    session_id: str
    message: str
    model_provider: str
    provider_used: str
    db_session: Any
    history: list[dict[str, str]]
    short_term_memory: dict[str, Any]
    preference_memory: dict[str, Any]
    intent: IntentType
    confidence: float
    routing_reason: str
    needs_clarification: bool
    clarification_question: str | None
    missing_fields: list[str]
    memory_used: dict[str, bool]
    restored_fields: list[str]
    product_name: str | None
    subject_name: str | None
    subject_type: str | None
    campaign_theme: str | None
    audience: str | None
    daily_report_context: dict[str, Any]
    tool_outputs: dict[str, Any]
    tool_details: list[dict[str, Any]]
    structured_result: dict[str, Any]
    logs: list[str]
    used_tools: list[str]
    agent_path: list[str]
    draft_answer: str
    answer: str


def append_log(state: WorkflowState | dict[str, Any], message: str) -> list[str]:
    logs = list(state.get("logs", []))
    logs.append(message)
    return logs


def append_path(state: WorkflowState | dict[str, Any], node_name: str) -> list[str]:
    path = list(state.get("agent_path", []))
    path.append(node_name)
    return path


def append_tool(state: WorkflowState | dict[str, Any], tool_name: str) -> list[str]:
    tools = list(state.get("used_tools", []))
    if tool_name not in tools:
        tools.append(tool_name)
    return tools


def append_tool_detail(
    state: WorkflowState | dict[str, Any],
    detail: dict[str, Any],
) -> list[dict[str, Any]]:
    details = list(state.get("tool_details", []))
    details.append(detail)
    return details


def mark_memory_usage(
    state: WorkflowState | dict[str, Any],
    memory_key: Literal["short_term_memory", "preference_memory"],
) -> dict[str, bool]:
    usage = {
        "short_term_memory": False,
        "preference_memory": False,
        **dict(state.get("memory_used", {})),
    }
    usage[memory_key] = True
    return usage


def append_restored_field(state: WorkflowState | dict[str, Any], field_name: str) -> list[str]:
    restored_fields = list(state.get("restored_fields", []))
    if field_name not in restored_fields:
        restored_fields.append(field_name)
    return restored_fields
