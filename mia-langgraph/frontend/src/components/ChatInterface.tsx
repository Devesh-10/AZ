import React, { useState } from "react";
import { ChatMessage, KpiResult } from "../types";
import { sendQuery } from "../api/chatApi";
import VisualizationPanel from "./VisualizationPanel";
import "./ChatInterface.css";

// Simple text formatting - no table parsing (tables rendered separately)
const formatText = (content: string): string => {
  let formatted = content;

  // Remove any pipe characters or table-like content from narrative
  formatted = formatted.replace(/\|[^|]*\|/g, '');
  formatted = formatted.replace(/DATA_TABLE_START[\s\S]*?DATA_TABLE_END/g, '');
  formatted = formatted.replace(/\|[-:\s]+\|/g, '');

  // Convert markdown formatting
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, '<li>$1</li>');

  // Clean up
  formatted = formatted.replace(/\n\n+/g, '</p><p>');
  formatted = formatted.replace(/\n/g, ' ');
  formatted = formatted.replace(/\s+/g, ' ').trim();

  if (formatted && !formatted.startsWith('<')) {
    formatted = '<p>' + formatted + '</p>';
  }

  return formatted;
};

// Format number with proper units
const formatValue = (value: number, kpiName: string): string => {
  const lowerName = kpiName.toLowerCase();

  // Determine unit based on KPI name
  let unit = '';
  if (lowerName.includes('yield') || lowerName.includes('rft') || lowerName.includes('oee') || lowerName.includes('adherence') || lowerName.includes('%')) {
    unit = '%';
  } else if (lowerName.includes('cycle') || lowerName.includes('time') || lowerName.includes('hr')) {
    unit = ' hr';
  } else if (lowerName.includes('batch') || lowerName.includes('count')) {
    unit = ' batches';
  } else if (lowerName.includes('volume')) {
    unit = ' units';
  } else if (lowerName.includes('deviation')) {
    unit = '';
  }

  // Format number
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M${unit}`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k${unit}`;
  } else {
    return `${value.toLocaleString()}${unit}`;
  }
};

// Format KPI name for display
const formatKpiName = (name: string): string => {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
};

