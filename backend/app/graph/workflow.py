from langgraph.graph import END, StateGraph

from app.agents.analysis_agent import analysis_agent
from app.agents.content_agent import content_agent
from app.agents.general_agent import general_agent
from app.agents.intent_agent import intent_agent
from app.agents.product_agent import product_agent
from app.agents.summary_agent import summary_agent
from app.agents.support_agent import support_agent
from app.core.redis_client import redis_store
from app.graph.state import WorkflowState, append_log, append_path
from app.schemas.agent import ClarificationNodeResult


def load_context(state: WorkflowState) -> dict:
    history = redis_store.get_history(state["session_id"])
    short_term_memory = redis_store.get_short_term_memory(state["session_id"])
    preference_memory = redis_store.get_preference_memory(state["session_id"])
    return {
        "history": history,
        "short_term_memory": short_term_memory,
        "preference_memory": preference_memory,
        "memory_used": {
            "short_term_memory": False,
            "preference_memory": False,
        },
        "restored_fields": [],
        "tool_details": [],
        "logs": append_log(
            state,
            (
                f"已加载 {len(history)} 条会话上下文，"
                f"short_term_memory 字段 {len(short_term_memory)} 个，"
                f"preference_memory 字段 {len(preference_memory)} 个。"
            ),
        ),
        "agent_path": append_path(state, "ContextLoader"),
    }


def clarification_node(state: WorkflowState) -> dict:
    question = state.get("clarification_question") or "请补充更具体的信息。"
    structured_result = ClarificationNodeResult(
        question=question,
        missing_fields=state.get("missing_fields", []),
        context_preview={
            "intent": state.get("intent"),
            "subject_name": state.get("subject_name"),
            "restored_fields": state.get("restored_fields", []),
        },
    ).model_dump()

    return {
        "draft_answer": f"### 需要补充信息\n\n{question}",
        "structured_result": structured_result,
        "logs": append_log(state, "ClarificationNode 已触发，等待用户补充关键信息。"),
        "agent_path": append_path(state, "ClarificationNode"),
    }


def route_by_intent(state: WorkflowState) -> str:
    if state.get("needs_clarification"):
        return "clarification_node"

    intent = state["intent"]
    if intent == "general_chat":
        return "general_agent"
    if intent == "product_qa":
        return "product_agent"
    if intent == "campaign_copy":
        return "content_agent"
    if intent == "customer_support":
        return "support_agent"
    return "analysis_agent"


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_context", load_context)
    graph.add_node("intent_agent", intent_agent.run)
    graph.add_node("clarification_node", clarification_node)
    graph.add_node("general_agent", general_agent.run)
    graph.add_node("product_agent", product_agent.run)
    graph.add_node("content_agent", content_agent.run)
    graph.add_node("support_agent", support_agent.run)
    graph.add_node("analysis_agent", analysis_agent.run)
    graph.add_node("summary_agent", summary_agent.run)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "intent_agent")
    graph.add_conditional_edges(
        "intent_agent",
        route_by_intent,
        {
            "clarification_node": "clarification_node",
            "general_agent": "general_agent",
            "product_agent": "product_agent",
            "content_agent": "content_agent",
            "support_agent": "support_agent",
            "analysis_agent": "analysis_agent",
        },
    )
    graph.add_edge("clarification_node", "summary_agent")
    graph.add_edge("general_agent", "summary_agent")
    graph.add_edge("product_agent", "summary_agent")
    graph.add_edge("content_agent", "summary_agent")
    graph.add_edge("support_agent", "summary_agent")
    graph.add_edge("analysis_agent", "summary_agent")
    graph.add_edge("summary_agent", END)
    return graph.compile()


workflow_app = build_workflow()
