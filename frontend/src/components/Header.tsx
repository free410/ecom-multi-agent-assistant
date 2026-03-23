import type { ModelProvider, ProviderStatus } from "../types";

interface HeaderProps {
  provider: ModelProvider;
  onProviderChange: (provider: ModelProvider) => void;
  providerStatus: ProviderStatus | null;
  lastProviderUsed?: string | null;
  sessionId: string;
}

async function copySessionId(sessionId: string) {
  try {
    await navigator.clipboard.writeText(sessionId);
  } catch {
    // Ignore clipboard failures in demo mode.
  }
}

function getProviderHint(provider: ModelProvider, providerStatus: ProviderStatus | null) {
  if (!providerStatus) {
    return "正在读取 provider 状态...";
  }

  if (provider === "mock") {
    return "Mock 始终可用，适合本地演示。";
  }

  if (providerStatus.available) {
    return `${providerStatus.display_name} 已配置，可直接调用。`;
  }

  return `${providerStatus.display_name} 未配置，将自动回退到 Mock。`;
}

export function Header({
  provider,
  onProviderChange,
  providerStatus,
  lastProviderUsed,
  sessionId,
}: HeaderProps) {
  const providerHint = getProviderHint(provider, providerStatus);

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">AI Application MVP</p>
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
          <small className="provider-hint">{providerHint}</small>
          {lastProviderUsed ? <small className="provider-used">最近一次实际使用: {lastProviderUsed}</small> : null}
        </label>
        <button className="session-chip session-chip-button" onClick={() => void copySessionId(sessionId)}>
          <span>当前会话</span>
          <strong>{sessionId.slice(0, 12)}</strong>
          <small>点击复制 session_id</small>
        </button>
      </div>
    </header>
  );
}
