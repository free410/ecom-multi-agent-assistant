from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool
from app.tools.campaign_tools import generate_campaign_copy


class ContentAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        product_name = state.get("product_name") or "云萃保温咖啡杯"
        campaign_theme = state.get("campaign_theme") or "限时活动"
        audience = state.get("audience") or "目标人群"
        db = state.get("db_session")

        tool_result = generate_campaign_copy(
            product_name=product_name,
            campaign_theme=campaign_theme,
            audience=audience,
            db=db,
        )
        prompt = (
            f"基于以下活动信息，输出更适合电商页面展示的促销文案。\n{tool_result}\n"
            "请提供标题、卖点句和行动号召，语言简洁有转化感。"
        )
        llm_result = llm_client.generate(
            system_prompt="你是资深电商内容运营，擅长活动文案与人群定向表达。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        draft = (
            f"### 活动文案\n"
            f"**标题**：{tool_result.get('headline', '活动文案生成失败')}\n\n"
            f"**核心内容**：\n"
            f"- {' '.join(tool_result.get('bullets', []))}\n"
            f"- {tool_result.get('cta', '')}\n\n"
            f"**AI优化版**：\n{llm_result.text}"
        )
        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"campaign_copy": tool_result},
            "draft_answer": draft,
            "logs": append_log(state, f"ContentAgent 已生成人群定向文案，主题为 {campaign_theme}。"),
            "used_tools": append_tool(state, "generate_campaign_copy"),
            "agent_path": append_path(state, "ContentAgent"),
        }


content_agent = ContentAgent()

