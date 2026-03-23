from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool, append_tool_detail
from app.schemas.agent import ContentAgentResult, ToolExecutionDetail
from app.tools.campaign_tools import generate_campaign_copy


class ContentAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        subject_name = state.get("product_name") or state.get("subject_name") or "云萃保温咖啡杯"
        campaign_theme = state.get("campaign_theme") or "限时活动"
        audience = state.get("audience") or "目标人群"
        db = state.get("db_session")

        tool_result = generate_campaign_copy(
            product_name=subject_name,
            campaign_theme=campaign_theme,
            audience=audience,
            db=db,
        )

        prompt = (
            "基于以下活动信息，输出更适合电商页面展示的促销文案。"
            "请提供标题、卖点句和行动号召，语言简洁有转化感。\n"
            f"{tool_result}"
        )
        llm_result = llm_client.generate(
            system_prompt="你是资深电商内容运营，擅长活动文案与人群定向表达。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        structured_result = ContentAgentResult(
            product_name=tool_result.get("product_name", subject_name),
            campaign_theme=tool_result.get("campaign_theme", campaign_theme),
            audience=tool_result.get("audience", audience),
            headline=tool_result.get("headline", ""),
            bullets=tool_result.get("bullets", []),
            cta=tool_result.get("cta", ""),
            optimized_copy=llm_result.text,
        ).model_dump()

        draft = (
            "### 活动文案\n"
            f"**标题**：{structured_result['headline']}\n\n"
            "**核心内容**：\n"
            f"- {' '.join(structured_result['bullets'])}\n"
            f"- {structured_result['cta']}\n\n"
            f"**AI优化版**：\n{structured_result['optimized_copy']}"
        )

        tool_details = append_tool_detail(
            state,
            ToolExecutionDetail(
                tool_name="generate_campaign_copy",
                purpose="根据商品卖点、活动主题和目标人群生成促销文案底稿",
                tool_input={
                    "product_name": subject_name,
                    "campaign_theme": campaign_theme,
                    "audience": audience,
                },
                tool_output=tool_result,
            ).model_dump(),
        )

        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"campaign_copy": tool_result},
            "tool_details": tool_details,
            "used_tools": append_tool(state, "generate_campaign_copy"),
            "structured_result": structured_result,
            "draft_answer": draft,
            "logs": append_log(state, f"ContentAgent 已生成人群定向文案，主题为 {campaign_theme}。"),
            "agent_path": append_path(state, "ContentAgent"),
        }


content_agent = ContentAgent()
