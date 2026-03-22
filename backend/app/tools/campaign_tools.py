from typing import Any

from sqlalchemy.orm import Session

from app.tools.product_tools import get_product_info


def generate_campaign_copy(
    product_name: str,
    campaign_theme: str,
    audience: str,
    db: Session | None = None,
) -> dict[str, Any]:
    product_result = get_product_info(product_name, db=db)
    if not product_result["found"]:
        return product_result

    product = product_result["product"]
    headline = f"{campaign_theme}限定 | {product['name']}让{audience}更轻松拥有高质感体验"
    bullets = [
        f"核心卖点：{product['selling_points'][0]}，突出产品差异化体验。",
        f"场景共鸣：适合{audience}在{'、'.join(product['target_users'][:2])}场景中快速决策。",
        f"转化补充：到手价约 {product['price']} 元，搭配“{product['after_sale_policy']}”增强下单信心。",
    ]
    return {
        "found": True,
        "product_name": product["name"],
        "campaign_theme": campaign_theme,
        "audience": audience,
        "headline": headline,
        "bullets": bullets,
        "cta": "立即下单，抢占活动限时优惠。",
    }

