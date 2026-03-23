import { useState } from "react";
import type { ChatResponse } from "../types";

interface StructuredResultPanelProps {
  result: ChatResponse | null;
  onFill: (prompt: string) => void;
  onRun: (prompt: string) => void;
}

const asRecord = (value: unknown): Record<string, unknown> =>
  typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};

const asStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];

const asRecordArray = (value: unknown): Record<string, unknown>[] =>
  Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    : [];

async function copyText(text: string) {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // ignore
  }
}

function renderGeneralChat(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const prompts = asStringArray(result.suggested_prompts);

  return (
    <div className="structured-stack">
      <div className="structured-note">这里保留推荐追问，避免和上方 AI 完整回复重复。</div>
      <div className="prompt-action-grid">
        {prompts.map((prompt) => (
          <article key={prompt} className="result-card">
            <span className="result-label">推荐追问</span>
            <p>{prompt}</p>
            <div className="card-actions">
              <button className="mini-primary" onClick={() => onRun(prompt)}>
                立即执行
              </button>
              <button className="mini-ghost" onClick={() => onFill(prompt)}>
                填入输入框
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function renderClarification(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const missingFields = asStringArray(result.missing_fields);
  const question = String(result.question ?? "请补充更具体的信息");
  const fieldMap: Record<string, string> = {
    product_name: "商品名称",
    campaign_theme: "活动主题",
    audience: "目标人群",
  };

  return (
    <div className="structured-stack">
      <article className="result-card accent">
        <span className="result-label">当前缺失信息</span>
        <p>{question}</p>
        <div className="field-chip-list">
          {missingFields.map((field) => (
            <span key={field} className="field-chip">
              {fieldMap[field] || field}
            </span>
          ))}
        </div>
      </article>

      {missingFields.includes("product_name") ? (
        <div className="prompt-action-grid">
          {["云萃保温咖啡杯", "轻研便携榨汁杯", "晨露香氛豆乳杯"].map((product) => (
            <article key={product} className="result-card">
              <span className="result-label">快捷补充</span>
              <strong>{product}</strong>
              <div className="card-actions">
                <button className="mini-primary" onClick={() => onRun(product)}>
                  直接发送
                </button>
                <button className="mini-ghost" onClick={() => onFill(product)}>
                  填入输入框
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function renderProductQA(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const sellingPoints = asStringArray(result.selling_points);
  const targetUsers = asStringArray(result.target_users);
  const faqAnswer = String(result.faq_answer ?? "");
  const afterSalePolicy = String(result.after_sale_policy ?? "");
  const productName = String(result.product_name ?? "当前商品");

  return (
    <div className="structured-stack">
      <div className="structured-note">这里提炼成可复用的商品知识卡片，方便继续追问和二次生成。</div>
      <div className="structured-grid">
        <article className="result-card accent">
          <span className="result-label">商品</span>
          <strong>{productName}</strong>
          <div className="card-actions">
            <button className="mini-ghost" onClick={() => onFill(`基于 ${productName} 再补充 3 个适合详情页的卖点表达`)}>
              扩展卖点
            </button>
          </div>
        </article>

        <article className="result-card">
          <span className="result-label">适用人群</span>
          <ul className="compact-list">
            {targetUsers.length > 0 ? targetUsers.map((item) => <li key={item}>{item}</li>) : <li>暂无</li>}
          </ul>
        </article>

        <article className="result-card">
          <span className="result-label">核心卖点</span>
          <ul className="compact-list">
            {sellingPoints.length > 0 ? sellingPoints.map((item) => <li key={item}>{item}</li>) : <li>暂无</li>}
          </ul>
        </article>

        <article className="result-card">
          <span className="result-label">售后与 FAQ</span>
          <p>{faqAnswer || afterSalePolicy || "暂无可展示内容"}</p>
          <div className="card-actions">
            <button className="mini-primary" onClick={() => onRun(`基于 ${productName} 的售后规则生成一条标准客服回复模板`)}>
              生成客服模板
            </button>
          </div>
        </article>
      </div>
    </div>
  );
}

function renderCampaign(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const bullets = asStringArray(result.bullets);

  return (
    <div className="structured-grid">
      <article className="result-card accent">
        <span className="result-label">标题</span>
        <strong>{String(result.headline ?? "暂无标题")}</strong>
        <div className="card-actions">
          <button className="mini-primary" onClick={() => onFill(`请基于这个标题继续优化：${String(result.headline ?? "")}`)}>
            继续优化
          </button>
          <button className="mini-ghost" onClick={() => void copyText(String(result.headline ?? ""))}>
            复制标题
          </button>
        </div>
      </article>

      {bullets.map((item) => (
        <article key={item} className="result-card">
          <span className="result-label">卖点文案</span>
          <p>{item}</p>
          <div className="card-actions">
            <button className="mini-ghost" onClick={() => onFill(`把这句卖点扩写成详情页文案：${item}`)}>
              填入扩写
            </button>
          </div>
        </article>
      ))}

      <article className="result-card">
        <span className="result-label">行动号召</span>
        <p>{String(result.cta ?? "-")}</p>
        <div className="card-actions">
          <button className="mini-primary" onClick={() => onRun(`基于这组文案再生成 3 个行动号召版本：${String(result.cta ?? "")}`)}>
            再生成 3 个
          </button>
        </div>
      </article>
    </div>
  );
}

function renderReview(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const data = asRecord(result.data);
  const negativeKeywords = asRecord(data.negative_keywords);
  const keywords = asRecordArray(negativeKeywords.keywords);
  const recommendations = asStringArray(result.recommendations);
  const summaryText = asStringArray(result.highlights).join("；") || "暂无摘要";

  return (
    <div className="structured-stack">
      <div className="keyword-blocks">
        {keywords.length > 0 ? (
          keywords.map((item, index) => {
            const keyword = String(item.keyword ?? "-");
            return (
              <button
                key={`${keyword}-${index}`}
                className="keyword-chip clickable-chip"
                onClick={() => onRun(`针对“${keyword}”这个差评关键词生成客服安抚回复和详情页优化建议`)}
              >
                <strong>{keyword}</strong>
                <span>{String(item.count ?? 0)} 次</span>
              </button>
            );
          })
        ) : (
          <div className="keyword-chip empty">暂无高频关键词</div>
        )}
      </div>

      <article className="result-card">
        <span className="result-label">摘要</span>
        <p>{summaryText}</p>
        <div className="card-actions">
          <button className="mini-ghost" onClick={() => onFill(`把这段评论摘要改写成日报表达：${summaryText}`)}>
            改写成日报
          </button>
        </div>
      </article>

      <article className="result-card">
        <span className="result-label">建议</span>
        <ul className="compact-list">
          {recommendations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </div>
  );
}

function renderCompetitor(
  result: Record<string, unknown>,
  onFill: (prompt: string) => void,
  onRun: (prompt: string) => void,
) {
  const data = asRecord(result.data);
  const competitorCompare = asRecord(data.competitor_compare);
  const comparisons = asRecordArray(competitorCompare.comparisons);

  return (
    <div className="table-wrap">
      <table className="result-table">
        <thead>
          <tr>
            <th>竞品</th>
            <th>竞品亮点</th>
            <th>竞品弱点</th>
            <th>价格带</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {comparisons.map((item, index) => {
            const competitorName = String(item.competitor_name ?? "-");
            return (
              <tr key={`${competitorName}-${index}`}>
                <td>{competitorName}</td>
                <td>{asStringArray(item.competitor_highlights).join("、") || "-"}</td>
                <td>{asStringArray(item.competitor_weaknesses).join("、") || "-"}</td>
                <td>{String(item.price_range ?? "-")}</td>
                <td>
                  <button
                    className="table-action"
                    onClick={() => onRun(`基于 ${competitorName} 的差异，生成一版详情页对比卖点话术`)}
                  >
                    生成对比话术
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="table-footer-actions">
        <button className="mini-ghost" onClick={() => onFill("请把这份竞品对比整理成适合汇报的 bullet points")}>
          转成汇报提纲
        </button>
      </div>
    </div>
  );
}

function renderDailyReport(result: Record<string, unknown>, onFill: (prompt: string) => void) {
  const data = asRecord(result.data);
  const report = asRecord(data.daily_report);
  const overview = asRecord(report.overview);

  const sections = [
    {
      title: "核心概览",
      content: [
        `销售额：${String(overview.sales ?? "-")}`,
        `流量：${String(overview.traffic ?? "-")}`,
        `转化率：${String(overview.conversion_rate ?? "-")}`,
      ],
    },
    { title: "亮点", content: asStringArray(report.highlights) },
    { title: "风险", content: asStringArray(report.risks) },
    { title: "待办", content: asStringArray(report.pending_tasks) },
  ];

  return (
    <div className="report-grid">
      {sections.map((section) => (
        <article key={section.title} className="result-card">
          <span className="result-label">{section.title}</span>
          <ul className="compact-list">
            {section.content.length > 0 ? (
              section.content.map((item) => <li key={item}>{item}</li>)
            ) : (
              <li>暂无数据</li>
            )}
          </ul>
          <div className="card-actions">
            <button className="mini-ghost" onClick={() => onFill(`请基于日报中的 ${section.title} 部分继续展开分析`)}>
              继续展开
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

function renderFallback(structured: Record<string, unknown>) {
  const keys = Object.keys(structured);

  return (
    <div className="structured-stack">
      <div className="structured-note">这里展示的是结构化字段摘要，原始 JSON 已收起，避免和上方 AI 回复重复。</div>
      <article className="result-card">
        <span className="result-label">结构化字段</span>
        <div className="field-chip-list">
          {keys.map((key) => (
            <span key={key} className="field-chip">
              {key}
            </span>
          ))}
        </div>
      </article>
    </div>
  );
}

export function StructuredResultPanel({ result, onFill, onRun }: StructuredResultPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (!result) {
    return null;
  }

  const structured = asRecord(result.structured_result);
  if (Object.keys(structured).length === 0) {
    return null;
  }

  return (
    <section className={`panel structured-panel collapsible-panel ${collapsed ? "is-collapsed" : ""}`}>
      <div className="panel-header">
        <h2>结构化结果</h2>
        <div className="panel-header-actions">
          {!collapsed ? <span className="hint-text">这里偏向卡片和下一步操作，不重复展示上方完整回复</span> : null}
          <button
            type="button"
            className={`collapse-arrow ${collapsed ? "is-collapsed" : ""}`}
            onClick={() => setCollapsed((prev) => !prev)}
            aria-label={collapsed ? "展开结构化结果" : "收起结构化结果"}
            title={collapsed ? "展开" : "收起"}
          >
            &gt;
          </button>
        </div>
      </div>

      {!collapsed ? (
        <>
          {result.intent === "general_chat" && renderGeneralChat(structured, onFill, onRun)}
          {structured.agent === "ClarificationNode" && renderClarification(structured, onFill, onRun)}
          {result.intent === "product_qa" && renderProductQA(structured, onFill, onRun)}
          {result.intent === "campaign_copy" && renderCampaign(structured, onFill, onRun)}
          {result.intent === "review_summary" && renderReview(structured, onFill, onRun)}
          {result.intent === "competitor_compare" && renderCompetitor(structured, onFill, onRun)}
          {result.intent === "daily_report" && renderDailyReport(structured, onFill)}
          {![
            "general_chat",
            "product_qa",
            "campaign_copy",
            "review_summary",
            "competitor_compare",
            "daily_report",
          ].includes(result.intent) &&
            structured.agent !== "ClarificationNode" &&
            renderFallback(structured)}

          <details className="raw-json-details">
            <summary>查看原始结构化数据</summary>
            <pre className="json-preview">{JSON.stringify(structured, null, 2)}</pre>
          </details>
        </>
      ) : (
        <div className="collapsed-panel-placeholder">
          <span className="hint-text">已收起结构化结果</span>
        </div>
      )}
    </section>
  );
}
