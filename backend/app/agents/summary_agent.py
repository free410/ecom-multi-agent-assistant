from typing import Any

from app.graph.state import WorkflowState, append_log, append_path
from app.schemas.agent import SummaryAgentResult


class SummaryAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        confidence = round(float(state.get("confidence", 0.0)), 2)
        routing_reason = state.get("routing_reason", "未提供路由说明")
        memory_used = state.get(
            "memory_used",
            {"short_term_memory": False, "preference_memory": False},
        )

        intro = (
            f"意图：`{state.get('intent', 'unknown')}`  \n"
            f"置信度：`{confidence}`  \n"
            f"模型：`{state.get('provider_used', state.get('model_provider', 'mock'))}`  \n"
            f"路由原因：{routing_reason}  \n"
            f"执行链路：`{' -> '.join(state.get('agent_path', []))}`  \n"
            f"记忆使用：`short_term={memory_used.get('short_term_memory', False)}, "
            f"preference={memory_used.get('preference_memory', False)}`\n\n"
        )
        answer = intro + state.get("draft_answer", "暂无输出。")

        summary_structured = SummaryAgentResult(
            title=f"{state.get('intent', 'unknown')} 结果汇总",
            answer_markdown=answer,
            next_action="如需继续，可直接基于当前会话追问，系统会优先恢复短期上下文。",
            metadata={
                "intent": state.get("intent"),
                "confidence": confidence,
                "routing_reason": routing_reason,
            },
        ).model_dump()

        return {
            "answer": answer,
            "summary_result": summary_structured,
            "logs": append_log(state, "SummaryAgent 已整理最终输出。"),
            "agent_path": append_path(state, "SummaryAgent"),
        }


summary_agent = SummaryAgent()

