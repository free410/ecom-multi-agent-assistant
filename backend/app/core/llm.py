import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str
    provider: str
    mode: str


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def resolve_provider(self, provider: str | None) -> str:
        requested = provider or self.settings.default_provider
        if requested == "mock":
            return "mock"
        if requested == "qwen" and self.settings.qwen_api_key and self.settings.qwen_base_url:
            return "qwen"
        if requested == "deepseek" and self.settings.deepseek_api_key and self.settings.deepseek_base_url:
            return "deepseek"
        if requested != "mock":
            logger.warning(
                "Provider %s missing configuration. Falling back to mock mode.",
                requested,
            )
        return "mock"

    def provider_statuses(self) -> dict[str, dict[str, Any]]:
        qwen_configured = bool(self.settings.qwen_api_key and self.settings.qwen_base_url)
        deepseek_configured = bool(self.settings.deepseek_api_key and self.settings.deepseek_base_url)
        return {
            "qwen": {
                "configured": qwen_configured,
                "available": qwen_configured,
                "display_name": "Qwen",
                "fallback": "mock" if not qwen_configured else None,
            },
            "deepseek": {
                "configured": deepseek_configured,
                "available": deepseek_configured,
                "display_name": "DeepSeek",
                "fallback": "mock" if not deepseek_configured else None,
            },
            "mock": {
                "configured": True,
                "available": True,
                "display_name": "Mock",
                "fallback": None,
            },
        }

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: str | None = None,
        temperature: float = 0.4,
    ) -> LLMResult:
        resolved_provider = self.resolve_provider(provider)
        if resolved_provider == "mock":
            return LLMResult(
                text=self._mock_response(system_prompt=system_prompt, user_prompt=user_prompt),
                provider="mock",
                mode="mock",
            )

        base_url, api_key, model = self._provider_config(resolved_provider)
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(
            connect=self.settings.llm_connect_timeout_seconds,
            read=self.settings.llm_read_timeout_seconds,
            write=self.settings.llm_write_timeout_seconds,
            pool=self.settings.llm_pool_timeout_seconds,
        )
        retries = max(self.settings.llm_max_retries, 0)

        last_exception: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return LLMResult(text=content, provider=resolved_provider, mode="remote")
            except httpx.ReadTimeout as exc:
                last_exception = exc
                logger.warning(
                    "Remote LLM read timeout on attempt %s/%s for provider %s.",
                    attempt + 1,
                    retries + 1,
                    resolved_provider,
                )
                if attempt < retries:
                    time.sleep(1.2)
                    continue
            except Exception as exc:
                last_exception = exc
                break

        logger.warning(
            "Remote LLM call failed: %s. Falling back to mock mode.",
            last_exception,
        )
        return LLMResult(
            text=self._mock_response(system_prompt=system_prompt, user_prompt=user_prompt),
            provider="mock",
            mode="mock_fallback",
        )

    def _provider_config(self, provider: str) -> tuple[str, str, str]:
        if provider == "qwen":
            return (
                self.settings.qwen_base_url or "",
                self.settings.qwen_api_key or "",
                self.settings.qwen_model,
            )
        return (
            self.settings.deepseek_base_url or "",
            self.settings.deepseek_api_key or "",
            self.settings.deepseek_model,
        )

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n{user_prompt}".lower()

        if any(keyword in prompt for keyword in ["你好", "您好", "hello", "hi", "你能做什么", "通用对话"]):
            return (
                "你好，我是你的电商运营智能助手。"
                "我可以帮你做商品问答、活动文案、客服回复、评论分析、竞品整理和运营日报。"
                "你可以直接告诉我商品名和任务目标，我会继续处理。"
            )
        if "促销" in prompt or "campaign" in prompt or "文案" in prompt:
            return (
                "推荐文案：\n"
                "1. 限时活动上线，核心卖点直击需求，适合目标人群快速决策。\n"
                "2. 强调品质、价格和使用场景，搭配明确行动号召。\n"
                "3. 建议同步突出优惠时效、售后保障和真实口碑。"
            )
        if "客服" in prompt or "售后" in prompt or "reply" in prompt:
            return "客服建议：先表达理解和歉意，再说明当前处理方案，最后补充售后保障和下一步动作。"
        if "评论" in prompt or "竞品" in prompt or "日报" in prompt:
            return "分析结论：近期反馈集中在体验、价格感知和服务响应上，建议优先处理高频问题并同步优化卖点表达。"
        return "基于商品资料和上下文，建议围绕卖点、适用人群、常见疑问和售后承诺组织回复。"


llm_client = LLMClient()
