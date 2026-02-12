import React, { useState, useEffect } from "react";
import { AgentLogEntry } from "../types";
import { getTelemetry } from "../api/chatApi";
import "./AgentTelemetryPanel.css";

interface AgentTelemetryPanelProps {
  sessionId: string | null;
}

const AgentTelemetryPanel: React.FC<AgentTelemetryPanelProps> = ({
  sessionId,
}) => {
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setLogs([]);
      return;
    }

    const fetchLogs = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getTelemetry(sessionId);
        setLogs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch logs");
      } finally {
        setIsLoading(false);
      }
    };

    fetchLogs();

    // Poll for updates every 3 seconds while active
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const getAgentIcon = (agentName: string) => {
    const icons: Record<string, string> = {
      Supervisor: "🎯",
      "KPI Gateway": "🔌",
      Analyst: "📊",
      Validator: "✅",
      Visualization: "📈",
    };
    return icons[agentName] || "⚙️";
  };

  const getStatusBadge = (status: string) => {
    return status === "success" ? (
      <span className="status-badge success">✓</span>
    ) : (
      <span className="status-badge error">✗</span>
    );
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  if (!sessionId) {
    return (
      <div className="telemetry-panel empty">
        <div className="empty-state">
          <span className="empty-icon">🔍</span>
          <p>Agent telemetry will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="telemetry-panel">
      <div className="telemetry-header">
        <h3>🤖 Agent Telemetry</h3>
        <span className="log-count">{logs.length} steps</span>
      </div>

      <div className="telemetry-content">
        {isLoading && logs.length === 0 && (
          <div className="loading-state">Loading...</div>
        )}

        {error && <div className="error-state">{error}</div>}

        {logs.length === 0 && !isLoading && !error && (
          <div className="empty-logs">No agent activity yet</div>
        )}

        <div className="timeline">
          {logs.map((log, index) => (
            <div
              key={log.id}
              className={`timeline-item ${log.status}`}
              onClick={() => toggleExpand(log.id)}
            >
              <div className="timeline-marker">
                <div className="marker-dot"></div>
                {index < logs.length - 1 && <div className="marker-line"></div>}
              </div>

              <div className="timeline-content">
                <div className="log-header">
                  <span className="agent-icon">{getAgentIcon(log.agentName)}</span>
                  <span className="agent-name">{log.agentName}</span>
                  {getStatusBadge(log.status)}
                  <span className="log-time">{formatTime(log.timestamp)}</span>
                </div>

                <div className="log-summary">
                  <div className="summary-row">
                    <span className="label">Input:</span>
                    <span className="value">{log.inputSummary}</span>
                  </div>
                  <div className="summary-row">
                    <span className="label">Output:</span>
                    <span className="value">{log.outputSummary}</span>
                  </div>
                </div>

                {expandedIds.has(log.id) && log.reasoningSummary && (
                  <div className="log-details">
                    <div className="reasoning">
                      <span className="label">Reasoning:</span>
                      <p>{log.reasoningSummary}</p>
                    </div>
                  </div>
                )}

                {log.reasoningSummary && (
                  <button className="expand-btn">
                    {expandedIds.has(log.id) ? "▲ Less" : "▼ More"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AgentTelemetryPanel;
