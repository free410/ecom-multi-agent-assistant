import axios from "axios";
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type {
  ChatResponse,
  HealthResponse,
  ModelProvider,
  Product,
  SessionDetail,
  SessionSummary,
} from "../types";

const ACTIVE_SESSION_KEY = "ecom-assistant-active-session-id";
const ACTIVE_PROVIDER_KEY = "ecom-assistant-active-provider";
const SESSION_LIST_CACHE_KEY = "ecom-assistant-session-list-cache";
const SESSION_DETAIL_CACHE_KEY = "ecom-assistant-session-detail-cache";

type SessionDetailCacheMap = Record<string, SessionDetail>;

const createSessionId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}`;
};

function getStoredSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(ACTIVE_SESSION_KEY);
  return value && value.trim() ? value : null;
}

function getStoredProvider(): ModelProvider {
  if (typeof window === "undefined") {
    return "mock";
  }
  const value = window.localStorage.getItem(ACTIVE_PROVIDER_KEY);
  if (value === "qwen" || value === "deepseek" || value === "mock") {
    return value;
  }
  return "mock";
}

function persistSessionId(sessionId: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
}

function persistProvider(provider: ModelProvider) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACTIVE_PROVIDER_KEY, provider);
}

function normalizeChatResponse(result: ChatResponse | null): ChatResponse | null {
  if (!result) {
    return null;
  }

  return {
    ...result,
    logs: Array.isArray(result.logs) ? result.logs : [],
    used_tools: Array.isArray(result.used_tools) ? result.used_tools : [],
    agent_path: Array.isArray(result.agent_path) ? result.agent_path : [],
    provider_used: result.provider_used || "unknown",
    structured_result:
      result.structured_result && typeof result.structured_result === "object"
        ? result.structured_result
        : {},
    confidence: typeof result.confidence === "number" ? result.confidence : 0,
    routing_reason: result.routing_reason || "",
    memory_used: result.memory_used ?? {
      short_term_memory: false,
      preference_memory: false,
    },
    restored_fields: Array.isArray(result.restored_fields) ? result.restored_fields : [],
    tool_details: Array.isArray(result.tool_details) ? result.tool_details : [],
  };
}

function normalizeSessionSummary(item: SessionSummary): SessionSummary {
  return {
    session_id: item.session_id,
    title: item.title || "新会话",
    last_intent: item.last_intent ?? null,
    updated_at: item.updated_at ?? null,
  };
}

function normalizeSessionDetail(detail: SessionDetail, sessionId?: string): SessionDetail {
  return {
    session_id: detail.session_id || sessionId || "",
    history: Array.isArray(detail.history)
      ? detail.history.filter(
          (item) =>
            item &&
            typeof item.role === "string" &&
            typeof item.content === "string" &&
            item.content.trim().length > 0,
        )
      : [],
    last_result: normalizeChatResponse(detail.last_result),
  };
}

function safeParse<T>(value: string | null, fallback: T): T {
  if (!value) {
    return fallback;
  }
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

function getCachedSessions(): SessionSummary[] {
  if (typeof window === "undefined") {
    return [];
  }
  const parsed = safeParse<SessionSummary[]>(window.localStorage.getItem(SESSION_LIST_CACHE_KEY), []);
  return parsed
    .filter((item) => item && typeof item.session_id === "string" && item.session_id.trim())
    .map(normalizeSessionSummary);
}

function persistSessions(sessions: SessionSummary[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(SESSION_LIST_CACHE_KEY, JSON.stringify(sessions));
}

function getCachedSessionDetailMap(): SessionDetailCacheMap {
  if (typeof window === "undefined") {
    return {};
  }
  const parsed = safeParse<Record<string, SessionDetail>>(
    window.localStorage.getItem(SESSION_DETAIL_CACHE_KEY),
    {},
  );
  const normalized: SessionDetailCacheMap = {};
  for (const [key, value] of Object.entries(parsed)) {
    normalized[key] = normalizeSessionDetail(value, key);
  }
  return normalized;
}

function getCachedSessionDetail(sessionId: string): SessionDetail | null {
  const cacheMap = getCachedSessionDetailMap();
  return cacheMap[sessionId] ?? null;
}

function persistSessionDetail(detail: SessionDetail) {
  if (typeof window === "undefined" || !detail.session_id) {
    return;
  }
  const cacheMap = getCachedSessionDetailMap();
  cacheMap[detail.session_id] = normalizeSessionDetail(detail, detail.session_id);
  window.localStorage.setItem(SESSION_DETAIL_CACHE_KEY, JSON.stringify(cacheMap));
}

function deleteCachedSessionDetail(sessionId: string) {
  if (typeof window === "undefined") {
    return;
  }
  const cacheMap = getCachedSessionDetailMap();
  delete cacheMap[sessionId];
  window.localStorage.setItem(SESSION_DETAIL_CACHE_KEY, JSON.stringify(cacheMap));
}

function clearSessionCaches() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(SESSION_LIST_CACHE_KEY);
  window.localStorage.removeItem(SESSION_DETAIL_CACHE_KEY);
  window.localStorage.removeItem(ACTIVE_SESSION_KEY);
}

function mergeSessions(remote: SessionSummary[], cached: SessionSummary[]): SessionSummary[] {
  const merged = new Map<string, SessionSummary>();

  for (const item of cached) {
    merged.set(item.session_id, normalizeSessionSummary(item));
  }

  for (const item of remote) {
    const existing = merged.get(item.session_id);
    merged.set(item.session_id, normalizeSessionSummary({ ...existing, ...item }));
  }

  return Array.from(merged.values()).sort((a, b) => {
    const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
    const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
    return timeB - timeA;
  });
}

function deriveSessionSummary(
  sessionId: string,
  history: Array<{ role: string; content: string }>,
  lastResult: ChatResponse | null,
  previous?: SessionSummary | null,
): SessionSummary {
  const firstUserMessage = history.find((item) => item.role === "user")?.content?.trim();
  return normalizeSessionSummary({
    session_id: sessionId,
    title: firstUserMessage?.slice(0, 30) || previous?.title || "新会话",
    last_intent: lastResult?.intent || previous?.last_intent || null,
    updated_at: new Date().toISOString(),
  });
}

function mergeSessionDetail(
  sessionId: string,
  remote: SessionDetail | null,
  cached: SessionDetail | null,
): SessionDetail {
  const normalizedRemote = remote ? normalizeSessionDetail(remote, sessionId) : null;
  const normalizedCached = cached ? normalizeSessionDetail(cached, sessionId) : null;

  const useRemoteHistory = Boolean(normalizedRemote?.history?.length);
  const useRemoteLastResult = Boolean(normalizedRemote?.last_result);

  return {
    session_id: sessionId,
    history: useRemoteHistory ? normalizedRemote!.history : normalizedCached?.history ?? [],
    last_result: useRemoteLastResult
      ? normalizedRemote!.last_result
      : normalizedCached?.last_result ?? null,
  };
}

function getReadableErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      return "请求等待时间过长，请稍后重试或检查模型服务状态。";
    }
    if (err.message === "Network Error") {
      return "网络连接失败，请确认后端服务已经启动。";
    }
    if (typeof err.response?.data === "object" && err.response?.data && "detail" in err.response.data) {
      const detail = (err.response.data as { detail?: unknown }).detail;
      if (typeof detail === "string" && detail.trim()) {
        return detail;
      }
    }
    if (err.response?.status) {
      return `请求失败，状态码 ${err.response.status}。`;
    }
  }

  if (err instanceof Error && err.message) {
    return err.message;
  }

  return "发送消息失败。";
}

export function useChat() {
  const initialSessionId = getStoredSessionId() ?? createSessionId();
  const initialCachedDetail = getCachedSessionDetail(initialSessionId);

  const [sessionId, setSessionIdState] = useState<string>(initialSessionId);
  const [provider, setProviderState] = useState<ModelProvider>(() => getStoredProvider());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>(() => getCachedSessions());
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail>(
    initialCachedDetail ?? {
      session_id: initialSessionId,
      history: [],
      last_result: null,
    },
  );
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(
    normalizeChatResponse(initialCachedDetail?.last_result ?? null),
  );

  const setSessionId = (nextSessionId: string) => {
    setSessionIdState(nextSessionId);
    persistSessionId(nextSessionId);
  };

  const setProvider = (nextProvider: ModelProvider) => {
    setProviderState(nextProvider);
    persistProvider(nextProvider);
  };

  const updateSessionsState = (nextSessions: SessionSummary[]) => {
    setSessions(nextSessions);
    persistSessions(nextSessions);
  };

  const updateSessionDetailState = (detail: SessionDetail) => {
    const normalizedDetail = normalizeSessionDetail(detail, detail.session_id);
    setSessionDetail(normalizedDetail);
    setLastResponse(normalizeChatResponse(normalizedDetail.last_result));
    persistSessionDetail(normalizedDetail);
  };

  const upsertSessionSummary = (
    targetSessionId: string,
    history: Array<{ role: string; content: string }>,
    result: ChatResponse | null,
  ) => {
    setSessions((prev) => {
      const previous = prev.find((item) => item.session_id === targetSessionId) ?? null;
      const summary = deriveSessionSummary(targetSessionId, history, result, previous);
      const next = mergeSessions([summary], prev);
      persistSessions(next);
      return next;
    });
  };

  const refreshSessions = async () => {
    const remoteSessions = await apiClient.getSessions();
    const mergedSessions = mergeSessions(remoteSessions, getCachedSessions());
    updateSessionsState(mergedSessions);
    return mergedSessions;
  };

  const refreshHealth = async () => {
    const next = await apiClient.getHealth();
    setHealth(next);
    return next;
  };

  const refreshSessionDetail = async (targetSessionId: string) => {
    const cachedDetail = getCachedSessionDetail(targetSessionId);
    try {
      const remoteDetail = await apiClient.getSession(targetSessionId);
      const mergedDetail = mergeSessionDetail(targetSessionId, remoteDetail, cachedDetail);
      updateSessionDetailState(mergedDetail);
      upsertSessionSummary(targetSessionId, mergedDetail.history, mergedDetail.last_result);
      return mergedDetail;
    } catch (err) {
      if (cachedDetail) {
        updateSessionDetailState(cachedDetail);
        upsertSessionSummary(targetSessionId, cachedDetail.history, cachedDetail.last_result);
        return cachedDetail;
      }
      throw err;
    }
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        setBooting(true);
        const cachedSessions = getCachedSessions();
        if (cachedSessions.length > 0) {
          updateSessionsState(cachedSessions);
        }

        await apiClient.initSeed();

        const [productList, remoteSessions, nextHealth] = await Promise.all([
          apiClient.getProducts(),
          apiClient.getSessions().catch(() => []),
          apiClient.getHealth().catch(() => null),
        ]);

        setProducts(productList);
        if (nextHealth) {
          setHealth(nextHealth);
        }

        const mergedSessions = mergeSessions(remoteSessions, getCachedSessions());
        updateSessionsState(mergedSessions);

        const storedSessionId = getStoredSessionId();
        const cachedDetailMap = getCachedSessionDetailMap();
        const cachedSessionIds = Object.keys(cachedDetailMap);

        const preferredSessionId =
          (storedSessionId &&
            (mergedSessions.some((item) => item.session_id === storedSessionId) ||
              Boolean(cachedDetailMap[storedSessionId])) &&
            storedSessionId) ||
          mergedSessions[0]?.session_id ||
          cachedSessionIds[0] ||
          initialSessionId;

        if (preferredSessionId !== sessionId) {
          setSessionId(preferredSessionId);
        } else if (preferredSessionId) {
          try {
            await refreshSessionDetail(preferredSessionId);
          } catch {
            const cachedDetail = getCachedSessionDetail(preferredSessionId);
            if (cachedDetail) {
              updateSessionDetailState(cachedDetail);
            }
          }
        }
      } catch (err) {
        setError(getReadableErrorMessage(err));
      } finally {
        setBooting(false);
      }
    };

    void bootstrap();
  }, []);

  useEffect(() => {
    persistSessionId(sessionId);
  }, [sessionId]);

  useEffect(() => {
    persistProvider(provider);
  }, [provider]);

  useEffect(() => {
    const cachedDetail = getCachedSessionDetail(sessionId);
    if (cachedDetail) {
      updateSessionDetailState(cachedDetail);
    } else {
      setSessionDetail({ session_id: sessionId, history: [], last_result: null });
      setLastResponse(null);
    }

    const loadSession = async () => {
      try {
        setError(null);
        await refreshSessionDetail(sessionId);
      } catch {
        if (!cachedDetail) {
          setSessionDetail({ session_id: sessionId, history: [], last_result: null });
          setLastResponse(null);
        }
      }
    };

    if (!sessionId) {
      return;
    }

    void loadSession();
  }, [sessionId]);

  const sendMessage = async (message?: string) => {
    const finalMessage = (message ?? input).trim();
    if (!finalMessage) {
      return null;
    }

    const previousSessions = [...sessions];
    const previousDetail = sessionDetail;
    const previousLastResponse = lastResponse;

    try {
      setLoading(true);
      setError(null);

      const userHistory = [...sessionDetail.history, { role: "user", content: finalMessage }];
      const provisionalSummary = deriveSessionSummary(
        sessionId,
        userHistory,
        lastResponse,
        sessions.find((item) => item.session_id === sessionId) ?? null,
      );
      updateSessionsState(mergeSessions([provisionalSummary], sessions));

      const response = await apiClient.sendChat({
        session_id: sessionId,
        message: finalMessage,
        model_provider: provider,
      });
      const normalizedResponse = normalizeChatResponse(response);
      const nextDetail: SessionDetail = {
        session_id: sessionId,
        history: [...userHistory, { role: "assistant", content: normalizedResponse?.answer ?? "" }],
        last_result: normalizedResponse,
      };

      updateSessionDetailState(nextDetail);
      upsertSessionSummary(sessionId, nextDetail.history, normalizedResponse);
      setInput("");

      await Promise.allSettled([refreshSessionDetail(sessionId), refreshSessions(), refreshHealth()]);
      persistSessionId(sessionId);
      return normalizedResponse;
    } catch (err) {
      updateSessionsState(previousSessions);
      setSessionDetail(previousDetail);
      setLastResponse(previousLastResponse);
      persistSessionDetail(previousDetail);
      setError(getReadableErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  };

  const selectSession = async (targetSessionId: string) => {
    setSessionId(targetSessionId);
    const cachedDetail = getCachedSessionDetail(targetSessionId);
    if (cachedDetail) {
      updateSessionDetailState(cachedDetail);
    }
    await refreshSessionDetail(targetSessionId);
  };

  const createNewSession = () => {
    const next = createSessionId();
    setSessionId(next);
    setSessionDetail({ session_id: next, history: [], last_result: null });
    setLastResponse(null);
    setInput("");
  };

  const deleteSession = async (targetSessionId: string) => {
    try {
      setError(null);
      await apiClient.deleteSession(targetSessionId);

      deleteCachedSessionDetail(targetSessionId);

      const nextSessions = sessions.filter((item) => item.session_id !== targetSessionId);
      updateSessionsState(nextSessions);

      if (targetSessionId === sessionId) {
        const fallbackSessionId = nextSessions[0]?.session_id ?? createSessionId();
        setSessionId(fallbackSessionId);

        const fallbackDetail = getCachedSessionDetail(fallbackSessionId);
        if (fallbackDetail) {
          updateSessionDetailState(fallbackDetail);
        } else {
          setSessionDetail({ session_id: fallbackSessionId, history: [], last_result: null });
          setLastResponse(null);
        }
      }
    } catch (err) {
      setError(getReadableErrorMessage(err));
    }
  };

  const clearLocalCache = async () => {
    clearSessionCaches();
    updateSessionsState([]);
    setSessionDetail({ session_id: sessionId, history: [], last_result: null });
    setLastResponse(null);

    try {
      const mergedSessions = await refreshSessions();
      const fallbackSessionId = mergedSessions[0]?.session_id ?? createSessionId();
      setSessionId(fallbackSessionId);
      if (mergedSessions.length > 0) {
        await refreshSessionDetail(fallbackSessionId);
      }
    } catch {
      const next = createSessionId();
      setSessionId(next);
      setSessionDetail({ session_id: next, history: [], last_result: null });
      setLastResponse(null);
    }
  };

  const providerStatus = health?.providers?.[provider] ?? null;

  return {
    sessionId,
    provider,
    setProvider,
    providerStatus,
    health,
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
  };
}
