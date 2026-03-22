export type ModelProvider = "qwen" | "deepseek" | "mock";

export interface ChatRequest {
  session_id: string;
  message: string;
  model_provider: ModelProvider;
}

export interface ChatResponse {
  session_id: string;
  intent: string;
  answer: string;
  logs: string[];
  used_tools: string[];
  agent_path: string[];
  provider_used: string;
}

export interface SessionDetail {
  session_id: string;
  history: Array<{ role: string; content: string }>;
  last_result: ChatResponse | null;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  last_intent?: string | null;
  updated_at?: string | null;
}

export interface Product {
  id: number;
  name: string;
  category: string;
  selling_points: string[];
  price: number;
  target_users: string[];
  faq: Array<{ question: string; answer: string }>;
  after_sale_policy: string;
}

export interface SeedInitResponse {
  message: string;
  product_count: number;
  review_count: number;
  competitor_count: number;
  database_mode: string;
}

export interface HealthResponse {
  status: string;
  database: Record<string, unknown>;
  redis: Record<string, unknown>;
}

