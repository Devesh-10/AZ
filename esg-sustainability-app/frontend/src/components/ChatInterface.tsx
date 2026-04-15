import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { sendChatMessage } from "../api/api";
import type { ChatMessage } from "../types";

const SUGGESTIONS = [
  "Which companies have the best ESG scores?",
  "Compare Apple vs Microsoft ESG performance",
  "What sectors score lowest on environmental metrics?",
  "Show me top 5 healthcare companies by ESG",
];

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Hello! I'm your ESG sustainability assistant. Ask me anything about ESG scores, company ratings, sector comparisons, or sustainability metrics." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const response = await sendChatMessage(msg);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please check that the backend is running and OPENAI_API_KEY is set." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.headerIcon}>🌿</div>
        <div>
          <div style={styles.headerTitle}>ESG Assistant</div>
          <div style={styles.headerSub}>Ask about ESG scores & sustainability</div>
        </div>
      </div>

      <div style={styles.messages}>
        {messages.map((msg, i) => (
          <div key={i} style={msg.role === "user" ? styles.userMsgRow : styles.assistantMsgRow}>
            <div style={msg.role === "user" ? styles.userBubble : styles.assistantBubble}>
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p style={{ margin: "4px 0" }}>{children}</p>,
                  strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
                  li: ({ children }) => <li style={{ marginLeft: 16, marginBottom: 2 }}>{children}</li>,
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div style={styles.assistantMsgRow}>
            <div style={styles.assistantBubble}>
              <div style={styles.typing}>
                <span style={styles.dot} /><span style={{ ...styles.dot, animationDelay: "0.2s" }} /><span style={{ ...styles.dot, animationDelay: "0.4s" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length <= 1 && (
        <div style={styles.suggestions}>
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => handleSend(s)} style={styles.suggestBtn}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div style={styles.inputRow}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about ESG scores..."
          style={styles.input}
          disabled={loading}
        />
        <button onClick={() => handleSend()} disabled={loading || !input.trim()} style={styles.sendBtn}>
          ➤
        </button>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex", flexDirection: "column", height: "100%",
    background: "#fff", borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    overflow: "hidden",
  },
  header: {
    display: "flex", alignItems: "center", gap: 10, padding: "16px 20px",
    borderBottom: "1px solid #e2e8f0", background: "#f0fdf4",
  },
  headerIcon: { fontSize: 24 },
  headerTitle: { fontWeight: 600, fontSize: 15, color: "#1e293b" },
  headerSub: { fontSize: 12, color: "#64748b" },
  messages: { flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 12 },
  userMsgRow: { display: "flex", justifyContent: "flex-end" },
  assistantMsgRow: { display: "flex", justifyContent: "flex-start" },
  userBubble: {
    background: "#059669", color: "#fff", padding: "10px 16px", borderRadius: "16px 16px 4px 16px",
    maxWidth: "85%", fontSize: 13, lineHeight: 1.5,
  },
  assistantBubble: {
    background: "#f1f5f9", color: "#1e293b", padding: "10px 16px", borderRadius: "16px 16px 16px 4px",
    maxWidth: "85%", fontSize: 13, lineHeight: 1.5,
  },
  typing: { display: "flex", gap: 4, padding: "4px 0" },
  dot: {
    width: 6, height: 6, borderRadius: "50%", background: "#94a3b8",
    animation: "blink 1s infinite",
  },
  suggestions: { display: "flex", flexWrap: "wrap", gap: 8, padding: "0 16px 12px" },
  suggestBtn: {
    padding: "6px 12px", borderRadius: 16, border: "1px solid #d1fae5",
    background: "#f0fdf4", color: "#059669", fontSize: 12, cursor: "pointer",
    fontFamily: "Inter, sans-serif",
  },
  inputRow: {
    display: "flex", gap: 8, padding: "12px 16px", borderTop: "1px solid #e2e8f0",
    background: "#fafafa",
  },
  input: {
    flex: 1, padding: "10px 14px", borderRadius: 10, border: "1px solid #e2e8f0",
    fontSize: 13, outline: "none", fontFamily: "Inter, sans-serif",
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: 10, border: "none",
    background: "#059669", color: "#fff", fontSize: 16, cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
};

export default ChatInterface;
