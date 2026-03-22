import re
from typing import Any

from sqlalchemy.orm import Session

from app.graph.state import WorkflowState, append_log, append_path
from app.services.seed_service import seed_service


class IntentAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        message = state["message"]
        db: Session | None = state.get("db_session")
        lowered = message.lower()

        intent = "product_qa"
        if any(keyword in message for keyword in ["日报", "今日复盘", "运营总结"]):
            intent = "daily_report"
        elif any(keyword in message for keyword in ["竞品", "差异", "对比"]):
            intent = "competitor_compare"
        elif any(keyword in message for keyword in ["差评", "评论", "关键词", "情感", "问题总结"]):
            intent = "review_summary"
        elif any(keyword in message for keyword in ["客服", "售后", "发货慢", "回复建议", "怎么回复"]):
            intent = "customer_support"
        elif any(keyword in lowered for keyword in ["campaign", "618", "双11", "促销", "文案", "活动"]):
            intent = "campaign_copy"

        product_name = seed_service.detect_product_name(message, db=db)
        campaign_theme = self._extract_campaign_theme(message)
        audience = self._extract_audience(message)

        return {
            "intent": intent,
            "product_name": product_name,
            "campaign_theme": campaign_theme,
            "audience": audience,
            "daily_report_context": self._extract_daily_report_context(message),
            "logs": append_log(state, f"IntentAgent 识别意图为 {intent}。"),
            "agent_path": append_path(state, "IntentAgent"),
        }

    @staticmethod
    def _extract_campaign_theme(message: str) -> str:
        for keyword in ["618", "双11", "女王节", "开学季", "春季焕新"]:
            if keyword in message:
                return keyword
        match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]+)活动", message)
        if match:
            return f"{match.group(1)}活动"
        return "限时活动"

    @staticmethod
    def _extract_audience(message: str) -> str:
        for keyword in ["上班族", "学生", "宝妈", "健身人群", "露营爱好者", "办公室人群"]:
            if keyword in message:
                return keyword
        return "目标人群"

    @staticmethod
    def _extract_daily_report_context(message: str) -> dict[str, Any]:
        if "日报" not in message:
            return {
                "sales": 12680,
                "traffic": 3590,
                "conversion_rate": "4.6%",
                "completed_tasks": ["完成活动页文案更新", "处理差评关键词分析", "优化客服回复模版"],
                "pending_tasks": ["跟进发货时效投诉", "补充竞品对比卡片"],
                "highlights": ["咖啡杯点击率提升12%", "榨汁杯收藏加购提升9%"],
                "risks": ["两款商品物流时效反馈偏多", "桌面风扇包装质检需加强"],
            }
        return {
            "sales": 12680,
            "traffic": 3590,
            "conversion_rate": "4.6%",
            "completed_tasks": ["完成活动页文案更新", "处理差评关键词分析", "优化客服回复模版"],
            "pending_tasks": ["跟进发货时效投诉", "补充竞品对比卡片"],
            "highlights": ["咖啡杯点击率提升12%", "榨汁杯收藏加购提升9%"],
            "risks": ["两款商品物流时效反馈偏多", "桌面风扇包装质检需加强"],
        }


intent_agent = IntentAgent()

