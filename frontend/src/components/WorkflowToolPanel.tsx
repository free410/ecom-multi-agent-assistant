import { useState } from "react";
import type { ChatResponse, ToolDetail } from "../types";

interface WorkflowToolPanelProps {
  result: ChatResponse | null;
  onFill: (prompt: string) => void;
  onRun: (prompt: string) => void;
  compact?: boolean;
}

interface ToolCatalogItem {
  toolName: string;
  title: string;
  scenario: string;
  samplePrompt: string;
}

const TOOL_CATALOG: ToolCatalogItem[] = [
  {
    toolName: "get_product_info",
    title: "商品信息检索",
    scenario: "商品问答、卖点提炼、客服回复前置检索",
    samplePrompt: "云萃保温咖啡杯适合哪些人群，有哪些卖点？",
  },
  {
    toolName: "search_product_faq",
    title: "FAQ 检索",
    scenario: "根据用户问题匹配 FAQ 与售后规则",
    samplePrompt: "这款咖啡杯可以放进洗碗机吗？",
  },
  {
    toolName: "summarize_reviews",
    title: "评论摘要",
    scenario: "汇总最近评论的整体反馈和情绪走势",
    samplePrompt: "总结云萃保温咖啡杯最近 7 天评论情况",
  },
  {
    toolName: "extract_negative_keywords",
    title: "差评关键词提取",
    scenario: "提取高频负面问题，辅助运营排查",
    samplePrompt: "总结云萃保温咖啡杯最近 7 天差评关键词",
  },
  {
    toolName: "generate_campaign_copy",
    title: "活动文案生成",
    scenario: "根据卖点、主题和人群生成促销文案",
    samplePrompt: "根据云萃保温咖啡杯的卖点生成 618 促销文案",
  },
  {
    toolName: "build_customer_reply",
    title: "客服回复生成",
    scenario: "结合售后规则生成安抚型回复建议",
    samplePrompt: "针对发货慢生成客服回复建议",
  },
  {
    toolName: "compare_competitors",
    title: "竞品对比整理",
    scenario: "整理我方商品与竞品的差异和优势",
    samplePrompt: "整理云萃保温咖啡杯与竞品的差异",
  },
  {
    toolName: "generate_daily_report",
    title: "运营日报生成",
    scenario: "根据上下文数据生成日报和待办建议",
    samplePrompt: "生成今天的运营日报",
  },
];

const AGENT_LABELS: Record<string, string> = {
  ContextLoader: "上下文加载",
  IntentAgent: "意图识别",
  ClarificationNode: "补充信息",
  GeneralAgent: "通用对话",
  ProductKnowledgeAgent: "商品知识",
  ProductAgent: "商品知识",
  ContentAgent: "内容生成",
  SupportAgent: "客服支持",
  AnalysisAgent: "分析处理",
  SummaryAgent: "结果汇总",
};

const TOOL_LABELS: Record<string, string> = {
  get_product_info: "商品信息检索",
  search_product_faq: "FAQ 检索",
  summarize_reviews: "评论摘要",
  extract_negative_keywords: "差评关键词提取",
  generate_campaign_copy: "活动文案生成",
  build_customer_reply: "客服回复生成",
  compare_competitors: "竞品对比整理",
  generate_daily_report: "运营日报生成",
};

const STATUS_LABELS: Record<string, string> = {
  success: "成功",
  skipped: "跳过",
  fallback: "回退",
};

function getAgentLabel(agent: string) {
  return AGENT_LABELS[agent] || agent;
}

function getToolLabel(tool: string) {
  return TOOL_LABELS[tool] || tool;
}

function getToolStatus(detail: ToolDetail) {
  const status = detail.status || "success";
  return STATUS_LABELS[status] || status;
}

function getLatency(detail: ToolDetail) {
  if (typeof detail.latency_ms === "number") {
    return `${detail.latency_ms} ms`;
  }

  const nestedLatency =
    detail.tool_output && typeof detail.tool_output === "object" && "latency_ms" in detail.tool_output
      ? (detail.tool_output as { latency_ms?: unknown }).latency_ms
      : undefined;

  return typeof nestedLatency === "number" ? `${nestedLatency} ms` : "-";
}

