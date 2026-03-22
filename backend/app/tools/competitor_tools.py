from typing import Any

from sqlalchemy.orm import Session

from app.tools.product_tools import get_product_info
from app.services.seed_service import seed_service


def compare_competitors(product_name: str, db: Session | None = None) -> dict[str, Any]:
    product_result = get_product_info(product_name, db=db)
    if not product_result["found"]:
        return product_result

    product = product_result["product"]
    competitors = seed_service.get_competitors(product_name=product["name"])
    comparisons = []
    for competitor in competitors:
        comparisons.append(
            {
                "competitor_name": competitor["name"],
                "our_advantages": [
                    f"我方主打 {product['selling_points'][0]}",
                    f"售后承诺更明确：{product['after_sale_policy']}",
                ],
                "competitor_highlights": competitor["highlights"],
                "competitor_weaknesses": competitor["weaknesses"],
                "price_range": competitor["price_range"],
            }
        )

    return {
        "found": True,
        "product_name": product["name"],
        "base_price": product["price"],
        "comparisons": comparisons,
    }

