from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool, append_tool_detail
from app.schemas.agent import SupportAgentResult, ToolExecutionDetail
from app.tools.support_tools import build_customer_reply


class SupportAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        subject_name = state.get("product_name") or state.get("subject_name") or "云萃保温咖啡杯"
        db = state.get("db_session")
        tool_result = build_customer_reply(subject_name, state["message"], db=db)

        prompt = (
            "请基于以下客服建议结果，润色成一条自然、专业、安抚情绪的客服回复。\n"
            f"{tool_result}"
        )
        llm_result = llm_client.generate(
            system_prompt="你是电商客服支持助手，擅长在解释规则时兼顾安抚情绪和转化。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        structured_result = SupportAgentResult(
            product_name=tool_result.get("product_name", subject_name),
            user_question=tool_result.get("user_question", state["message"]),
            faq_hit=bool(tool_result.get("faq_hit")),
            suggested_reply=tool_result.get("reply", ""),
            polished_reply=llm_result.text,
        ).model_dump()

        draft = (
            "### 客服回复建议\n"
            f"**建议回复**：{structured_result['suggested_reply']}\n\n"
            f"**AI润色版**：{structured_result['polished_reply']}"
        )

        tool_details = append_tool_detail(
            state,
            ToolExecutionDetail(
                tool_name="build_customer_reply",
                purpose="根据商品信息、售后规则和用户问题生成客服回复建议",
                tool_input={"product_name": subject_name, "user_question": state["message"]},
                tool_output=tool_result,
            ).model_dump(),
        )

        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"customer_reply": tool_result},
            "tool_details": tool_details,
            "used_tools": append_tool(state, "build_customer_reply"),
            "structured_result": structured_result,
            "draft_answer": draft,
            "logs": append_log(state, "SupportAgent 已生成客服辅助回复。"),
            "agent_path": append_path(state, "SupportAgent"),
        }


support_agent = SupportAgent()
