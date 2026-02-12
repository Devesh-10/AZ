import React, { useState, useRef, useEffect } from "react";
import { ChatMessage, VisualizationConfig, KpiResult } from "../types";
import { sendQuery } from "../api/chatApi";
import "./ChatPanel.css";

interface ChatPanelProps {
  sessionId: string | null;
  onSessionIdChange: (sessionId: string) => void;
  onVisualization: (config: VisualizationConfig | undefined) => void;
  onKpiResult: (results: KpiResult[] | undefined) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  sessionId,
  onSessionIdChange,
  onVisualization,
  onKpiResult,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendQuery(sessionId, userMessage.content);

      // Update session ID if this is the first message
      if (!sessionId && response.sessionId) {
        onSessionIdChange(response.sessionId);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        visualizationConfig: response.visualizationConfig,
        kpiResult: response.kpiResult,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update visualization and KPI results
      onVisualization(response.visualizationConfig);
      onKpiResult(response.kpiResult);

      // Show follow-up question if needed
      if (response.followUpQuestion) {
        const followUpMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content: `📝 ${response.followUpQuestion}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, followUpMessage]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedQuestions = [
    "What was total revenue in Q1 2024?",
    "Show me revenue by region",
    "Compare revenue and cost by month",
    "Why is APAC revenue lower than Americas?",
  ];

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>💬 KPI Assistant</h2>
        {sessionId && (
          <span className="session-id">Session: {sessionId.slice(0, 8)}...</span>
        )}
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome to the Agentic KPI Assistant!</h3>
            <p>Ask questions about your business KPIs. Try one of these:</p>
            <div className="suggested-questions">
              {suggestedQuestions.map((q, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => setInput(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content.split("\n").map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  {i < msg.content.split("\n").length - 1 && <br />}
                </React.Fragment>
              ))}
            </div>
            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span className="loading-text">Analyzing...</span>
          </div>
        )}

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your KPIs..."
          disabled={isLoading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="send-btn"
        >
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
};

export default ChatPanel;
