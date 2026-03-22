from typing import Any

from sqlalchemy.orm import Session

from app.tools.product_tools import get_product_info, search_product_faq


def build_customer_reply(product_name: str, user_question: str, db: Session | None = None) -> dict[str, Any]:
    product_result = get_product_info(product_name, db=db)
    if not product_result["found"]:
        return product_result

    faq_result = search_product_faq(product_name, user_question, db=db)
    product = product_result["product"]
    answer = (
        f"您好，关于您提到的“{user_question}”，我们已经帮您核对 {product['name']} 的信息。"
    )
    if faq_result.get("matched") and faq_result.get("faq"):
        answer += f" 官方建议是：{faq_result['faq']['answer']}"
    else:
        answer += " 当前建议先确认订单信息和使用场景，我们会继续协助跟进。"
    answer += f" 同时本商品售后规则为：{product['after_sale_policy']}"

    return {
        "found": True,
        "product_name": product["name"],
        "user_question": user_question,
        "faq_hit": faq_result.get("matched", False),
        "reply": answer,
    }

