import re
from typing import Any

from sqlalchemy.orm import Session

from app.graph.state import (
    WorkflowState,
    append_log,
    append_path,
    append_restored_field,
    mark_memory_usage,
)
from app.schemas.agent import IntentAgentResult
from app.services.seed_service import seed_service


INTENT_KEYWORDS: dict[str, list[str]] = {
    "daily_report": ["日报", "今日复盘", "运营总结", "报表"],
    "competitor_compare": ["竞品", "差异", "对比", "同行"],
    "review_summary": ["差评", "评论", "关键词", "情感", "问题总结", "摘要"],
    "customer_support": ["客服", "售后", "发货慢", "回复建议", "怎么回复", "退换", "安抚"],
    "campaign_copy": ["campaign", "618", "双11", "促销", "文案", "活动", "海报"],
    "product_qa": ["卖点", "适合人群", "适用人群", "常见问题", "faq", "介绍", "参数"],
}

GENERAL_CHAT_KEYWORDS = [
    "你好",
    "您好",
    "嗨",
    "hi",
    "hello",
    "在吗",
    "你是谁",
    "你能做什么",
    "你会什么",
    "介绍一下你自己",
    "帮帮我",
    "怎么用",
]

FOLLOW_UP_HINTS = ["这款", "这个", "它", "这个产品", "该商品", "我说的是", "就是", "要的是", "它是"]
DIRECT_SUBJECT_REPLY_MAX_LENGTH = 12


