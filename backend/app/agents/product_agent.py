from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool, append_tool_detail
from app.schemas.agent import ProductKnowledgeAgentResult, ToolExecutionDetail
from app.tools.product_tools import get_product_info, search_product_faq


class ProductKnowledgeAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        subject_name = state.get("product_name") or state.get("subject_name") or "云萃保温咖啡杯"
        db = state.get("db_session")

        product_result = get_product_info(subject_name, db=db)
        faq_result = search_product_faq(subject_name, state["message"], db=db)

        prompt = (
            "请根据以下商品资料回答用户问题，语言简洁，适合电商运营或客服场景。\n"
            f"商品信息：{product_result}\n"
            f"FAQ结果：{faq_result}\n"
            f"用户问题：{state['message']}"
        )
        llm_result = llm_client.generate(
            system_prompt="你是电商商品知识助手，擅长把商品卖点和 FAQ 整理成清晰回答。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        product = product_result.get("product", {})
        structured_result = ProductKnowledgeAgentResult(
            product_name=product.get("name", subject_name),
            summary=product_result.get("summary", ""),
            selling_points=product.get("selling_points", []),
            target_users=product.get("target_users", []),
            faq_hit=bool(faq_result.get("matched")),
            faq_answer=(faq_result.get("faq") or {}).get("answer"),
            after_sale_policy=product.get("after_sale_policy"),
            suggested_answer=llm_result.text,
        ).model_dump()

        draft = (
            "### 商品问答\n"
            f"- 商品：{structured_result['product_name']}\n"
            f"- 卖点：{'、'.join(structured_result['selling_points']) or '暂无'}\n"
            f"- 适用人群：{'、'.join(structured_result['target_users']) or '暂无'}\n"
            f"- FAQ匹配：{structured_result['faq_answer'] or '未命中FAQ，建议结合售后规则解释'}\n\n"
            f"{llm_result.text}"
        )

        tool_details = append_tool_detail(
            state,
            ToolExecutionDetail(
                tool_name="get_product_info",
                purpose="检索商品卖点、适用人群、价格与售后规则",
                tool_input={"product_name": subject_name},
                tool_output=product_result,
            ).model_dump(),
        )
        tool_details = append_tool_detail(
            {"tool_details": tool_details},
            ToolExecutionDetail(
                tool_name="search_product_faq",
                purpose="根据用户问题匹配商品 FAQ",
                tool_input={"product_name": subject_name, "question": state["message"]},
                tool_output=faq_result,
            ).model_dump(),
        )

        used_tools = append_tool(state, "get_product_info")
        used_tools = append_tool({"used_tools": used_tools}, "search_product_faq")

        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"product_info": product_result, "faq_result": faq_result},
            "tool_details": tool_details,
            "used_tools": used_tools,
            "structured_result": structured_result,
            "draft_answer": draft,
            "logs": append_log(state, f"ProductKnowledgeAgent 已完成商品知识检索，LLM 模式为 {llm_result.mode}。"),
            "agent_path": append_path(state, "ProductKnowledgeAgent"),
        }


product_agent = ProductKnowledgeAgent()
