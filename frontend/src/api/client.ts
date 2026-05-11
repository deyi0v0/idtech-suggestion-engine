export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatHistoryItem[];
}

export interface ForceChatRequest extends ChatRequest {
  force_recommendation?: boolean;
  debug_mode?: boolean;
}

export interface RecommendationBundle {
  hardware_name: string;
  hardware_items: Record<string, unknown>[];
  explanation: string;
  software?: Record<string, unknown>[];
  highlights?: string[];
}

export interface ChatResponse {
  type: "question" | "recommendation" | "clarification" | "error";
  text: string;
  quick_replies?: string[];
  recommendation?: RecommendationBundle;
  debug?: Record<string, unknown>;
}

export interface PDFRequest {
  hardware_name: string;
  software_name?: string;
  highlights?: string[];
  explanation: string;
}

const API_BASE =
  (globalThis as { __VITE_API_BASE_URL__?: string }).__VITE_API_BASE_URL__ ??
  (typeof process !== "undefined" ? process.env.VITE_API_BASE_URL : undefined) ??
  "";

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }
  return response;
}

export async function sendChatMessage(chatRequest: ChatRequest): Promise<ChatResponse> {
  const response = await apiFetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(chatRequest),
  });

  return response.json() as Promise<ChatResponse>;
}

export async function forceChatMessage(chatRequest: ForceChatRequest): Promise<ChatResponse> {
  const response = await apiFetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(chatRequest),
  });

  return response.json() as Promise<ChatResponse>;
}

export async function downloadPDF(payload: PDFRequest): Promise<Blob> {
  const response = await apiFetch("/api/pdf/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return response.blob();
}

export async function downloadRecommendationPDF(bundle: RecommendationBundle): Promise<Blob> {
  const response = await apiFetch("/api/pdf/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bundle),
  });

  return response.blob();
}
