import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "../components/ChatMessage";
import { ExamplePrompts } from "../components/ExamplePrompts";
import { ExecutionPanel } from "../components/ExecutionPanel";
import { Header } from "../components/Header";
import { SessionList } from "../components/SessionList";
import { StructuredResultPanel } from "../components/StructuredResultPanel";
import { WorkflowToolPanel } from "../components/WorkflowToolPanel";
import { useChat } from "../hooks/useChat";
import type { ExampleTask } from "../types";

interface DisplayMessage {
  id: string;
  role: string;
  content: string;
  streaming?: boolean;
}

const DEFAULT_TASKS: ExampleTask[] = [
  {
    title: "618 活动文案",
    description: "围绕商品卖点和目标人群生成可投放的促销文案。",
    prompt: "根据云萃保温咖啡杯的卖点生成618促销文案",
    intent: "campaign_copy",
  },
  {
    title: "差评关键词提炼",
    description: "总结最近 7 天评论里的高频负面反馈和风险点。",
    prompt: "总结云萃保温咖啡杯最近7天差评关键词",
    intent: "review_summary",
  },
  {
    title: "客服安抚回复",
    description: "针对物流或售后问题生成更自然的客服建议话术。",
    prompt: "针对云萃保温咖啡杯用户反馈“发货慢”生成客服回复建议",
    intent: "customer_support",
  },
  {
    title: "竞品对比整理",
    description: "输出结构化竞品差异，方便做运营对标和卖点定位。",
    prompt: "整理云萃保温咖啡杯与竞品的差异",
    intent: "competitor_compare",
  },
  {
    title: "今日运营日报",
    description: "基于任务结果和运营数据生成简洁日报。",
    prompt: "生成今天的运营日报",
    intent: "daily_report",
  },
  {
    title: "商品知识问答",
    description: "快速回答商品卖点、适用人群和 FAQ 问题。",
    prompt: "云萃保温咖啡杯适合哪些人群，有哪些卖点？",
    intent: "product_qa",
  },
];

function toDisplayMessages(history: Array<{ role: string; content: string }>): DisplayMessage[] {
  return history.map((item, index) => ({
    id: `${item.role}-${index}-${item.content.length}`,
    role: item.role,
    content: item.content,
  }));
}

