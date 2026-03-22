from typing import Any

from app.graph.state import WorkflowState, append_log, append_path


class SummaryAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        intro = (
            f"意图：`{state.get('intent', 'unknown')}`  \n"
            f"模型：`{state.get('provider_used', state.get('model_provider', 'mock'))}`  \n"
            f"执行链路：`{' -> '.join(state.get('agent_path', []))}`\n\n"
        )
        answer = intro + state.get("draft_answer", "暂无输出。")
        return {
            "answer": answer,
            "logs": append_log(state, "SummaryAgent 已整理最终输出。"),
            "agent_path": append_path(state, "SummaryAgent"),
        }


summary_agent = SummaryAgent()

