import axios from "axios";
import type {
  APIMessage,
  ChatRequest,
  ChatResponse,
  HealthResponse,
  Product,
  SeedInitResponse,
  SessionDetail,
  SessionSummary,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api",
  timeout: 30000,
});

export const apiClient = {
  initSeed: async () => (await api.post<SeedInitResponse>("/seed/init")).data,
  getHealth: async () => (await api.get<HealthResponse>("/health")).data,
  getProducts: async () => (await api.get<Product[]>("/products")).data,
  sendChat: async (payload: ChatRequest) =>
    (await api.post<ChatResponse>("/chat", payload, { timeout: 0 })).data,
  getSession: async (sessionId: string) =>
    (await api.get<SessionDetail>(`/session/${sessionId}`)).data,
  getSessions: async () => (await api.get<SessionSummary[]>("/sessions")).data,
  deleteSession: async (sessionId: string) =>
    (await api.delete<APIMessage>(`/session/${sessionId}`)).data,
};
