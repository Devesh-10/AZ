import { useState, useEffect } from "react";
import { AgentLogEntry } from "../types";
import { getTelemetry } from "../api/chatApi";
import "./AgentFlowPanel.css";

interface AgentFlowPanelProps {
  sessionId: string | null;
  isCollapsed?: boolean;
}

const AgentFlowPanel: React.FC<AgentFlowPanelProps> = ({ sessionId, isCollapsed = false }) => {
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedThinking, setExpandedThinking] = useState<Set<string>>(new Set());
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'flow' | 'diagram'>('flow');

  useEffect(() => {
    if (!sessionId) {
      setLogs([]);
      return;
    }

    let isMounted = true;

    const fetchLogs = async (isInitial = false) => {
      if (isInitial) setIsLoading(true);
      try {
        const data = await getTelemetry(sessionId);
        if (isMounted) {
          // Only update if data actually changed
          setLogs(prev => {
            if (JSON.stringify(prev) === JSON.stringify(data)) return prev;
            return data;
          });
        }
      } catch (error) {
        console.error("Failed to fetch telemetry:", error);
      } finally {
        if (isInitial && isMounted) setIsLoading(false);
      }
    };

    fetchLogs(true);
    const interval = setInterval(() => fetchLogs(false), 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId]);

  const toggleThinking = (logId: string) => {
    setExpandedThinking(prev => {
      const next = new Set(prev);
      if (next.has(logId)) {
        next.delete(logId);
      } else {
        next.add(logId);
      }
      return next;
    });
  };

  const toggleMessage = (logId: string) => {
    setExpandedMessages(prev => {
      const next = new Set(prev);
      if (next.has(logId)) {
        next.delete(logId);
      } else {
        next.add(logId);
      }
      return next;
    });
  };

  // Determine which path was taken based on most recent logs
  const getRoutingPath = () => {
    // Use last 6 logs (most recent query)
    const recentLogs = logs.slice(-6);
    const agentNames = recentLogs.map(l => l.agentName);
    const hasKpiGateway = agentNames.includes("KPI Gateway");
    const hasAnalyst = agentNames.includes("Analyst");

    if (hasAnalyst) return "analyst";
    if (hasKpiGateway) return "kpi";
    return null;
  };

  const routingPath = getRoutingPath();

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case "Supervisor":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4M12 8h.01" />
          </svg>
        );
      case "KPI Gateway":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3v18h18" />
            <path d="M18 17V9M13 17V5M8 17v-3" />
          </svg>
        );
      case "Analyst":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          </svg>
        );
      case "Validator":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        );
      case "Visualization":
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        );
      default:
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
          </svg>
        );
    }
  };

  const getAgentColor = (agentName: string) => {
    switch (agentName) {
      case "Supervisor": return { bg: "rgba(139, 92, 246, 0.2)", border: "#8b5cf6", text: "#a78bfa" };
      case "KPI Gateway": return { bg: "rgba(16, 185, 129, 0.2)", border: "#10b981", text: "#34d399" };
      case "Analyst": return { bg: "rgba(59, 130, 246, 0.2)", border: "#3b82f6", text: "#60a5fa" };
      case "Validator": return { bg: "rgba(245, 158, 11, 0.2)", border: "#f59e0b", text: "#fbbf24" };
      case "Visualization": return { bg: "rgba(236, 72, 153, 0.2)", border: "#ec4899", text: "#f472b6" };
      default: return { bg: "rgba(107, 114, 128, 0.2)", border: "#6b7280", text: "#9ca3af" };
    }
  };


  // Collapsed view - just icons
  if (isCollapsed) {
    return (
      <div className="agent-flow-panel collapsed">
        <div className="collapsed-icons">
          {logs.length === 0 ? (
            <div className="collapsed-empty">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4M12 8h.01" />
              </svg>
            </div>
          ) : (
            logs.map((log, index) => (
              <div
                key={log.id}
                className={`collapsed-icon ${log.status}`}
                title={`${log.agentName}: ${log.outputSummary}`}
                style={{ borderColor: getAgentColor(log.agentName).border }}
              >
                {getAgentIcon(log.agentName)}
                {index < logs.length - 1 && <div className="collapsed-connector" />}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // Render the premium routing flow diagram
  const renderRoutingDiagram = () => {
    if (!routingPath) return null;

    return (
      <div className="premium-diagram">
        <div className="diagram-header">
          <div className="diagram-title-row">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span>Agent Pipeline</span>
          </div>
          <div className="diagram-status">
            <span className="status-dot active" />
            <span>Active</span>
          </div>
        </div>

        <div className="pipeline-container">
          {/* Query Node */}
          <div className="pipeline-node start">
            <div className="node-glow" />
            <div className="node-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <span className="node-label">Query</span>
          </div>

          <div className="pipeline-arrow" />

          {/* Supervisor Node */}
          <div className="pipeline-node router">
            <div className="node-glow purple" />
            <div className="node-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4M12 8h.01" />
              </svg>
            </div>
            <span className="node-label">Supervisor</span>
            <span className="node-badge">Router</span>
          </div>

          {/* Branch */}
          <div className="pipeline-branch">
            <div className={`branch-path left ${routingPath === 'kpi' ? 'active' : ''}`}>
              <svg viewBox="0 0 60 50" className="branch-svg">
                <path d="M30 0 L10 25 L10 50" fill="none" strokeWidth="2" />
              </svg>
            </div>
            <div className={`branch-path right ${routingPath === 'analyst' ? 'active' : ''}`}>
              <svg viewBox="0 0 60 50" className="branch-svg">
                <path d="M30 0 L50 25 L50 50" fill="none" strokeWidth="2" />
              </svg>
            </div>
          </div>

          {/* Agent Nodes Side by Side */}
          <div className="pipeline-agents">
            <div className={`pipeline-node agent ${routingPath === 'kpi' ? 'active' : 'inactive'}`}>
              <div className="node-glow green" />
              <div className="node-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 3v18h18" />
                  <path d="M18 17V9M13 17V5M8 17v-3" />
                </svg>
              </div>
              <span className="node-label">KPI Mart</span>
              <span className="node-sublabel">Summary Tables</span>
            </div>

            <div className={`pipeline-node agent ${routingPath === 'analyst' ? 'active' : 'inactive'}`}>
              <div className="node-glow blue" />
              <div className="node-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                </svg>
              </div>
              <span className="node-label">Analyst</span>
              <span className="node-sublabel">Transaction Data</span>
            </div>
          </div>

          {/* Merge */}
          <div className="pipeline-merge">
            <div className={`merge-path left ${routingPath === 'kpi' ? 'active' : ''}`}>
              <svg viewBox="0 0 60 50" className="merge-svg">
                <path d="M10 0 L10 25 L30 50" fill="none" strokeWidth="2" />
              </svg>
            </div>
            <div className={`merge-path right ${routingPath === 'analyst' ? 'active' : ''}`}>
              <svg viewBox="0 0 60 50" className="merge-svg">
                <path d="M50 0 L50 25 L30 50" fill="none" strokeWidth="2" />
              </svg>
            </div>
          </div>

          {/* Validator Node */}
          <div className="pipeline-node processor">
            <div className="node-glow yellow" />
            <div className="node-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <span className="node-label">Validator</span>
          </div>

          <div className="pipeline-arrow" />

          {/* Visualization Node */}
          <div className="pipeline-node processor">
            <div className="node-glow pink" />
            <div className="node-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="node-label">Visualization</span>
          </div>

          <div className="pipeline-arrow" />

          {/* Response Node */}
          <div className="pipeline-node end">
            <div className="node-glow" />
            <div className="node-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <span className="node-label">Response</span>
          </div>
        </div>

        <div className="diagram-legend">
          <div className="legend-item">
            <span className="legend-dot active" />
            <span>Active</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot inactive" />
            <span>Skipped</span>
          </div>
        </div>
      </div>
    );
  };

  if (!sessionId || logs.length === 0) {
    return (
      <div className="agent-flow-panel">
        <div className="empty-state">
          <div className="empty-animation">
            <div className="empty-circle" />
            <div className="empty-circle delay-1" />
            <div className="empty-circle delay-2" />
          </div>
          <div className="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <p className="empty-title">Waiting for query</p>
          <p className="empty-subtitle">Ask a question to see the agent flow</p>
        </div>
      </div>
    );
  }

  return (
    <div className="agent-flow-panel">
      <div className="panel-tabs">
        <button
          className={`tab-btn ${activeTab === 'flow' ? 'active' : ''}`}
          onClick={() => setActiveTab('flow')}
        >
          Timeline
        </button>
        <button
          className={`tab-btn ${activeTab === 'diagram' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagram')}
        >
          Diagram
        </button>
        <span className="steps-count">{logs.length} steps</span>
      </div>

      {activeTab === 'diagram' ? (
        renderRoutingDiagram()
      ) : (
        <div className="logs-section">
          <div className="flow-content">
            {/* Show last 6 logs (most recent query) in chronological order */}
            {logs.slice(-6).map((log, index, displayedLogs) => {
              const nextAgent = index < displayedLogs.length - 1 ? displayedLogs[index + 1].agentName : null;
              const isThinkingExpanded = expandedThinking.has(log.id);
              const isMessageExpanded = expandedMessages.has(log.id);
              const colors = getAgentColor(log.agentName);

              return (
                <div key={log.id} className={`flow-step ${log.status}`}>
                  {/* Connection Line */}
                  <div className="step-timeline">
                    <div
                      className="timeline-dot"
                      style={{ background: colors.border, boxShadow: `0 0 12px ${colors.border}` }}
                    />
                    {index < displayedLogs.length - 1 && (
                      <div className="timeline-line" style={{ background: `linear-gradient(180deg, ${colors.border} 0%, ${getAgentColor(displayedLogs[index + 1].agentName).border} 100%)` }} />
                    )}
                  </div>

                  {/* Content Card */}
                  <div
                    className="step-card"
                    style={{ borderColor: colors.border, background: colors.bg }}
                  >
                    <div className="card-header">
                      <div className="agent-badge" style={{ color: colors.text }}>
                        {getAgentIcon(log.agentName)}
                        <span>{log.agentName}</span>
                      </div>
                      <div className="card-meta">
                        <span className={`status-badge ${log.status}`}>
                          {log.status === "success" ? (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          ) : (
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                              <line x1="18" y1="6" x2="6" y2="18" />
                              <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                          )}
                        </span>
                        <span className="timestamp">
                          {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                    </div>

                    <p className="output-summary">{log.outputSummary}</p>

                    {/* Action Buttons */}
                    <div className="card-actions">
                      {log.reasoningSummary && (
                        <button
                          className={`action-btn thinking ${isThinkingExpanded ? 'expanded' : ''}`}
                          onClick={() => toggleThinking(log.id)}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                          </svg>
                          <span>Thinking</span>
                          <svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>
                      )}

                      {nextAgent && (
                        <button
                          className={`action-btn message ${isMessageExpanded ? 'expanded' : ''}`}
                          onClick={() => toggleMessage(log.id)}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 2L11 13" />
                            <path d="M22 2l-7 20-4-9-9-4 20-7z" />
                          </svg>
                          <span>→ {nextAgent}</span>
                          <svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="6 9 12 15 18 9" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Expandable Sections */}
                    {isThinkingExpanded && log.reasoningSummary && (
                      <div className="expandable-content thinking-content">
                        <div className="content-header">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                          </svg>
                          <span>Agent Reasoning</span>
                        </div>
                        <p>{log.reasoningSummary}</p>
                      </div>
                    )}

                    {isMessageExpanded && nextAgent && (
                      <div className="expandable-content message-content">
                        <div className="message-flow">
                          <div className="flow-from" style={{ borderColor: colors.border }}>
                            {log.agentName}
                          </div>
                          <div className="flow-arrow">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <line x1="5" y1="12" x2="19" y2="12" />
                              <polyline points="12 5 19 12 12 19" />
                            </svg>
                          </div>
                          <div className="flow-to" style={{ borderColor: getAgentColor(nextAgent).border }}>
                            {nextAgent}
                          </div>
                        </div>
                        <div className="message-details">
                          <div className="detail-row">
                            <span className="detail-label">Output:</span>
                            <span className="detail-value">{log.outputSummary}</span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Next Input:</span>
                            <span className="detail-value">{logs[index + 1]?.inputSummary || "Processing..."}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flow-step loading">
                <div className="step-timeline">
                  <div className="timeline-dot loading" />
                </div>
                <div className="step-card loading-card">
                  <div className="loading-pulse">
                    <div className="pulse-dot" />
                    <div className="pulse-dot" />
                    <div className="pulse-dot" />
                  </div>
                  <span>Processing...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentFlowPanel;