export function HomePage() {
  const {
    sessionId,
    provider,
    setProvider,
    providerStatus,
    input,
    setInput,
    loading,
    booting,
    error,
    products,
    sessions,
    sessionDetail,
    lastResponse,
    sendMessage,
    selectSession,
    createNewSession,
    deleteSession,
    clearLocalCache,
  } = useChat();

  const chatHistoryRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const streamTimerRef = useRef<number | null>(null);
  const isAnimatingRef = useRef(false);

  const [quickActionHint, setQuickActionHint] = useState("");
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([]);
  const [animatingResponse, setAnimatingResponse] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  useEffect(() => {
    if (isAnimatingRef.current) {
      return;
    }
    setDisplayMessages(toDisplayMessages(sessionDetail.history));
  }, [sessionDetail.history, sessionId]);

  useEffect(() => {
    const container = chatHistoryRef.current;
    if (!container) {
      return;
    }

    const rafId = window.requestAnimationFrame(() => {
      container.scrollTop = container.scrollHeight;
    });

    return () => window.cancelAnimationFrame(rafId);
  }, [displayMessages, lastResponse]);

  useEffect(() => {
    if (!quickActionHint) {
      return;
    }

    const timer = window.setTimeout(() => setQuickActionHint(""), 2200);
    return () => window.clearTimeout(timer);
  }, [quickActionHint]);

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) {
        window.clearTimeout(streamTimerRef.current);
      }
    };
  }, []);

  const focusComposer = () => {
    const inputElement = inputRef.current;
    if (!inputElement) {
      return;
    }

    inputElement.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      inputElement.focus();
      const end = inputElement.value.length;
      inputElement.setSelectionRange(end, end);
    }, 120);
  };

  const stopStreaming = () => {
    if (streamTimerRef.current) {
      window.clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }
    isAnimatingRef.current = false;
    setAnimatingResponse(false);
  };

  const streamAssistantMessage = (content: string) =>
    new Promise<void>((resolve) => {
      const chars = Array.from(content);
      const assistantId = `assistant-${Date.now()}`;
      let index = 0;

      isAnimatingRef.current = true;
      setAnimatingResponse(true);
      setDisplayMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          streaming: true,
        },
      ]);

      const tick = () => {
        index += 1;
        const nextContent = chars.slice(0, index).join("");

        setDisplayMessages((prev) =>
          prev.map((item) =>
            item.id === assistantId
              ? {
                  ...item,
                  content: nextContent,
                  streaming: index < chars.length,
                }
              : item,
          ),
        );

        if (index < chars.length) {
          const currentChar = chars[index - 1] ?? "";
          const delay = ["，", "。", "？", "！", "\n"].includes(currentChar) ? 36 : 12;
          streamTimerRef.current = window.setTimeout(tick, delay);
        } else {
          stopStreaming();
          resolve();
        }
      };

      streamTimerRef.current = window.setTimeout(tick, 40);
    });

  const submitPrompt = async (prompt?: string) => {
    const finalPrompt = (prompt ?? input).trim();
    if (!finalPrompt || loading || animatingResponse) {
      return;
    }

    stopStreaming();
    setQuickActionHint("");
    setDisplayMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: finalPrompt,
      },
    ]);

    const response = await sendMessage(finalPrompt);
    if (!response) {
      isAnimatingRef.current = false;
      setAnimatingResponse(false);
      return;
    }

    await streamAssistantMessage(response.answer);
  };

  const handleRunPrompt = (prompt: string) => {
    setQuickActionHint("已直接执行该操作");
    void submitPrompt(prompt);
  };

  const handleFillPrompt = (prompt: string) => {
    setInput(prompt);
    setQuickActionHint("已填入输入框，可直接发送或继续编辑");
    focusComposer();
  };

  const handleProductClick = (productName: string) => {
    handleFillPrompt(`帮我分析 ${productName} 的核心卖点、适用人群和常见 FAQ`);
  };

  return (
    <div className="app-shell">
      <Header
        provider={provider}
        onProviderChange={setProvider}
        providerStatus={providerStatus}
        lastProviderUsed={lastResponse?.provider_used ?? null}
        sessionId={sessionId}
      />

      <main
        className={`layout-grid ${leftCollapsed ? "left-collapsed" : ""} ${
          rightCollapsed ? "right-collapsed" : ""
        }`}
      >
        <SessionList
          sessions={sessions}
          activeSessionId={sessionId}
          collapsed={leftCollapsed}
          onToggleCollapse={() => setLeftCollapsed((prev) => !prev)}
          onClearLocalCache={() => {
            stopStreaming();
            void clearLocalCache();
            setDisplayMessages([]);
          }}
          onSelect={async (targetSessionId) => {
            stopStreaming();
            await selectSession(targetSessionId);
          }}
          onCreate={() => {
            stopStreaming();
            createNewSession();
            setDisplayMessages([]);
          }}
          onDelete={(targetSessionId) => {
            const targetSession = sessions.find((item) => item.session_id === targetSessionId);
            const confirmed = window.confirm(
              `确认删除会话“${targetSession?.title ?? "未命名会话"}”吗？删除后将同时移除本地缓存与后端记录。`,
            );
            if (!confirmed) {
              return;
            }
            stopStreaming();
            void deleteSession(targetSessionId);
            if (targetSessionId === sessionId) {
              setDisplayMessages([]);
            }
          }}
        />

        <section className="panel chat-panel">
          <div className="panel-header">
            <h2>聊天区</h2>
            <span className="hint-text">
              支持商品问答、文案生成、客服回复、评论分析、竞品整理、日报生成
            </span>
          </div>

          <div className="product-strip">
            {products.slice(0, 6).map((product) => (
              <button
                key={product.id}
                type="button"
                className="product-pill product-button"
                onClick={() => handleProductClick(product.name)}
              >
                {product.name}
              </button>
            ))}
          </div>
          <p className="hint-text strip-hint">点击商品胶囊可快速填充问题，再修改后发送。</p>

          <ExamplePrompts tasks={DEFAULT_TASKS} onRun={handleRunPrompt} onFill={handleFillPrompt} />

          <div ref={chatHistoryRef} className="chat-history">
            {booting ? (
              <p className="empty-text">正在初始化 mock 数据和会话...</p>
            ) : displayMessages.length === 0 ? (
              <p className="empty-text">从上方示例任务卡片开始，或直接输入你的运营问题。</p>
            ) : (
              displayMessages.map((item) => (
                <ChatMessage
                  key={item.id}
                  role={item.role}
                  content={item.content}
                  streaming={Boolean(item.streaming)}
                />
              ))
            )}
          </div>

          <StructuredResultPanel result={lastResponse} onFill={handleFillPrompt} onRun={handleRunPrompt} />

          <div className="composer">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入你的问题，例如：总结这款产品最近 7 天差评关键词"
              rows={4}
            />
            <div className="composer-footer">
              <div className="composer-status">
                {error ? (
                  <span className="error-text">{error}</span>
                ) : animatingResponse || loading ? (
                  <span className="hint-text">AI 正在生成回复，消息会以打字机效果逐步显示。</span>
                ) : (
                  <span className="hint-text">保留 Markdown 回复，同时展示结构化结果</span>
                )}
                {quickActionHint ? <span className="quick-action-hint">{quickActionHint}</span> : null}
              </div>
              <button
                type="button"
                className="primary-button"
                disabled={loading || booting || animatingResponse}
                onClick={() => void submitPrompt()}
              >
                {loading || animatingResponse ? "生成中..." : "发送"}
              </button>
            </div>
          </div>
        </section>

        {rightCollapsed ? (
          <aside className="right-rail right-rail-collapsed">
            <section className="panel collapsed-sidebar collapsed-right-rail right-rail-panel">
              <button
                className="rail-handle right-handle"
                onClick={() => setRightCollapsed(false)}
                aria-label="展开右侧工作流栏"
                title="展开右侧工作流栏"
              >
                &lt;
              </button>
              <div className="collapsed-rail-icon">◎</div>
              <div className="collapsed-rail-count">
                {(lastResponse?.used_tools?.length ?? 0) > 0 ? `${lastResponse?.used_tools.length}` : "0"}
              </div>
            </section>
          </aside>
        ) : (
          <aside className="right-rail right-rail-panel">
            <button
              className="rail-handle right-handle"
              onClick={() => setRightCollapsed(true)}
              aria-label="收起右侧工作流栏"
              title="收起右侧工作流栏"
            >
              &gt;
            </button>
            <ExecutionPanel result={lastResponse} onFill={handleFillPrompt} onRun={handleRunPrompt} />
            <WorkflowToolPanel
              result={lastResponse}
              onFill={handleFillPrompt}
              onRun={handleRunPrompt}
              compact
            />
          </aside>
        )}
      </main>
    </div>
  );
}
