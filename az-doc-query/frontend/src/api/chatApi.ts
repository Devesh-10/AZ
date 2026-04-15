const API_BASE = '/api';

export interface Source {
  doc_title: string;
  doc_type: string;
  section: string;
  relevance: number;
}

export interface ChatResponse {
  answer: string;
  session_id: string;
  sources: Source[];
}

export interface DocSummary {
  id: string;
  title: string;
  type: string;
  section_count: number;
}

export async function sendQuery(
  question: string,
  sessionId: string | null,
  docTypeFilter?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      doc_type_filter: docTypeFilter || null,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function fetchDocuments(): Promise<DocSummary[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error(`Failed to load documents`);
  return res.json();
}

export async function fetchDocTypes(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/doc-types`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.types;
}

export async function clearSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
}
