from typing import Any, Literal, TypedDict


IntentType = Literal[
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
    intent: IntentType
    product_name: str | None
    campaign_theme: str | None
    audience: str | None
    daily_report_context: dict[str, Any]
    tool_outputs: dict[str, Any]
    logs: list[str]
    used_tools: list[str]
    agent_path: list[str]
    draft_answer: str
    answer: str


def append_log(state: WorkflowState, message: str) -> list[str]:
    logs = list(state.get("logs", []))
    logs.append(message)
    return logs


def append_path(state: WorkflowState, node_name: str) -> list[str]:
    path = list(state.get("agent_path", []))
    path.append(node_name)
    return path


def append_tool(state: WorkflowState, tool_name: str) -> list[str]:
    tools = list(state.get("used_tools", []))
    if tool_name not in tools:
        tools.append(tool_name)
    return tools

