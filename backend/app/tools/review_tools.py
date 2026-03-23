from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.seed_service import seed_service
from app.tools.tool_response import build_tool_response


NEGATIVE_KEYWORD_CANDIDATES = [
    "发货慢",
    "包装",
    "杯盖",
    "续航",
    "物流",
    "噪音",
    "划痕",
    "偏小",
    "说明书",
    "防水塞",
    "太硬",
    "塑料感",
]


def _recent_reviews(product_name: str, days: int) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    product = seed_service.find_product(product_name)
    if not product:
        return None, []

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
    reviews = []
    for review in seed_service.get_reviews(product_id=product["id"]):
        review_date = datetime.strptime(review["created_at"], "%Y-%m-%d").date()
        if review_date >= cutoff:
            reviews.append(review)
    return product, reviews


def summarize_reviews(product_name: str, days: int = 7) -> dict[str, Any]:
    return build_tool_response(
        tool_name="summarize_reviews",
        tool_input={"product_name": product_name, "days": days},
        executor=lambda: _summarize_reviews_impl(product_name, days),
    )


def _summarize_reviews_impl(product_name: str, days: int = 7) -> dict[str, Any]:
    product, reviews = _recent_reviews(product_name, days)
    if not product:
        return {"found": False, "message": f"未找到商品：{product_name}"}

    if not reviews:
        return {"found": True, "product_name": product_name, "review_count": 0, "summary": "最近没有评论数据。"}

    rating_counter = Counter(review["rating"] for review in reviews)
    positives = [item["content"] for item in reviews if item["rating"] >= 4][:3]
    negatives = [item["content"] for item in reviews if item["rating"] <= 3][:3]

    return {
        "found": True,
        "product_name": product["name"],
        "review_count": len(reviews),
        "average_rating": round(sum(item["rating"] for item in reviews) / len(reviews), 2),
        "rating_distribution": dict(sorted(rating_counter.items())),
        "positive_samples": positives,
        "negative_samples": negatives,
        "summary": (
            f"最近{days}天共{len(reviews)}条评论，整体评分 {round(sum(item['rating'] for item in reviews) / len(reviews), 2)} 分。"
            f" 正向反馈集中在{'、'.join(_top_words(positives)) or '体验、品质'}，"
            f"负向反馈集中在{'、'.join(_top_words(negatives)) or '物流、细节体验'}。"
        ),
    }


def extract_negative_keywords(product_name: str, days: int = 7) -> dict[str, Any]:
    return build_tool_response(
        tool_name="extract_negative_keywords",
        tool_input={"product_name": product_name, "days": days},
        executor=lambda: _extract_negative_keywords_impl(product_name, days),
    )


def _extract_negative_keywords_impl(product_name: str, days: int = 7) -> dict[str, Any]:
    product, reviews = _recent_reviews(product_name, days)
    if not product:
        return {"found": False, "message": f"未找到商品：{product_name}"}

    negative_reviews = [item for item in reviews if item["rating"] <= 3]
    keyword_counter: Counter[str] = Counter()
    for review in negative_reviews:
        content = review["content"]
        for keyword in NEGATIVE_KEYWORD_CANDIDATES:
            if keyword in content:
                keyword_counter[keyword] += 1

    top_keywords = [{"keyword": key, "count": value} for key, value in keyword_counter.most_common(5)]
    return {
        "found": True,
        "product_name": product["name"],
        "negative_review_count": len(negative_reviews),
        "keywords": top_keywords,
        "examples": [item["content"] for item in negative_reviews[:3]],
    }


def _top_words(sentences: list[str]) -> list[str]:
    if not sentences:
        return []

    candidates = ["保温", "颜值", "轻便", "续航", "清洗", "支撑", "风力", "静音", "发货", "包装", "划痕"]
    counter: Counter[str] = Counter()
    for sentence in sentences:
        for word in candidates:
            if word in sentence:
                counter[word] += 1
    return [word for word, _ in counter.most_common(3)]

