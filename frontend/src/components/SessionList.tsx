import type { SessionSummary } from "../types";

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelect: (sessionId: string) => void;
  onCreate: () => void;
  onDelete: (sessionId: string) => void;
  onClearLocalCache: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  onDelete,
  onClearLocalCache,
  collapsed,
  onToggleCollapse,
}: SessionListProps) {
  if (collapsed) {
    return (
      <section className="panel sidebar collapsed-sidebar left-rail-panel">
        <button
          className="rail-handle left-handle"
          onClick={onToggleCollapse}
          aria-label="展开左侧会话栏"
          title="展开左侧会话栏"
        >
          &gt;
        </button>
        <div className="collapsed-rail-icon">▤</div>
        <div className="collapsed-rail-count">{sessions.length}</div>
      </section>
    );
  }

  return (
    <section className="panel sidebar left-rail-panel">
      <button
        className="rail-handle left-handle"
        onClick={onToggleCollapse}
        aria-label="收起左侧会话栏"
        title="收起左侧会话栏"
      >
        &lt;
      </button>

      <div className="session-sidebar-header">
        <div className="session-sidebar-title">
          <h2>会话列表</h2>
          <span className="hint-text">保留最近会话，刷新后自动恢复</span>
        </div>

        <div className="session-toolbar">
          <button className="ghost-button compact-ghost-button" onClick={onClearLocalCache} type="button">
            清缓存
          </button>
          <button className="ghost-button compact-ghost-button" onClick={onCreate} type="button">
            新建
          </button>
        </div>
      </div>

      <div className="session-list">
        {sessions.length === 0 ? (
          <p className="empty-text">还没有历史会话，先发送一条消息开始体验。</p>
        ) : (
          sessions.map((item, index) => (
            <div
              key={item.session_id}
              className={`session-item session-card ${item.session_id === activeSessionId ? "active" : ""}`}
            >
              <button type="button" className="session-main" onClick={() => onSelect(item.session_id)}>
                <div className="session-title-row">
                  <strong className="session-title-text">{item.title}</strong>
                  {index === 0 ? <span className="session-badge">最近</span> : null}
                </div>
                <div className="session-meta-row">
                  <span className="session-intent-pill">{item.last_intent || "未执行"}</span>
                </div>
              </button>

              <button
                type="button"
                className="session-delete"
                title="删除会话"
                aria-label={`删除会话 ${item.title}`}
                onClick={() => onDelete(item.session_id)}
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
