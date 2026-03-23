import { useState } from "react";
import type { ExampleTask } from "../types";

interface ExamplePromptsProps {
  tasks: ExampleTask[];
  onRun: (prompt: string) => void;
  onFill: (prompt: string) => void;
}

export function ExamplePrompts({ tasks, onRun, onFill }: ExamplePromptsProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <section className={`panel examples-panel collapsible-panel ${collapsed ? "is-collapsed" : ""}`}>
      <div className="panel-header">
        <h2>示例任务卡片</h2>
        <div className="panel-header-actions">
          {!collapsed ? <span className="hint-text">点击立即执行，或先填入输入框后再编辑</span> : null}
          <button
            type="button"
            className={`collapse-arrow ${collapsed ? "is-collapsed" : ""}`}
            onClick={() => setCollapsed((prev) => !prev)}
            aria-label={collapsed ? "展开示例任务卡片" : "收起示例任务卡片"}
            title={collapsed ? "展开" : "收起"}
          >
            &gt;
          </button>
        </div>
      </div>

      {!collapsed ? (
        <div className="task-card-grid">
          {tasks.map((task) => (
            <article key={task.prompt} className="task-card">
              <span className="task-intent">{task.intent}</span>
              <strong>{task.title}</strong>
              <p>{task.description}</p>
              <div className="card-actions">
                <button className="mini-primary" onClick={() => onRun(task.prompt)}>
                  立即执行
                </button>
                <button className="mini-ghost" onClick={() => onFill(task.prompt)}>
                  填入输入框
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="collapsed-panel-placeholder">
          <span className="hint-text">已收起示例任务卡片</span>
        </div>
      )}
    </section>
  );
}
