from langgraph.graph import END, StateGraph

from app.agents.analysis_agent import analysis_agent
from app.agents.content_agent import content_agent
from app.agents.intent_agent import intent_agent
from app.agents.product_agent import product_agent
from app.agents.summary_agent import summary_agent
from app.agents.support_agent import support_agent
from app.core.redis_client import redis_store
from app.graph.state import WorkflowState, append_log, append_path


def load_context(state: WorkflowState) -> dict:
    history = redis_store.get_history(state["session_id"])
    return {
        "history": history,
        "logs": append_log(state, f"已加载 {len(history)} 条会话上下文。"),
        "agent_path": append_path(state, "ContextLoader"),
    }


def route_by_intent(state: WorkflowState) -> str:
    intent = state["intent"]
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
            "product_agent": "product_agent",
            "content_agent": "content_agent",
            "support_agent": "support_agent",
            "analysis_agent": "analysis_agent",
        },
    )
    graph.add_edge("product_agent", "summary_agent")
    graph.add_edge("content_agent", "summary_agent")
    graph.add_edge("support_agent", "summary_agent")
    graph.add_edge("analysis_agent", "summary_agent")
    graph.add_edge("summary_agent", END)
    return graph.compile()


workflow_app = build_workflow()

