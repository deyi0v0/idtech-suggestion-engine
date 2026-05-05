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
}

export type ChatResponse = Record<string, unknown>;

export interface PDFRequest {
  hardware_name: string;
  software_name?: string;
  highlights?: string[];
  explanation: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

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
