from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool
from app.tools.competitor_tools import compare_competitors
from app.tools.report_tools import generate_daily_report
from app.tools.review_tools import extract_negative_keywords, summarize_reviews


class AnalysisAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        intent = state["intent"]
        product_name = state.get("product_name") or "云萃保温咖啡杯"
        tool_outputs: dict[str, Any] = {}
        used_tools = list(state.get("used_tools", []))
        db = state.get("db_session")

        if intent == "review_summary":
            tool_outputs["review_summary"] = summarize_reviews(product_name, days=7)
            tool_outputs["negative_keywords"] = extract_negative_keywords(product_name, days=7)
            used_tools = append_tool({"used_tools": used_tools}, "summarize_reviews")
            used_tools = append_tool({"used_tools": used_tools}, "extract_negative_keywords")
            user_prompt = f"请根据评论摘要和差评关键词输出适合运营复盘的结论：{tool_outputs}"
            section_title = "评论摘要"
        elif intent == "competitor_compare":
            tool_outputs["competitor_compare"] = compare_competitors(product_name, db=db)
            used_tools = append_tool({"used_tools": used_tools}, "compare_competitors")
            user_prompt = f"请根据竞品对比结果，输出结构化对比和运营建议：{tool_outputs}"
            section_title = "竞品整理"
        else:
            tool_outputs["daily_report"] = generate_daily_report(state.get("daily_report_context", {}))
            used_tools = append_tool({"used_tools": used_tools}, "generate_daily_report")
            user_prompt = f"请根据日报结构化数据，生成适合汇报的日报总结：{tool_outputs}"
            section_title = "运营日报"

        llm_result = llm_client.generate(
            system_prompt="你是电商分析助手，擅长把评论、竞品和日报数据整理为可执行结论。",
            user_prompt=user_prompt,
            provider=state.get("model_provider"),
        )

        draft = f"### {section_title}\n\n{llm_result.text}\n\n```json\n{tool_outputs}\n```"
        return {
            "provider_used": llm_result.provider,
            "tool_outputs": tool_outputs,
            "draft_answer": draft,
            "logs": append_log(state, f"AnalysisAgent 已完成 {intent} 分析。"),
            "used_tools": used_tools,
            "agent_path": append_path(state, "AnalysisAgent"),
        }


analysis_agent = AnalysisAgent()

