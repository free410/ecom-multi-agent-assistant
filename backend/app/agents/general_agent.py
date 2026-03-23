from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path
from app.schemas.agent import GeneralAgentResult


class GeneralAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        message = state["message"]
        subject_name = state.get("subject_name")

        llm_result = llm_client.generate(
            system_prompt=(
                "你是一个友好的电商运营智能助手。"
                "当用户只是打招呼、闲聊或者问你能做什么时，"
                "请先自然回应，再告诉用户你能处理的电商任务。"
            ),
            user_prompt=(
                f"用户输入：{message}\n"
                "请给出简短自然的中文回复，并附带 3 到 4 个可继续提问的方向。"
            ),
            provider=state.get("model_provider"),
            temperature=0.5,
        )

        if subject_name:
            reply = (
                f"{subject_name} 当然可以继续做。"
                f"如果你要的是 {subject_name} 的电商运营内容，我可以直接帮你写文案、提炼卖点、做客服回复，"
                "也可以先帮你拆目标。"
            )
            suggested_prompts = [
                f"帮我写一个{subject_name}的促销文案",
                f"总结{subject_name}的核心卖点",
                f"给我一版{subject_name}的详情页标题",
                f"做一条{subject_name}的客服回复模板",
            ]
        else:
            suggested_prompts = [
                "帮我生成云萃保温咖啡杯的618促销文案",
                "总结云萃保温咖啡杯最近7天差评关键词",
                "针对发货慢生成客服回复建议",
                "整理云萃保温咖啡杯与竞品的差异",
            ]
            reply = llm_result.text.strip() or (
                "你好，我是你的电商运营智能助手。"
                "我可以帮你做商品问答、活动文案、客服回复、评论分析、竞品整理和运营日报。"
            )

        structured_result = GeneralAgentResult(
            user_message=message,
            reply=reply,
            suggested_prompts=suggested_prompts,
        ).model_dump()

        draft_answer = (
            "### 通用对话\n\n"
            f"{reply}\n\n"
            "**你也可以直接这样问我：**\n"
            + "\n".join(f"- {prompt}" for prompt in suggested_prompts)
        )

        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {},
            "tool_details": [],
            "used_tools": [],
            "structured_result": structured_result,
            "draft_answer": draft_answer,
            "logs": append_log(state, "GeneralAgent 已处理通用问候或兜底对话输入。"),
            "agent_path": append_path(state, "GeneralAgent"),
        }


general_agent = GeneralAgent()
