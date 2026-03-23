from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.services.seed_service import seed_service
from app.tools.tool_response import build_tool_response


def _match_faq(question: str, faq_list: list[dict[str, str]]) -> dict[str, str] | None:
    best_score = 0.0
    best_item = None
    for faq in faq_list:
        score = SequenceMatcher(None, question.lower(), faq["question"].lower()).ratio()
        if score > best_score:
            best_score = score
            best_item = faq
    return best_item


def get_product_info(product_name: str, db: Session | None = None) -> dict[str, Any]:
    return build_tool_response(
        tool_name="get_product_info",
        tool_input={"product_name": product_name},
        executor=lambda: _get_product_info_impl(product_name, db=db),
    )


def _get_product_info_impl(product_name: str, db: Session | None = None) -> dict[str, Any]:
    product = seed_service.find_product(product_name, db=db)
    if product:
        return {
            "found": True,
            "source": "seed",
            "product": product,
            "summary": f"{product['name']} 主打 {'、'.join(product['selling_points'][:3])}，适合 {'、'.join(product['target_users'])}。",
        }

    generic_product = seed_service.build_generic_product_profile(product_name)
    return {
        "found": True,
        "source": "generic",
        "product": generic_product,
        "summary": f"{generic_product['name']} 可围绕 {'、'.join(generic_product['selling_points'][:3])} 来组织表达，适合 {'、'.join(generic_product['target_users'])}。",
        "message": f"未命中内置商品数据，已按“{product_name}”类目生成通用商品资料。",
    }


def search_product_faq(product_name: str, question: str, db: Session | None = None) -> dict[str, Any]:
    return build_tool_response(
        tool_name="search_product_faq",
        tool_input={"product_name": product_name, "question": question},
        executor=lambda: _search_product_faq_impl(product_name, question, db=db),
    )


def _search_product_faq_impl(
    product_name: str,
    question: str,
    db: Session | None = None,
) -> dict[str, Any]:
    product_result = _get_product_info_impl(product_name, db=db)
    if not product_result["found"]:
        return {"found": False, "message": f"未找到商品：{product_name}"}

    product = product_result["product"]
    faq_item = _match_faq(question, product["faq"])
    return {
        "found": True,
        "source": product_result.get("source", "seed"),
        "matched": faq_item is not None,
        "question": question,
        "faq": faq_item,
        "fallback_after_sale": product["after_sale_policy"],
    }