// Render data tables from KPI results - picks the best single table to display
const DataTable: React.FC<{ results: KpiResult[] }> = ({ results }) => {
  if (!results || results.length === 0) return null;

  // Find the best table to display based on data characteristics
  // Priority: breakdown tables (by_status, by_site, by_equipment) > summary with multiple metrics > single values
  const scoredResults = results.map(r => {
    let score = 0;
    const name = r.kpiName.toLowerCase();
    const hasMultiplePoints = r.dataPoints.length > 1;
    const isBreakdown = name.includes('by_status') || name.includes('by_site') || name.includes('by_equipment');
    const isCategoryData = r.dataPoints.every(dp =>
      !dp.label.toLowerCase().includes('avg') &&
      !dp.label.toLowerCase().includes('total') &&
      !dp.label.toLowerCase().includes('%')
    );

    if (isBreakdown && isCategoryData) score += 100; // Best: categorical breakdowns
    if (hasMultiplePoints) score += 50;
    if (isCategoryData) score += 25;
    if (name.includes('status')) score += 10; // Prefer status breakdowns

    return { result: r, score };
  });

  scoredResults.sort((a, b) => b.score - a.score);
  const bestResult = scoredResults[0]?.result;
  if (!bestResult) return null;

  const dataPoints = bestResult.dataPoints;
  if (dataPoints.length === 0) return null;

  // Determine if this is count data (show percentages) or metric data (no percentages)
  const isCountData = dataPoints.every(dp => {
    const label = dp.label.toLowerCase();
    return !label.includes('avg') && !label.includes('%') && !label.includes('time') && !label.includes('yield');
  });

  // Separate totals from categories
  const totalRows = dataPoints.filter(dp => dp.label.toLowerCase().startsWith('total'));
  const categoryRows = dataPoints.filter(dp => !dp.label.toLowerCase().startsWith('total'));

  // Sort by value descending, limit to 6 rows
  const sortedCategories = [...categoryRows].sort((a, b) => b.value - a.value).slice(0, 6);

  // Calculate total for percentage calculation (only for count data)
  const calculatedTotal = isCountData ? sortedCategories.reduce((sum, dp) => sum + dp.value, 0) : 0;

  // Generate display title from kpiName
  const displayTitle = formatKpiName(bestResult.kpiName.replace(/_/g, ' '));

  return (
    <div className="data-table-container">
      <div className="table-title">{displayTitle}</div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Value</th>
            {isCountData && <th>Share</th>}
          </tr>
        </thead>
        <tbody>
          {sortedCategories.map((dp, idx) => {
            const percentage = isCountData && calculatedTotal > 0
              ? ((dp.value / calculatedTotal) * 100).toFixed(1)
              : null;
            return (
              <tr key={`${dp.label}-${idx}`}>
                <td>{dp.label}</td>
                <td className="value-cell">{formatValue(dp.value, bestResult.kpiName)}</td>
                {isCountData && <td className="percentage-cell">{percentage}%</td>}
              </tr>
            );
          })}
          {totalRows.map((dp, idx) => (
            <tr key={`total-${idx}`} className="total-row">
              <td><strong>{dp.label}</strong></td>
              <td className="value-cell"><strong>{formatValue(dp.value, bestResult.kpiName)}</strong></td>
              {isCountData && <td className="percentage-cell"><strong>-</strong></td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

interface ChatInterfaceProps {
  sessionId: string | null;
  onSessionIdChange: (sessionId: string | null) => void;
  onNewMessage: () => void;
  onBackToDashboard?: () => void;
  onSqlGenerated?: (sql: string | null) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  onSessionIdChange,
  onNewMessage,
  onBackToDashboard,
  onSqlGenerated,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
    onSessionIdChange(null);
    if (onSqlGenerated) onSqlGenerated(null);
  };

  const suggestedQuestions = {
    kpiQuestions: [
      "What is the average formulation lead time for SKU_456 over the past three months?",
      "Show OEE performance for the last 3 months",
      "What is the batch yield for SKU_123 this month?",
    ],
    analystQuestions: [
      "What is the waiting time between end of formulation and start of packaging for batch B2025-00007?",
      "Why is our RFT below target? What are the root causes?",
      "How can we improve our OEE packaging efficiency?",
    ],
  };

  const handleSend = async (message: string) => {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    onNewMessage();

    try {
      const response = await sendQuery(sessionId, message);

      if (!sessionId && response.sessionId) {
        onSessionIdChange(response.sessionId);
      }

      // Get data for table from analyst result or kpi result
      const tableData = response.analystResult?.supportingKpiResults || response.kpiResult;

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        visualizationConfig: response.visualizationConfig,
        kpiResult: tableData,
        analystResult: response.analystResult,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Pass generated SQL to parent
      if (response.generatedSql && onSqlGenerated) {
        onSqlGenerated(response.generatedSql);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  const handleSuggestionClick = (question: string) => {
    handleSend(question);
  };

  // Show welcome screen if no messages
  if (messages.length === 0) {
    return (
      <div className="chat-interface">
        {onBackToDashboard && (
          <button className="back-to-dashboard-btn" onClick={onBackToDashboard}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
        )}
        <div className="welcome-container">
          <div className="suggestions-container">
            <p className="try-asking">Try asking:</p>

            <div className="suggestion-category">
              <span className="category-label">SIMPLE KPI QUERIES</span>
              {suggestedQuestions.kpiQuestions.map((q, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => handleSuggestionClick(q)}
                >
                  "{q}"
                </button>
              ))}
            </div>

            <div className="suggestion-category">
              <span className="category-label">DEEP ANALYSIS (ANALYST AGENT)</span>
              {suggestedQuestions.analystQuestions.map((q, i) => (
                <button
                  key={i}
                  className="suggestion-btn"
                  onClick={() => handleSuggestionClick(q)}
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about manufacturing data..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || !input.trim()}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>

        <div className="version-tag">Version 2.0 (LangGraph)</div>
      </div>
    );
  }

  // Show chat messages
  return (
    <div className="chat-interface">
      <div className="chat-header-buttons">
        {onBackToDashboard && (
          <button className="back-to-dashboard-btn" onClick={onBackToDashboard}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Dashboard
          </button>
        )}
        <button className="new-chat-btn" onClick={handleNewChat}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Chat
        </button>
      </div>
      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="message-avatar">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
            )}
            <div className="message-content">
              <div className="formatted-content" dangerouslySetInnerHTML={{ __html: formatText(msg.content) }} />
              {msg.kpiResult && msg.kpiResult.length > 0 && (
                <DataTable results={msg.kpiResult} />
              )}
              {msg.visualizationConfig && (
                <div className="message-visualization">
                  <VisualizationPanel config={msg.visualizationConfig} />
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="input-area">
        <div className="quick-suggestions">
          {["Batch yield", "OEE", "Cycle time", "RFT rate"].map((q, i) => (
            <button
              key={i}
              className="quick-chip"
              onClick={() => handleSend(`What is our ${q.toLowerCase()}?`)}
              disabled={isLoading}
            >
              {q}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about manufacturing data..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || !input.trim()}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