export function WorkflowToolPanel({
  result,
  onFill,
  onRun,
  compact = false,
}: WorkflowToolPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const activeTools = new Set(result?.used_tools ?? []);
  const toolDetails = Array.isArray(result?.tool_details) ? result.tool_details : [];
  const agentPath = Array.isArray(result?.agent_path) ? result.agent_path : [];

  return (
    <section className={`panel workflow-panel collapsible-panel ${compact ? "compact" : ""} ${collapsed ? "is-collapsed" : ""}`}>
      <div className="panel-header workflow-header">
        <h2>工具与工作流</h2>
        <button
          type="button"
          className={`collapse-arrow ${collapsed ? "is-collapsed" : ""}`}
          onClick={() => setCollapsed((prev) => !prev)}
          aria-label={collapsed ? "展开工具与工作流" : "收起工具与工作流"}
          title={collapsed ? "展开" : "收起"}
        >
          &gt;
        </button>
      </div>

      {!collapsed ? (
        <div className="workflow-layout compact-layout">
          <section className="workflow-section flat-section">
            <div className="workflow-section-title">
              <h3>本轮工作流</h3>
            </div>
            {result ? (
              <div className="workflow-flow-list">
                {agentPath.map((agent, index) => (
                  <button
                    key={`${agent}-${index}`}
                    type="button"
                    className="workflow-chip flat-chip"
                    onClick={() => onFill(`解释一下 ${getAgentLabel(agent)} 在这次任务中的作用`)}
                  >
                    <span className="workflow-chip-index">{index + 1}</span>
                    <span>{getAgentLabel(agent)}</span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="empty-text">发送消息后，这里会展示本轮经过的 Agent 节点。</p>
            )}
          </section>

          <section className="workflow-section flat-section">
            <div className="workflow-section-title">
              <h3>本轮工具调用</h3>
            </div>
            {toolDetails.length > 0 ? (
              <div className="tool-call-list compact-call-list">
                {toolDetails.map((detail, index) => (
                  <article
                    key={`${detail.tool_name}-${index}`}
                    className={`tool-call-card compact-call-card ${activeTools.has(detail.tool_name) ? "active" : ""}`}
                  >
                    <div className="tool-call-top">
                      <strong>{getToolLabel(detail.tool_name)}</strong>
                      <span className="tool-status-badge">{getToolStatus(detail)}</span>
                    </div>
                    <div className="tool-call-meta">
                      <span>{getLatency(detail)}</span>
                      <span>{detail.purpose || "辅助当前任务处理"}</span>
                    </div>
                    <div className="card-actions compact-actions">
                      <button
                        type="button"
                        className="mini-ghost"
                        onClick={() => onFill(`解释工具 ${getToolLabel(detail.tool_name)} 这次的执行结果`)}
                      >
                        查看结果
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-text">本轮没有触发工具调用。</p>
            )}
          </section>

          <section className="workflow-section flat-section">
            <div className="workflow-section-title">
              <h3>工具总览</h3>
            </div>
            <div className="tool-catalog-grid compact-catalog-grid">
              {TOOL_CATALOG.map((tool) => {
                const isActive = activeTools.has(tool.toolName);
                return (
                  <article key={tool.toolName} className={`tool-catalog-card compact-catalog-card ${isActive ? "active" : ""}`}>
                    <div className="tool-catalog-header">
                      <strong>{tool.title}</strong>
                      {isActive ? <span className="catalog-active-badge">本轮已调用</span> : null}
                    </div>
                    <p className="tool-purpose">触发场景：{tool.scenario}</p>
                    <div className="catalog-badges compact-badges">
                      <span className="catalog-badge success">已接入</span>
                      <span className="catalog-badge verified">已验证</span>
                    </div>
                    <div className="card-actions compact-actions">
                      <button type="button" className="mini-primary" onClick={() => onRun(tool.samplePrompt)}>
                        演示
                      </button>
                      <button type="button" className="mini-ghost" onClick={() => onFill(tool.samplePrompt)}>
                        填入
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        </div>
      ) : (
        <div className="collapsed-panel-placeholder">
          <span className="hint-text">已收起工具与工作流</span>
        </div>
      )}
    </section>
  );
}
