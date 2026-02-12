import { ChatResponse, AgentLogEntry, KnowledgeGraph } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Send a query to the KPI assistant
 */
export async function sendQuery(
  sessionId: string | null,
  message: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      sessionId,
      message,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  return response.json();
}

/**
 * Get telemetry logs for a session
 */
export async function getTelemetry(sessionId: string): Promise<AgentLogEntry[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/chat/telemetry/${sessionId}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Get the knowledge graph schema
 */
export async function getKnowledgeGraph(): Promise<KnowledgeGraph> {
  const response = await fetch(`${API_BASE_URL}/api/meta/knowledge-graph`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Get available KPIs and dimensions
 */
export async function getSchema(): Promise<{
  kpis: string[];
  dimensions: Record<string, string[]>;
}> {
  const response = await fetch(`${API_BASE_URL}/api/meta/schema`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
