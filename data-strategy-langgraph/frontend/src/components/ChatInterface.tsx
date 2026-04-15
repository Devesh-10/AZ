import React, { useState } from "react";
import { ChatMessage, KpiResult, DataSource } from "../types";
import { sendQuery } from "../api/chatApi";
import VisualizationPanel from "./VisualizationPanel";
import "./ChatInterface.css";

// Enterprise-level text formatting with markdown table support
const formatText = (content: string): string => {
  let formatted = content;

  formatted = formatted.replace(/DATA_TABLE_START[\s\S]*?DATA_TABLE_END/g, '');

  const lines = formatted.split('\n');
  const result: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      if (i + 1 < lines.length && /^\|[\s\-:]+\|/.test(lines[i + 1].trim())) {
        const tableRows: string[] = [];
        const headerCells = line.split('|').filter(c => c.trim() !== '').map(c => c.trim());

        tableRows.push('<thead><tr>' + headerCells.map(c => `<th>${c}</th>`).join('') + '</tr></thead>');

        i += 2;

        const bodyRows: string[] = [];
        while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
          const cells = lines[i].split('|').filter(c => c.trim() !== '').map(c => c.trim());
          bodyRows.push('<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>');
          i++;
        }

        if (bodyRows.length > 0) {
          tableRows.push('<tbody>' + bodyRows.join('') + '</tbody>');
        }

        result.push('<div class="markdown-table"><table class="enterprise-table">' + tableRows.join('') + '</table></div>');
        continue;
      }
    }

    result.push(line);
    i++;
  }

  formatted = result.join('\n');

  formatted = formatted.replace(/^### (.+)$/gm, '<h4 class="section-header">$1</h4>');
  formatted = formatted.replace(/^## (.+)$/gm, '<h3 class="section-header">$1</h3>');

  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, '<li>$1</li>');

  formatted = formatted.replace(/(<li>.*?<\/li>\n?)+/g, '<ul class="details-list">$&</ul>');

  formatted = formatted.replace(/\n\n+/g, '</p><p>');
  formatted = formatted.replace(/(?<!<\/h[34]>|<\/table>|<\/div>|<\/ul>)\n(?!<)/g, '<br>');

  if (formatted && !formatted.startsWith('<')) {
    formatted = '<p>' + formatted + '</p>';
  }

  formatted = formatted.replace(/<p>\s*<\/p>/g, '');
  formatted = formatted.replace(/<p>\s*<br>\s*<\/p>/g, '');

  return formatted;
};

const formatValue = (value: number, kpiName: string): string => {
  const lowerName = kpiName.toLowerCase();

  let unit = '';
  if (lowerName.includes('completeness') || lowerName.includes('accuracy') || lowerName.includes('score') || lowerName.includes('consistency') || lowerName.includes('uniqueness') || lowerName.includes('%')) {
    unit = '%';
  } else if (lowerName.includes('time') || lowerName.includes('freshness') || lowerName.includes('hr')) {
    unit = ' hr';
  } else if (lowerName.includes('count') || lowerName.includes('null') || lowerName.includes('missing')) {
    unit = '';
  } else if (lowerName.includes('row') || lowerName.includes('record')) {
    unit = ' rows';
  }

  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M${unit}`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k${unit}`;
  } else {
    return `${value.toLocaleString()}${unit}`;
  }
};

const formatKpiName = (name: string): string => {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
};

