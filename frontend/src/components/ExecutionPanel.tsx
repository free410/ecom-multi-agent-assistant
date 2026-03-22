import type { ChatResponse } from "../types";

interface ExecutionPanelProps {
  result: ChatResponse | null;
}

export function ExecutionPanel({ result }: ExecutionPanelProps) {
  return (
    <section className="panel execution-panel">
      <div className="panel-header">
        <h2>执行面板</h2>
      </div>
      {!result ? (
        <p className="empty-text">发送消息后，这里会展示 intent、agent path、tools 和执行日志。</p>
      ) : (
        <div className="execution-content">
          <div className="meta-group">
            <span className="meta-label">Intent</span>
            <strong>{result.intent}</strong>
          </div>
          <div className="meta-group">
            <span className="meta-label">Provider</span>
            <strong>{result.provider_used}</strong>
          </div>
          <div className="meta-group">
            <span className="meta-label">Agent Path</span>
            <div className="tag-list">
              {result.agent_path.map((item) => (
                <span key={item} className="tag">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div className="meta-group">
            <span className="meta-label">Used Tools</span>
            <div className="tag-list">
              {result.used_tools.map((item) => (
                <span key={item} className="tag subtle">
                  {item}
                </span>
              ))}
            </div>
          </div>
          <div className="meta-group">
            <span className="meta-label">Logs</span>
            <ul className="log-list">
              {result.logs.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}

