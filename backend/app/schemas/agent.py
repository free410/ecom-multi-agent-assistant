from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolExecutionDetail(BaseModel):
    tool_name: str
    purpose: str
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: Any = None
    status: Literal["success", "skipped", "fallback"] = "success"


class MemoryUsageDetail(BaseModel):
    short_term_memory: bool = False
    preference_memory: bool = False


class IntentAgentResult(BaseModel):
    agent: str = "IntentAgent"
    intent: str
    confidence: float
    routing_reason: str
    needs_clarification: bool
    clarification_question: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    restored_fields: list[str] = Field(default_factory=list)


class ClarificationNodeResult(BaseModel):
    agent: str = "ClarificationNode"
    question: str
    missing_fields: list[str] = Field(default_factory=list)
    context_preview: dict[str, Any] = Field(default_factory=dict)


class GeneralAgentResult(BaseModel):
    agent: str = "GeneralAgent"
    user_message: str
    reply: str
    suggested_prompts: list[str] = Field(default_factory=list)


class ProductKnowledgeAgentResult(BaseModel):
    agent: str = "ProductKnowledgeAgent"
    product_name: str
    summary: str
    selling_points: list[str]
    target_users: list[str]
    faq_hit: bool
    faq_answer: str | None = None
    after_sale_policy: str | None = None
    suggested_answer: str


class ContentAgentResult(BaseModel):
    agent: str = "ContentAgent"
    product_name: str
    campaign_theme: str
    audience: str
    headline: str
    bullets: list[str]
    cta: str
    optimized_copy: str


class SupportAgentResult(BaseModel):
    agent: str = "SupportAgent"
    product_name: str
    user_question: str
    faq_hit: bool
    suggested_reply: str
    polished_reply: str


class AnalysisAgentResult(BaseModel):
    agent: str = "AnalysisAgent"
    analysis_type: str
    product_name: str | None = None
    highlights: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class SummaryAgentResult(BaseModel):
    agent: str = "SummaryAgent"
    title: str
    answer_markdown: str
    next_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
