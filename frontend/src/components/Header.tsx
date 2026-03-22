import type { ModelProvider } from "../types";

interface HeaderProps {
  provider: ModelProvider;
  onProviderChange: (provider: ModelProvider) => void;
  sessionId: string;
}

export function Header({ provider, onProviderChange, sessionId }: HeaderProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">AI 应用开发 MVP</p>
        <h1>多 Agent 电商运营智能助手平台</h1>
        <p className="subtext">LangGraph + FastAPI + React + Redis/MySQL 降级可运行</p>
      </div>
      <div className="toolbar">
        <label className="provider-box">
          <span>模型 Provider</span>
          <select
            value={provider}
            onChange={(event) => onProviderChange(event.target.value as ModelProvider)}
          >
            <option value="qwen">Qwen</option>
            <option value="deepseek">DeepSeek</option>
            <option value="mock">Mock</option>
          </select>
        </label>
        <div className="session-chip">
          <span>当前会话</span>
          <strong>{sessionId.slice(0, 12)}</strong>
        </div>
      </div>
    </header>
  );
}

