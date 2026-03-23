import { useState } from "react";
import type { ChatResponse, ToolDetail } from "../types";

interface ExecutionPanelProps {
  result: ChatResponse | null;
  onFill: (prompt: string) => void;
  onRun: (prompt: string) => void;
}

const INTENT_LABELS: Record<string, string> = {
  product_qa: "商品问答",
  campaign_copy: "活动文案",
  customer_support: "客服回复",
  review_summary: "评论摘要",
  competitor_compare: "竞品整理",
  daily_report: "运营日报",
  general_chat: "通用对话",
};

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
  compare_competitors: "竞品对比",
  generate_daily_report: "日报生成",
};

const STATUS_LABELS: Record<string, string> = {
  success: "成功",
  skipped: "跳过",
  fallback: "回退",
};

const PROVIDER_LABELS: Record<string, string> = {
  qwen: "Qwen",
  deepseek: "DeepSeek",
  mock: "Mock",
  unknown: "未知",
};

function getIntentLabel(intent: string): string {
  return INTENT_LABELS[intent] || intent;
}

function getAgentLabel(agent: string): string {
  return AGENT_LABELS[agent] || agent;
}

function getToolLabel(toolName: string): string {
  return TOOL_LABELS[toolName] || toolName;
}

function getStatusLabel(status: string | undefined): string {
  return STATUS_LABELS[status || "success"] || status || "成功";
}

function getProviderLabel(provider: string): string {
  return PROVIDER_LABELS[provider] || provider;
}

function getRestoredFieldLabel(field: string): string {
  if (field === "product_name") return "商品名称";
  if (field === "campaign_theme") return "活动主题";
  if (field === "audience") return "目标人群";
  return field;
}

function resolveLatency(detail: ToolDetail): string {
  if (typeof detail.latency_ms === "number") {
    return `${detail.latency_ms} ms`;
  }

  const nestedLatency =
    detail.tool_output && typeof detail.tool_output === "object" && "latency_ms" in detail.tool_output
      ? (detail.tool_output as { latency_ms?: unknown }).latency_ms
      : undefined;

  return typeof nestedLatency === "number" ? `${nestedLatency} ms` : "-";
}

