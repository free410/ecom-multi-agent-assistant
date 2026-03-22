from typing import Any


def generate_daily_report(input_context: dict[str, Any]) -> dict[str, Any]:
    sales = input_context.get("sales", 0)
    traffic = input_context.get("traffic", 0)
    conversion_rate = input_context.get("conversion_rate", "0%")
    completed_tasks = input_context.get("completed_tasks", [])
    pending_tasks = input_context.get("pending_tasks", [])
    highlights = input_context.get("highlights", [])
    risks = input_context.get("risks", [])

    return {
        "headline": "电商运营日报",
        "overview": {
            "sales": sales,
            "traffic": traffic,
            "conversion_rate": conversion_rate,
        },
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "highlights": highlights,
        "risks": risks,
        "next_actions": [
            "持续跟进高频售后问题并优化客服话术。",
            "围绕高转化商品补充活动文案和短链路卖点。",
            "针对差评关键词同步优化详情页说明和发货预期。",
        ],
    }

