import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:3010";

export interface AgentStep {
  type: "tool_call" | "tool_result" | "ai_message";
  name: string | null;
  content: string;
  args?: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  steps: AgentStep[];
}

export async function sendChat(question: string, sessionId: string | null): Promise<ChatResponse> {
  const { data } = await axios.post<ChatResponse>(`${BASE_URL}/api/chat`, {
    question,
    session_id: sessionId,
  });
  return data;
}

export async function clearSession(sessionId: string): Promise<void> {
  await axios.delete(`${BASE_URL}/api/sessions/${sessionId}`);
}