export function ExecutionPanel({ result, onFill, onRun }: ExecutionPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (!result) {
    return (
      <section className="panel execution-panel collapsible-panel">
        <div className="panel-header">
          <h2>执行面板</h2>
          <button
            type="button"
            className={`collapse-arrow ${collapsed ? "is-collapsed" : ""}`}
            onClick={() => setCollapsed((prev) => !prev)}
            aria-label={collapsed ? "展开执行面板" : "收起执行面板"}
            title={collapsed ? "展开" : "收起"}
          >
            &gt;
          </button>
        </div>
        {!collapsed ? <p className="empty-text">发送消息后，这里会展示意图、置信度、路由原因、记忆与工具执行信息。</p> : null}
      </section>
    );
  }

  const confidence = typeof result.confidence === "number" ? result.confidence : 0;
  const provider = result.provider_used || "unknown";
  const routingReason = result.routing_reason || "暂无";
  const memoryUsed = result.memory_used ?? {
    short_term_memory: false,
    preference_memory: false,
  };
  const restoredFields = Array.isArray(result.restored_fields) ? result.restored_fields : [];
  const agentPath = Array.isArray(result.agent_path) ? result.agent_path : [];
  const usedTools = Array.isArray(result.used_tools) ? result.used_tools : [];
  const toolDetails = Array.isArray(result.tool_details) ? result.tool_details : [];
  const logs = Array.isArray(result.logs) ? result.logs : [];
  const intent = result.intent || "unknown";

  return (
    <section className={`panel execution-panel collapsible-panel ${collapsed ? "is-collapsed" : ""}`}>
      <div className="panel-header">
        <h2>执行面板</h2>
        <button
          type="button"
          className={`collapse-arrow ${collapsed ? "is-collapsed" : ""}`}
          onClick={() => setCollapsed((prev) => !prev)}
          aria-label={collapsed ? "展开执行面板" : "收起执行面板"}
          title={collapsed ? "展开" : "收起"}
        >
          &gt;
        </button>
      </div>

      {!collapsed ? (
        <div className="execution-content">
          <div className="meta-group">
            <span className="meta-label">意图</span>
            <button
              type="button"
              className="action-tag inset-control"
              onClick={() => onRun(`围绕 ${getIntentLabel(intent)} 这个任务，再给我一个后续优化建议`)}
            >
              {getIntentLabel(intent)}
            </button>
          </div>

          <div className="meta-group">
            <span className="meta-label">置信度</span>
            <button
              type="button"
              className="action-tag inset-control"
              onClick={() => onFill(`请解释为什么这次路由置信度是 ${confidence.toFixed(2)}`)}
            >
              {confidence.toFixed(2)}
            </button>
          </div>

          <div className="meta-group">
            <span className="meta-label">模型提供方</span>
            <button
              type="button"
              className="action-tag inset-control"
              onClick={() => onFill(`请说明为什么这次实际使用的是 ${getProviderLabel(provider)} provider`)}
            >
              {getProviderLabel(provider)}
            </button>
          </div>

          <div className="meta-group">
            <span className="meta-label">路由原因</span>
            <button
              type="button"
              className="copy-block inset-control"
              onClick={() => onFill(`请基于这条路由原因继续分析：${routingReason}`)}
            >
              {routingReason}
            </button>
          </div>

          <div className="meta-group">
            <span className="meta-label">记忆使用</span>
            <div className="tag-list inset-cluster">
              <button
                type="button"
                className={`tag-button ${memoryUsed.short_term_memory ? "active-tag" : ""}`}
                onClick={() => onFill("请基于当前会话短期记忆继续追问")}
              >
                短期记忆
              </button>
              <button
                type="button"
                className={`tag-button ${memoryUsed.preference_memory ? "active-tag" : ""}`}
                onClick={() => onFill("请基于我的历史偏好继续优化输出风格")}
              >
                偏好记忆
              </button>
            </div>
          </div>

          <div className="meta-group">
            <span className="meta-label">恢复字段</span>
            <div className="tag-list inset-cluster">
              {restoredFields.length > 0 ? (
                restoredFields.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className="tag-button subtle"
                    onClick={() => onFill(`请基于已恢复字段 ${getRestoredFieldLabel(item)} 继续完善当前任务`)}
                  >
                    {getRestoredFieldLabel(item)}
                  </button>
                ))
              ) : (
                <button
                  type="button"
                  className="tag-button subtle disabled-tag"
                  onClick={() => onFill("当前没有恢复字段，请解释为什么本轮没有使用记忆恢复")}
                >
                  无
                </button>
              )}
            </div>
          </div>

          <div className="meta-group">
            <span className="meta-label">执行路径</span>
            <div className="tag-list inset-cluster">
              {agentPath.map((item) => (
                <button
                  type="button"
                  key={item}
                  className="tag-button"
                  onClick={() => onFill(`解释一下 ${getAgentLabel(item)} 这个节点在本次任务里的作用`)}
                >
                  {getAgentLabel(item)}
                </button>
              ))}
            </div>
          </div>

          <div className="meta-group">
            <span className="meta-label">已用工具</span>
            <div className="tag-list inset-cluster">
              {usedTools.length > 0 ? (
                usedTools.map((item) => (
                  <button
                    type="button"
                    key={item}
                    className="tag-button subtle"
                    onClick={() => onRun(`解释工具 ${getToolLabel(item)} 的结果，并给出下一步建议`)}
                  >
                    {getToolLabel(item)}
                  </button>
                ))
              ) : (
                <button
                  type="button"
                  className="tag-button subtle disabled-tag"
                  onClick={() => onFill("请解释为什么本轮任务没有触发工具调用")}
                >
                  无工具
                </button>
              )}
            </div>
          </div>

          <div className="meta-group">
            <span className="meta-label">工具耗时</span>
            <div className="tool-metrics inset-metrics">
              {toolDetails.length > 0 ? (
                toolDetails.map((detail, index) => (
                  <button
                    type="button"
                    key={`${detail.tool_name}-${index}`}
                    className="tool-metric-card clickable-metric"
                    onClick={() => onFill(`请解释工具 ${getToolLabel(detail.tool_name)} 的执行结果和耗时表现`)}
                  >
                    <strong>{getToolLabel(detail.tool_name)}</strong>
                    <span>{resolveLatency(detail)}</span>
                    <small>{getStatusLabel(detail.status)}</small>
                  </button>
                ))
              ) : (
                <button
                  type="button"
                  className="tag-button subtle disabled-tag"
                  onClick={() => onFill("本轮没有工具耗时数据，请说明原因")}
                >
                  无工具调用
                </button>
              )}
            </div>
          </div>

          <div className="meta-group">
            <span className="meta-label">执行日志</span>
            <ul className="log-list interactive-log-list inset-log-list">
              {logs.map((item) => (
                <li key={item}>
                  <button
                    type="button"
                    className="log-action"
                    onClick={() => onFill(`基于这条执行日志继续说明：${item}`)}
                  >
                    {item}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <div className="collapsed-panel-placeholder">
          <span className="hint-text">已收起执行面板</span>
        </div>
      )}
    </section>
  );
}
