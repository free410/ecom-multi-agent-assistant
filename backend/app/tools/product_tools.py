from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.services.seed_service import seed_service


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
    product = seed_service.find_product(product_name, db=db)
    if not product:
        return {"found": False, "message": f"未找到商品：{product_name}"}
    return {
        "found": True,
        "product": product,
        "summary": f"{product['name']} 主打 {'、'.join(product['selling_points'][:3])}，适合 {'、'.join(product['target_users'])}。",
    }


def search_product_faq(product_name: str, question: str, db: Session | None = None) -> dict[str, Any]:
    product = seed_service.find_product(product_name, db=db)
    if not product:
        return {"found": False, "message": f"未找到商品：{product_name}"}

    faq_item = _match_faq(question, product["faq"])
    return {
        "found": True,
        "matched": faq_item is not None,
        "question": question,
        "faq": faq_item,
        "fallback_after_sale": product["after_sale_policy"],
    }

