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
  if (lowerName.includes('emission') || lowerName.includes('ghg') || lowerName.includes('co2')) {
    unit = ' tCO2';
  } else if (lowerName.includes('energy') || lowerName.includes('consumption')) {
    unit = ' MWh';
  } else if (lowerName.includes('water')) {
    unit = ' ML';
  } else if (lowerName.includes('waste')) {
    unit = ' tonnes';
  } else if (lowerName.includes('fleet') || lowerName.includes('vehicle')) {
    unit = ' vehicles';
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

// Render data tables from KPI results - one table per KPI type
const DataTable: React.FC<{ results: KpiResult[] }> = ({ results }) => {
  if (!results || results.length === 0) return null;

  // Group results by KPI name to avoid mixing different data types
  const groupedByKpi = new Map<string, KpiResult[]>();
  results.forEach(r => {
    const existing = groupedByKpi.get(r.kpiName) || [];
    existing.push(r);
    groupedByKpi.set(r.kpiName, existing);
  });

  // Only show the first/main KPI table to avoid clutter
  const mainKpi = Array.from(groupedByKpi.entries())[0];
  if (!mainKpi) return null;

  const [kpiName, kpiResults] = mainKpi;

  // Get all data points for this KPI
  const allDataPoints = kpiResults.flatMap(r => r.dataPoints);

  // Filter out meta entries and breakdown rows, dedupe (same logic as backend VisualizationAgent)
  const deduped = new Map<string, { label: string; value: number }>();
  allDataPoints.forEach(dp => {
    const lowerLabel = dp.label.toLowerCase();
    // Skip meta labels like "Total Records"
    if (lowerLabel.includes('record')) return;
    // Skip breakdown prefixed labels (e.g., "Site: Baar", "Month: 2024-01")
    if (dp.label.includes(':')) return;

    const existing = deduped.get(dp.label);
    if (!existing || dp.value > existing.value) {
      deduped.set(dp.label, dp);
    }
  });

  // Convert to array and sort by value descending
  const uniqueDataPoints = Array.from(deduped.values())
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  if (uniqueDataPoints.length === 0) return null;

  // Separate total rows from category rows for proper display
  const totalRows = uniqueDataPoints.filter(dp => dp.label.toLowerCase().startsWith('total'));
  const categoryRows = uniqueDataPoints.filter(dp => !dp.label.toLowerCase().startsWith('total'));

  // For GHG emissions, use the actual total (Scope 1 + Scope 2) not sum of all displayed values
  // This avoids double counting (e.g., Scope 1 Road Fleet is a subset of Scope 1 Total,
  // and Scope 2 Location-Based is an alternative to Scope 2 Market-Based)
  const isGhgEmissions = kpiName.toLowerCase().includes('ghg') || kpiName.toLowerCase().includes('emission');

  let calculatedTotal: number;
  if (isGhgEmissions && totalRows.length > 0) {
    // Use the actual total from the data
    calculatedTotal = totalRows[0].value;
  } else {
    // For other KPIs, sum the category rows
    calculatedTotal = categoryRows.reduce((sum, dp) => sum + dp.value, 0);
  }

  return (
    <div className="data-table-container">
      <div className="table-title">{formatKpiName(kpiName)}</div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Value</th>
            <th>Share</th>
          </tr>
        </thead>
        <tbody>
          {categoryRows.map((dp, idx) => {
            const percentage = calculatedTotal > 0 ? ((dp.value / calculatedTotal) * 100).toFixed(1) : '0';
            return (
              <tr key={`${dp.label}-${idx}`}>
                <td>{dp.label}</td>
                <td className="value-cell">{formatValue(dp.value, kpiName)}</td>
                <td className="percentage-cell">{percentage}%</td>
              </tr>
            );
          })}
          {totalRows.map((dp, idx) => (
            <tr key={`total-${idx}`} className="total-row">
              <td><strong>{dp.label}</strong></td>
              <td className="value-cell"><strong>{formatValue(dp.value, kpiName)}</strong></td>
              <td className="percentage-cell"><strong>-</strong></td>
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
      "What is our total energy consumption?",
      "Show me GHG emissions breakdown",
      "How much water did we use?",
    ],
    analystQuestions: [
      "Why are our emissions high? What are the main contributors?",
      "How can we improve our sustainability performance?",
      "Analyze our EV transition progress and recommend actions",
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
          <div className="welcome-icon">
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h1 className="welcome-title">Welcome to Sustainability Insight Agent</h1>
          <p className="welcome-subtitle">
            Ask questions about energy consumption, GHG emissions, water usage, waste management, and EV fleet transition.
          </p>

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
            placeholder="Ask about sustainability data..."
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

        <div className="version-tag">Version 1.0</div>
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
          {["Energy consumption", "GHG emissions", "Water usage", "EV fleet"].map((q, i) => (
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
            placeholder="Ask about sustainability data..."
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
