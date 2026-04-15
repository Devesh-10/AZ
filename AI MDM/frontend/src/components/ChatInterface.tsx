import { useState, useRef, useEffect } from "react";
import { sendChat, clearSession, type AgentStep } from "../api/chatApi";
import { AgentTrace } from "./AgentTrace";
import "./ChatInterface.css";

interface Message {
  role: "user" | "assistant";
  content: string;
  steps?: AgentStep[];
}

const SUGGESTIONS = [
  "Add Dr. Sara Chen, oncologist in Boston MA",
  "Find HCPs with last name Chen in Boston",
  "Add Cleveland Clinic Foundation in Cleveland OH",
  "Show me oncologists in Boston",
  "Are there duplicates for Mass General in Boston?",
];

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm the MDM Agent. I can help you search, create, and merge master data " +
        "(HCPs, HCOs, Products) while enforcing governance like search-before-create and " +
        "duplicate detection. Try one of the suggestions below or ask me anything.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text?: string) {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question }]);
    setLoading(true);
    try {
      const res = await sendChat(question, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, steps: res.steps }]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Error: ${e?.message ?? "request failed"}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (sessionId) {
      try {
        await clearSession(sessionId);
      } catch {
        /* ignore */
      }
    }
    setSessionId(null);
    setMessages([
      {
        role: "assistant",
        content: "Session cleared. What would you like to do?",
      },
    ]);
  }

  return (
    <div className="chat-root">
      <header className="chat-header">
        <div>
          <h1>Agentic MDM</h1>
          <p>Conversational master data management with governance</p>
        </div>
        <button className="clear-btn" onClick={handleClear}>
          New session
        </button>
      </header>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`bubble bubble-${msg.role}`}>
            <div className="bubble-content">
              {msg.content.split("\n").map((line, j) => (
                <div key={j}>{line || "\u00a0"}</div>
              ))}
            </div>
            {msg.steps && msg.steps.length > 0 && <AgentTrace steps={msg.steps} />}
          </div>
        ))}
        {loading && (
          <div className="bubble bubble-assistant">
            <div className="thinking">
              <span /><span /><span />
            </div>
          </div>
        )}
      </div>

      {messages.length <= 1 && (
        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => handleSend(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the MDM agent..."
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
