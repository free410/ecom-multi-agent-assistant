from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool, append_tool_detail
from app.schemas.agent import AnalysisAgentResult, ToolExecutionDetail
from app.tools.competitor_tools import compare_competitors
from app.tools.report_tools import generate_daily_report
from app.tools.review_tools import extract_negative_keywords, summarize_reviews


class AnalysisAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        intent = state["intent"]
        product_name = state.get("product_name") or "云萃保温咖啡杯"
        tool_outputs: dict[str, Any] = {}
        used_tools = list(state.get("used_tools", []))
        tool_details = list(state.get("tool_details", []))
        db = state.get("db_session")

        if intent == "review_summary":
            review_summary = summarize_reviews(product_name, days=7)
            negative_keywords = extract_negative_keywords(product_name, days=7)
            tool_outputs["review_summary"] = review_summary
            tool_outputs["negative_keywords"] = negative_keywords
            used_tools = append_tool({"used_tools": used_tools}, "summarize_reviews")
            used_tools = append_tool({"used_tools": used_tools}, "extract_negative_keywords")
            tool_details = append_tool_detail(
                {"tool_details": tool_details},
                ToolExecutionDetail(
                    tool_name="summarize_reviews",
                    purpose="汇总最近评论并给出评分分布与正负反馈",
                    tool_input={"product_name": product_name, "days": 7},
                    tool_output=review_summary,
                ).model_dump(),
            )
            tool_details = append_tool_detail(
                {"tool_details": tool_details},
                ToolExecutionDetail(
                    tool_name="extract_negative_keywords",
                    purpose="提取最近差评中的高频问题关键词",
                    tool_input={"product_name": product_name, "days": 7},
                    tool_output=negative_keywords,
                ).model_dump(),
            )
            user_prompt = f"请根据评论摘要和差评关键词输出适合运营复盘的结论：{tool_outputs}"
            section_title = "评论摘要"
            highlights = review_summary.get("positive_samples", [])
            issues = [item["keyword"] for item in negative_keywords.get("keywords", [])]
        elif intent == "competitor_compare":
            competitor_result = compare_competitors(product_name, db=db)
            tool_outputs["competitor_compare"] = competitor_result
            used_tools = append_tool({"used_tools": used_tools}, "compare_competitors")
            tool_details = append_tool_detail(
                {"tool_details": tool_details},
                ToolExecutionDetail(
                    tool_name="compare_competitors",
                    purpose="对比我方商品与竞品资料",
                    tool_input={"product_name": product_name},
                    tool_output=competitor_result,
                ).model_dump(),
            )
            user_prompt = f"请根据竞品对比结果，输出结构化对比和运营建议：{tool_outputs}"
            section_title = "竞品整理"
            highlights = ["我方售后承诺更明确", "具备核心卖点聚焦能力"]
            issues = ["需持续拉开价格心智", "需强化竞品差异表达"]
        else:
            daily_report = generate_daily_report(state.get("daily_report_context", {}))
            tool_outputs["daily_report"] = daily_report
            used_tools = append_tool({"used_tools": used_tools}, "generate_daily_report")
            tool_details = append_tool_detail(
                {"tool_details": tool_details},
                ToolExecutionDetail(
                    tool_name="generate_daily_report",
                    purpose="根据运营上下文生成日报结构化草稿",
                    tool_input=state.get("daily_report_context", {}),
                    tool_output=daily_report,
                ).model_dump(),
            )
            user_prompt = f"请根据日报结构化数据，生成适合汇报的日报总结：{tool_outputs}"
            section_title = "运营日报"
            highlights = daily_report.get("highlights", [])
            issues = daily_report.get("risks", [])

        llm_result = llm_client.generate(
            system_prompt="你是电商分析助手，擅长把评论、竞品和日报数据整理为可执行结论。",
            user_prompt=user_prompt,
            provider=state.get("model_provider"),
        )

        structured_result = AnalysisAgentResult(
            analysis_type=intent,
            product_name=None if intent == "daily_report" else product_name,
            highlights=highlights[:3],
            issues=issues[:5],
            recommendations=[
                "优先处理高频负反馈并同步优化详情页说明",
                "把分析结论沉淀为客服和运营可复用话术",
                "持续观察转化与评价变化，形成下轮迭代闭环",
            ],
            data=tool_outputs,
        ).model_dump()

        draft = f"### {section_title}\n\n{llm_result.text}\n\n```json\n{tool_outputs}\n```"
        return {
            "provider_used": llm_result.provider,
            "tool_outputs": tool_outputs,
            "tool_details": tool_details,
            "used_tools": used_tools,
            "structured_result": structured_result,
            "draft_answer": draft,
            "logs": append_log(state, f"AnalysisAgent 已完成 {intent} 分析。"),
            "agent_path": append_path(state, "AnalysisAgent"),
        }


analysis_agent = AnalysisAgent()

