from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool
from app.tools.support_tools import build_customer_reply


class SupportAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        product_name = state.get("product_name") or "云萃保温咖啡杯"
        db = state.get("db_session")
        tool_result = build_customer_reply(product_name, state["message"], db=db)

        prompt = (
            f"请基于以下客服建议结果，润色成一条自然、专业、安抚情绪的客服回复。\n{tool_result}"
        )
        llm_result = llm_client.generate(
            system_prompt="你是电商客服支持助手，擅长在解释规则时兼顾安抚情绪和转化。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        draft = (
            f"### 客服回复建议\n"
            f"**建议回复**：{tool_result.get('reply', '暂无')}\n\n"
            f"**AI润色版**：{llm_result.text}"
        )
        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"customer_reply": tool_result},
            "draft_answer": draft,
            "logs": append_log(state, "SupportAgent 已生成客服辅助回复。"),
            "used_tools": append_tool(state, "build_customer_reply"),
            "agent_path": append_path(state, "SupportAgent"),
        }


support_agent = SupportAgent()

