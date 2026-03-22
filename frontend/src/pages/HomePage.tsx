import { ChatMessage } from "../components/ChatMessage";
import { ExamplePrompts } from "../components/ExamplePrompts";
import { ExecutionPanel } from "../components/ExecutionPanel";
import { Header } from "../components/Header";
import { SessionList } from "../components/SessionList";
import { useChat } from "../hooks/useChat";

const DEFAULT_EXAMPLES = [
  "根据云萃保温咖啡杯的卖点生成618促销文案",
  "总结云萃保温咖啡杯最近7天差评关键词",
  "针对云萃保温咖啡杯用户反馈“发货慢”生成客服回复建议",
  "整理云萃保温咖啡杯与竞品的差异",
  "生成今天的运营日报",
];

export function HomePage() {
  const {
    sessionId,
    provider,
    setProvider,
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
  } = useChat();

  return (
    <div className="app-shell">
      <Header provider={provider} onProviderChange={setProvider} sessionId={sessionId} />

      <main className="layout-grid">
        <SessionList
          sessions={sessions}
          activeSessionId={sessionId}
          onSelect={selectSession}
          onCreate={createNewSession}
        />

        <section className="panel chat-panel">
          <div className="panel-header">
            <h2>聊天区</h2>
            <span className="hint-text">支持商品问答、文案生成、客服回复、评论分析、竞品整理、日报生成</span>
          </div>

          <div className="product-strip">
            {products.slice(0, 6).map((product) => (
              <span key={product.id} className="product-pill">
                {product.name}
              </span>
            ))}
          </div>

          <div className="chat-history">
            {booting ? (
              <p className="empty-text">正在初始化 mock 数据和会话...</p>
            ) : sessionDetail.history.length === 0 ? (
              <p className="empty-text">从右下示例问题开始，或直接输入你的运营问题。</p>
            ) : (
              sessionDetail.history.map((item, index) => (
                <ChatMessage key={`${item.role}-${index}`} role={item.role} content={item.content} />
              ))
            )}
          </div>

          <div className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入你的问题，例如：总结这款产品最近7天差评关键词"
              rows={4}
            />
            <div className="composer-footer">
              {error ? <span className="error-text">{error}</span> : <span className="hint-text">支持 Markdown 展示</span>}
              <button className="primary-button" disabled={loading || booting} onClick={() => void sendMessage()}>
                {loading ? "生成中..." : "发送"}
              </button>
            </div>
          </div>

          <ExamplePrompts prompts={DEFAULT_EXAMPLES} onSelect={(prompt) => void sendMessage(prompt)} />
        </section>

        <ExecutionPanel result={lastResponse} />
      </main>
    </div>
  );
}

