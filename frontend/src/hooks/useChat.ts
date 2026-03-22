import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type {
  ChatResponse,
  ModelProvider,
  Product,
  SessionDetail,
  SessionSummary,
} from "../types";

const createSessionId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}`;
};

export function useChat() {
  const [sessionId, setSessionId] = useState<string>(createSessionId());
  const [provider, setProvider] = useState<ModelProvider>("mock");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail>({
    session_id: sessionId,
    history: [],
    last_result: null,
  });
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  const refreshSessions = async () => {
    const next = await apiClient.getSessions();
    setSessions(next);
  };

  const refreshSessionDetail = async (targetSessionId: string) => {
    const detail = await apiClient.getSession(targetSessionId);
    setSessionDetail(detail);
    setLastResponse(detail.last_result);
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        setBooting(true);
        await apiClient.initSeed();
        const [productList] = await Promise.all([apiClient.getProducts(), refreshSessions()]);
        setProducts(productList);
      } catch (err) {
        setError(err instanceof Error ? err.message : "初始化失败");
      } finally {
        setBooting(false);
      }
    };

    void bootstrap();
  }, []);

  useEffect(() => {
    const loadSession = async () => {
      try {
        setError(null);
        await refreshSessionDetail(sessionId);
      } catch {
        setSessionDetail({ session_id: sessionId, history: [], last_result: null });
        setLastResponse(null);
      }
    };

    void loadSession();
  }, [sessionId]);

  const sendMessage = async (message?: string) => {
    const finalMessage = (message ?? input).trim();
    if (!finalMessage) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.sendChat({
        session_id: sessionId,
        message: finalMessage,
        model_provider: provider,
      });
      setLastResponse(response);
      setInput("");
      await Promise.all([refreshSessionDetail(sessionId), refreshSessions()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送消息失败");
    } finally {
      setLoading(false);
    }
  };

  const selectSession = async (targetSessionId: string) => {
    setSessionId(targetSessionId);
    await refreshSessionDetail(targetSessionId);
  };

  const createNewSession = () => {
    const next = createSessionId();
    setSessionId(next);
    setSessionDetail({ session_id: next, history: [], last_result: null });
    setLastResponse(null);
    setInput("");
  };

  return {
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
  };
}
