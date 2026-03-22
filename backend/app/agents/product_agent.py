from typing import Any

from app.core.llm import llm_client
from app.graph.state import WorkflowState, append_log, append_path, append_tool
from app.tools.product_tools import get_product_info, search_product_faq


class ProductKnowledgeAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        product_name = state.get("product_name") or "云萃保温咖啡杯"
        db = state.get("db_session")
        product_result = get_product_info(product_name, db=db)
        faq_result = search_product_faq(product_name, state["message"], db=db)

        prompt = (
            f"请根据以下商品资料回答用户问题。\n"
            f"商品信息：{product_result}\n"
            f"FAQ结果：{faq_result}\n"
            f"用户问题：{state['message']}\n"
            "输出简洁、适合电商运营或客服场景。"
        )
        llm_result = llm_client.generate(
            system_prompt="你是电商商品知识助手，擅长把商品卖点和FAQ整理成清晰回答。",
            user_prompt=prompt,
            provider=state.get("model_provider"),
        )

        draft = (
            f"### 商品问答\n"
            f"- 商品：{product_result['product']['name'] if product_result['found'] else product_name}\n"
            f"- 卖点：{'、'.join(product_result['product']['selling_points']) if product_result['found'] else '暂无'}\n"
            f"- 适用人群：{'、'.join(product_result['product']['target_users']) if product_result['found'] else '暂无'}\n"
            f"- FAQ匹配：{faq_result.get('faq', {}).get('answer', '未命中FAQ，建议结合售后规则解释')}\n\n"
            f"{llm_result.text}"
        )
        return {
            "provider_used": llm_result.provider,
            "tool_outputs": {"product_info": product_result, "faq_result": faq_result},
            "draft_answer": draft,
            "logs": append_log(state, f"ProductKnowledgeAgent 已完成商品知识检索，LLM 模式为 {llm_result.mode}。"),
            "used_tools": append_tool(
                {"used_tools": append_tool(state, "get_product_info")},
                "search_product_faq",
            ),
            "agent_path": append_path(state, "ProductKnowledgeAgent"),
        }


product_agent = ProductKnowledgeAgent()

