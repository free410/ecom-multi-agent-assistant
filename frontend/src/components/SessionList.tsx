import type { SessionSummary } from "../types";

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelect: (sessionId: string) => void;
  onCreate: () => void;
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
}: SessionListProps) {
  return (
    <section className="panel sidebar">
      <div className="panel-header">
        <h2>会话列表</h2>
        <button className="ghost-button" onClick={onCreate}>
          新建
        </button>
      </div>
      <div className="session-list">
        {sessions.length === 0 ? (
          <p className="empty-text">还没有历史会话，先发一条消息吧。</p>
        ) : (
          sessions.map((item) => (
            <button
              key={item.session_id}
              className={`session-item ${item.session_id === activeSessionId ? "active" : ""}`}
              onClick={() => onSelect(item.session_id)}
            >
              <strong>{item.title}</strong>
              <span>{item.last_intent || "未执行"}</span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