class IntentAgent:
    def run(self, state: WorkflowState) -> dict[str, Any]:
        message = state["message"].strip()
        lowered = message.lower()
        db: Session | None = state.get("db_session")
        short_term_memory = state.get("short_term_memory", {})
        preference_memory = state.get("preference_memory", {})
        pending_task = short_term_memory.get("pending_task", {}) or {}

        detected_subject = seed_service.detect_subject(message, db=db)
        product_name = detected_subject.get("product_name")
        subject_name = detected_subject.get("subject_name") or product_name
        subject_type = detected_subject.get("subject_type")

        intent, confidence, routing_reason = self._classify_intent(message, lowered)
        campaign_theme = self._extract_campaign_theme(message)
        audience = self._extract_audience(message)

        memory_used = dict(state.get("memory_used", {}))
        restored_fields = list(state.get("restored_fields", []))
        restore_notes: list[str] = []

        if self._should_resume_pending_task(
            message=message,
            pending_task=pending_task,
            intent=intent,
            confidence=confidence,
            subject_name=subject_name,
            product_name=product_name,
        ):
            intent = pending_task.get("intent", intent)
            confidence = max(confidence, 0.82 if (subject_name or product_name) else 0.68)
            routing_reason = f"延续上一轮待补充任务：{pending_task.get('intent', intent)}"
            memory_used = mark_memory_usage({"memory_used": memory_used}, "short_term_memory")

        (
            product_name,
            subject_name,
            campaign_theme,
            audience,
            memory_used,
            restored_fields,
            restore_notes,
        ) = self._restore_context_fields(
            message=message,
            short_term_memory=short_term_memory,
            preference_memory=preference_memory,
            pending_task=pending_task,
            product_name=product_name,
            subject_name=subject_name,
            campaign_theme=campaign_theme,
            audience=audience,
            memory_used=memory_used,
            restored_fields=restored_fields,
        )

        missing_fields = self._missing_fields(
            intent=intent,
            product_name=product_name,
            subject_name=subject_name,
        )
        needs_clarification = len(missing_fields) > 0 or (
            confidence < 0.5 and intent != "general_chat"
        )

        clarification_question = None
        if needs_clarification:
            clarification_question = self._build_clarification_question(intent, missing_fields)
            confidence = min(confidence, 0.45)

        if restore_notes:
            routing_reason = f"{routing_reason}；{'；'.join(restore_notes)}"

        structured_result = IntentAgentResult(
            intent=intent,
            confidence=round(confidence, 2),
            routing_reason=routing_reason,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            extracted_fields={
                "product_name": product_name,
                "subject_name": subject_name,
                "subject_type": subject_type,
                "campaign_theme": campaign_theme,
                "audience": audience,
            },
            restored_fields=restored_fields,
        ).model_dump()

        return {
            "intent": intent,
            "confidence": round(confidence, 2),
            "routing_reason": routing_reason,
            "product_name": product_name,
            "subject_name": subject_name,
            "subject_type": subject_type,
            "campaign_theme": campaign_theme,
            "audience": audience,
            "daily_report_context": self._extract_daily_report_context(message),
            "needs_clarification": needs_clarification,
            "clarification_question": clarification_question,
            "missing_fields": missing_fields,
            "memory_used": memory_used,
            "restored_fields": restored_fields,
            "structured_result": structured_result,
            "logs": append_log(
                state,
                f"IntentAgent 识别意图为 {intent}，置信度 {round(confidence, 2)}。",
            ),
            "agent_path": append_path(state, "IntentAgent"),
        }

    def _classify_intent(self, message: str, lowered: str) -> tuple[str, float, str]:
        if self._is_general_chat(message, lowered):
            return "general_chat", 0.92, "命中问候或通用咨询关键词，按通用对话处理"

        scores = {intent: 0 for intent in INTENT_KEYWORDS}
        matched_keywords: dict[str, list[str]] = {intent: [] for intent in INTENT_KEYWORDS}

        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                target = lowered if keyword.isascii() else message
                if keyword.lower() in target.lower():
                    scores[intent] += 1
                    matched_keywords[intent].append(keyword)

        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        second_score = sorted(scores.values(), reverse=True)[1]

        if best_score == 0:
            return "general_chat", 0.7, "未命中业务关键词，按通用对话处理"

        confidence = min(0.58 + best_score * 0.12, 0.95)
        if second_score == best_score and best_score > 0:
            confidence -= 0.12

        keywords = "、".join(matched_keywords[best_intent]) or "无"
        reason = f"命中关键词：{keywords}"
        if second_score == best_score and best_score > 0:
            reason += "；存在相近意图，因此置信度下调"
        return best_intent, confidence, reason

    @staticmethod
    def _is_general_chat(message: str, lowered: str) -> bool:
        stripped = lowered.strip()
        if stripped in {"你好", "您好", "hi", "hello", "嗨", "在吗"}:
            return True
        return any(keyword.lower() in lowered for keyword in GENERAL_CHAT_KEYWORDS)

    @staticmethod
    def _should_resume_pending_task(
        message: str,
        pending_task: dict[str, Any],
        intent: str,
        confidence: float,
        subject_name: str | None,
        product_name: str | None,
    ) -> bool:
        if not pending_task or not pending_task.get("intent"):
            return False

        if any(hint in message for hint in FOLLOW_UP_HINTS):
            return True
        if subject_name or product_name:
            return True
        if len(message.strip()) <= DIRECT_SUBJECT_REPLY_MAX_LENGTH and intent == "general_chat":
            return True
        if confidence < 0.62 and pending_task.get("missing_fields"):
            return True
        return False

    def _restore_context_fields(
        self,
        message: str,
        short_term_memory: dict[str, Any],
        preference_memory: dict[str, Any],
        pending_task: dict[str, Any],
        product_name: str | None,
        subject_name: str | None,
        campaign_theme: str | None,
        audience: str | None,
        memory_used: dict[str, bool],
        restored_fields: list[str],
    ) -> tuple[str | None, str | None, str | None, str | None, dict[str, bool], list[str], list[str]]:
        restore_notes: list[str] = []
        vague_reference = any(keyword in message for keyword in FOLLOW_UP_HINTS) or len(message.strip()) <= DIRECT_SUBJECT_REPLY_MAX_LENGTH

        for source in [pending_task, short_term_memory]:
            source_product_name = source.get("product_name") or source.get("recent_product_name")
            source_subject_name = source.get("subject_name") or source.get("recent_subject_name")
            source_campaign_theme = source.get("campaign_theme") or source.get("recent_campaign_theme")
            source_audience = source.get("audience") or source.get("recent_audience")

            if not product_name and source_product_name and vague_reference:
                product_name = source_product_name
                memory_used = mark_memory_usage({"memory_used": memory_used}, "short_term_memory")
                restored_fields = append_restored_field({"restored_fields": restored_fields}, "product_name")
                restore_notes.append("已从短期记忆恢复商品名称")

            if not subject_name and source_subject_name and vague_reference:
                subject_name = source_subject_name
                memory_used = mark_memory_usage({"memory_used": memory_used}, "short_term_memory")
                restored_fields = append_restored_field({"restored_fields": restored_fields}, "subject_name")
                restore_notes.append("已从短期记忆恢复任务主体")

            if not campaign_theme and source_campaign_theme and vague_reference:
                campaign_theme = source_campaign_theme
                memory_used = mark_memory_usage({"memory_used": memory_used}, "short_term_memory")
                restored_fields = append_restored_field({"restored_fields": restored_fields}, "campaign_theme")
                restore_notes.append("已从短期记忆恢复活动主题")

            if not audience and source_audience and vague_reference:
                audience = source_audience
                memory_used = mark_memory_usage({"memory_used": memory_used}, "short_term_memory")
                restored_fields = append_restored_field({"restored_fields": restored_fields}, "audience")
                restore_notes.append("已从短期记忆恢复目标人群")

        if not audience and preference_memory.get("preferred_audience"):
            audience = preference_memory["preferred_audience"]
            memory_used = mark_memory_usage({"memory_used": memory_used}, "preference_memory")
            restored_fields = append_restored_field({"restored_fields": restored_fields}, "audience")
            restore_notes.append("已从偏好记忆恢复目标人群")

        return (
            product_name,
            subject_name,
            campaign_theme,
            audience,
            memory_used,
            restored_fields,
            restore_notes,
        )

    @staticmethod
    def _extract_campaign_theme(message: str) -> str | None:
        for keyword in ["618", "双11", "女王节", "开学季", "春季焕新"]:
            if keyword in message:
                return keyword
        match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]+)活动", message)
        if match:
            return f"{match.group(1)}活动"
        if any(keyword in message for keyword in ["促销", "文案", "海报"]):
            return "限时活动"
        return None

    @staticmethod
    def _extract_audience(message: str) -> str | None:
        for keyword in ["上班族", "学生", "宝妈", "健身人群", "露营爱好者", "办公室人群"]:
            if keyword in message:
                return keyword
        return None

    @staticmethod
    def _extract_daily_report_context(message: str) -> dict[str, Any]:
        return {
            "sales": 12680,
            "traffic": 3590,
            "conversion_rate": "4.6%",
            "completed_tasks": ["完成活动页文案更新", "处理差评关键词分析", "优化客服回复模板"],
            "pending_tasks": ["跟进发货时效投诉", "补充竞品对比卡片"],
            "highlights": ["咖啡杯点击率提升12%", "榨汁杯收藏加购提升9%"],
            "risks": ["两款商品物流时效反馈偏多", "桌面风扇包装质检需加强"],
        }

    @staticmethod
    def _missing_fields(
        intent: str,
        product_name: str | None,
        subject_name: str | None,
    ) -> list[str]:
        if intent in {"daily_report", "general_chat"}:
            return []

        if intent in {"review_summary", "competitor_compare"}:
            return [] if product_name else ["product_name"]

        if intent in {"product_qa", "campaign_copy", "customer_support"}:
            return [] if (product_name or subject_name) else ["subject_name"]

        return []

    @staticmethod
    def _build_clarification_question(intent: str, missing_fields: list[str]) -> str:
        if "product_name" in missing_fields and intent in {"review_summary", "competitor_compare"}:
            return (
                "我可以继续处理这个任务，但评论分析和竞品对比需要具体商品名才能调用数据。"
                "请告诉我明确商品，例如：云萃保温咖啡杯。"
            )

        if "subject_name" in missing_fields:
            return (
                "我可以继续处理这个任务，但还缺少任务主体。"
                "你可以告诉我具体商品名，也可以直接说类目名。"
                "例如：云萃保温咖啡杯、iPhone 16、手机、耳机。"
            )

        return "为了更准确地继续，请补充更具体的商品、类目或目标信息。"


intent_agent = IntentAgent()