const DataTable: React.FC<{ results: KpiResult[] }> = ({ results }) => {
  if (!results || results.length === 0) return null;

  const scoredResults = results.map(r => {
    let score = 0;
    const name = r.kpiName.toLowerCase();
    const hasMultiplePoints = r.dataPoints.length > 1;
    const isBreakdown = name.includes('by_') || name.includes('per_');
    const isCategoryData = r.dataPoints.every(dp =>
      !dp.label.toLowerCase().includes('avg') &&
      !dp.label.toLowerCase().includes('total') &&
      !dp.label.toLowerCase().includes('%')
    );

    if (isBreakdown && isCategoryData) score += 100;
    if (hasMultiplePoints) score += 50;
    if (isCategoryData) score += 25;
    if (name.includes('table') || name.includes('system')) score += 10;

    return { result: r, score };
  });

  scoredResults.sort((a, b) => b.score - a.score);
  const bestResult = scoredResults[0]?.result;
  if (!bestResult) return null;

  const dataPoints = bestResult.dataPoints;
  if (dataPoints.length === 0) return null;

  const isCountData = dataPoints.every(dp => {
    const label = dp.label.toLowerCase();
    return !label.includes('avg') && !label.includes('%') && !label.includes('time') && !label.includes('score');
  });

  const totalRows = dataPoints.filter(dp => dp.label.toLowerCase().startsWith('total'));
  const categoryRows = dataPoints.filter(dp => !dp.label.toLowerCase().startsWith('total'));

  const sortedCategories = [...categoryRows].sort((a, b) => b.value - a.value).slice(0, 6);

  const calculatedTotal = isCountData ? sortedCategories.reduce((sum, dp) => sum + dp.value, 0) : 0;

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
  onAgentLogs?: (logs: { id: string; sessionId: string; timestamp: string; agentName: string; inputSummary: string; outputSummary: string; reasoningSummary?: string; status: string; }[]) => void;
  onLogout?: () => void;
  dataSource?: DataSource;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  onSessionIdChange,
  onNewMessage,
  onBackToDashboard,
  onSqlGenerated,
  onAgentLogs,
  onLogout,
  dataSource,
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
      "How complete is our batch data across all systems?",
      "What is the overall data quality score?",
      "Show data freshness metrics for LIMS",
    ],
    lifecycleQuestions: [
      "Run full DQ lifecycle on batch data",
      "Profile the LIMS results table",
      "Check all DQ rules for MES data",
      "Generate DQ scorecard across all systems",
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

      if (response.generatedSql && onSqlGenerated) {
        onSqlGenerated(response.generatedSql);
      }

      if (response.agentLogs && onAgentLogs) {
        onAgentLogs(response.agentLogs);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
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
            {dataSource && (
              <div className="connected-source-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
                <span>Connected: {dataSource.name} | {dataSource.assets} assets{dataSource.rules > 0 ? ` | ${dataSource.rules} rules` : ''}</span>
              </div>
            )}

            {/* Platform Capabilities Showcase */}
            <div className="capabilities-showcase">
              <div className="capabilities-header">
                <h2 className="capabilities-title">Data Quality Intelligence Platform</h2>
                <p className="capabilities-subtitle">AI-powered agents that discover, profile, validate, and heal your data</p>
              </div>

              <div className="capabilities-grid">
                <button className="capability-card active-cap" onClick={() => handleSuggestionClick("Profile all tables and show completeness, accuracy, uniqueness, consistency and timeliness dimensions")}>
                  <div className="cap-icon cap-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Discovery &amp; Profiling<span className="cap-badge cap-live">LIVE</span></div>
                    <div className="cap-desc">Scan 14 tables, compute 5-dimension DQ scores per table</div>
                  </div>
                </button>

                <button className="capability-card active-cap" onClick={() => handleSuggestionClick("Validate all DQ rules and show which rules are failing with violation counts")}>
                  <div className="cap-icon cap-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Rules Validation<span className="cap-badge cap-live">LIVE</span></div>
                    <div className="cap-desc">Run 15 governance rules, show pass/fail and violations</div>
                  </div>
                </button>

                <button className="capability-card active-cap" onClick={() => handleSuggestionClick("Generate DQ scorecard across all systems")}>
                  <div className="cap-icon cap-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">DQ Scorecard &amp; Reporting<span className="cap-badge cap-live">LIVE</span></div>
                    <div className="cap-desc">Full lifecycle: profile + rules + executive summary</div>
                  </div>
                </button>

                <div className="capability-card planned-cap" title="Coming soon">
                  <div className="cap-icon cap-icon-amber">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Scheduled DQ Runs<span className="cap-badge cap-planned">COMING SOON</span></div>
                    <div className="cap-desc">Automated daily/weekly lifecycle scans</div>
                  </div>
                </div>

                <div className="capability-card planned-cap" title="Coming soon">
                  <div className="cap-icon cap-icon-amber">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Alerts &amp; Jira Integration<span className="cap-badge cap-planned">COMING SOON</span></div>
                    <div className="cap-desc">Auto-notify stewards, create tickets on DQ breach</div>
                  </div>
                </div>

                <button className="capability-card active-cap" onClick={() => handleSuggestionClick("Run full DQ lifecycle with remediation plan and root cause analysis")}>
                  <div className="cap-icon cap-icon-green">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Self-Healing Data<span className="cap-badge cap-live">LIVE</span></div>
                    <div className="cap-desc">Detect → trace root cause → prioritize → remediation plan</div>
                  </div>
                </button>

                <div className="capability-card vision-cap" title="Future vision">
                  <div className="cap-icon cap-icon-purple">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="3" /><circle cx="19" cy="5" r="2" /><circle cx="5" cy="19" r="2" />
                      <line x1="14.5" y1="9.5" x2="17.5" y2="6.5" /><line x1="9.5" y1="14.5" x2="6.5" y2="17.5" />
                    </svg>
                  </div>
                  <div className="cap-body">
                    <div className="cap-label">Agent Mesh<span className="cap-badge cap-vision">VISION</span></div>
                    <div className="cap-desc">MDM, Lineage &amp; Compliance agents collaborating</div>
                  </div>
                </div>
              </div>
            </div>

            <p className="try-asking">Try asking:</p>

            <div className="suggestion-category">
              <span className="category-label">SINGLE METRIC QUERIES</span>
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
              <span className="category-label">DQ LIFECYCLE ANALYSIS</span>
              {suggestedQuestions.lifecycleQuestions.map((q, i) => (
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
            placeholder="Ask about data quality across your systems..."
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

        <div className="version-tag">Version 1.0 (LangGraph)</div>
      </div>
    );
  }

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
        {onLogout && (
          <button className="logout-btn" onClick={onLogout}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Logout
          </button>
        )}
      </div>
      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.role === "assistant" && (
              <div className="message-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
            )}
            <div className="message-content">
              <div className="formatted-content" dangerouslySetInnerHTML={{ __html: formatText(msg.content) }} />
              {msg.kpiResult && msg.kpiResult.length > 0 && (
                <DataTable results={msg.kpiResult} />
              )}
              {msg.visualizationConfig && msg.visualizationConfig.series && msg.visualizationConfig.series.length > 0 && (
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
          {[
            { label: "Full Lifecycle", query: "Run full DQ lifecycle on all tables" },
            { label: "Profile", query: "Profile the batch data tables" },
            { label: "Rules Check", query: "Check all DQ rules" },
            { label: "Scorecard", query: "Generate DQ scorecard" },
          ].map((q, i) => (
            <button
              key={i}
              className="quick-chip"
              onClick={() => handleSend(q.query)}
              disabled={isLoading}
            >
              {q.label}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="chat-input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about data quality across your systems..."
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
