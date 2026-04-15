import React, { useState } from "react";
import { AgentLogEntry } from "../types";
import "./AgentFlowPanel.css";

interface AgentFlowPanelProps {
  sessionId: string | null;
  isCollapsed?: boolean;
  logs?: AgentLogEntry[];
}

type RoutingPath = "lifecycle" | "kpi" | null;

interface PipelineStage {
  key: string;
  label: string;
  sublabel?: string;
  colorClass: string;
  glowColor: string;
  icon: React.ReactNode;
}

const LIFECYCLE_STAGES: PipelineStage[] = [
  {
    key: "query",
    label: "Query",
    colorClass: "start",
    glowColor: "#7c3a5c",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    key: "supervisor",
    label: "Supervisor",
    sublabel: "Router",
    colorClass: "supervisor",
    glowColor: "#8b5cf6",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4M12 8h.01" />
      </svg>
    ),
  },
  {
    key: "discovery",
    label: "Discovery",
    sublabel: "Asset Scan",
    colorClass: "discovery",
    glowColor: "#06b6d4",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    key: "profiling",
    label: "Profiling",
    sublabel: "Data Analysis",
    colorClass: "profiling",
    glowColor: "#3b82f6",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      </svg>
    ),
  },
  {
    key: "rules",
    label: "Rules",
    sublabel: "Validation Rules",
    colorClass: "rules",
    glowColor: "#f59e0b",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    key: "reporting",
    label: "Reporting",
    sublabel: "Score & Report",
    colorClass: "reporting",
    glowColor: "#10b981",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    key: "remediation",
    label: "Remediation",
    sublabel: "Fix & Heal",
    colorClass: "remediation",
    glowColor: "#ef4444",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
      </svg>
    ),
  },
  {
    key: "response",
    label: "Response",
    colorClass: "end",
    glowColor: "#7c3a5c",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
];

const KPI_STAGES: PipelineStage[] = [
  {
    key: "query",
    label: "Query",
    colorClass: "start",
    glowColor: "#7c3a5c",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    key: "supervisor",
    label: "Supervisor",
    sublabel: "Router",
    colorClass: "supervisor",
    glowColor: "#8b5cf6",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4M12 8h.01" />
      </svg>
    ),
  },
  {
    key: "kpi",
    label: "KPI Agent",
    sublabel: "Metric Computation",
    colorClass: "kpi",
    glowColor: "#10b981",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3v18h18" />
        <path d="M18 17V9M13 17V5M8 17v-3" />
      </svg>
    ),
  },
  {
    key: "validator",
    label: "Validator",
    sublabel: "Quality Check",
    colorClass: "validator",
    glowColor: "#eab308",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
  {
    key: "response",
    label: "Response",
    colorClass: "end",
    glowColor: "#7c3a5c",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
];

const AgentFlowPanel: React.FC<AgentFlowPanelProps> = ({ sessionId, isCollapsed = false, logs = [] }) => {
  const [expandedThinking, setExpandedThinking] = useState<Set<string>>(new Set());
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'flow' | 'diagram' | 'roadmap'>('flow');
  const isLoading = false;

  const toggleThinking = (logId: string) => {
    setExpandedThinking(prev => {
      const next = new Set(prev);
      if (next.has(logId)) { next.delete(logId); } else { next.add(logId); }
      return next;
    });
  };

  const toggleMessage = (logId: string) => {
    setExpandedMessages(prev => {
      const next = new Set(prev);
      if (next.has(logId)) { next.delete(logId); } else { next.add(logId); }
      return next;
    });
  };

  const getRoutingPath = (): RoutingPath => {
    const agentNames = logs.map(l => l.agentName.toLowerCase());
    const hasLifecycle = agentNames.some(n =>
      n.includes("discovery") || n.includes("profiling") || n.includes("rules") ||
      n.includes("reporting") || n.includes("remediation")
    );
    const hasKpi = agentNames.some(n => n.includes("kpi"));
    if (hasLifecycle) return "lifecycle";
    if (hasKpi) return "kpi";
    return null;
  };

  const routingPath = getRoutingPath();

  const getAgentIcon = (agentName: string) => {
    const name = agentName.toLowerCase();
    if (name.includes("supervisor")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>);
    }
    if (name.includes("kpi")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M18 17V9M13 17V5M8 17v-3" /></svg>);
    }
    if (name.includes("discovery")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>);
    }
    if (name.includes("profiling")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /></svg>);
    }
    if (name.includes("rules")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>);
    }
    if (name.includes("reporting")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>);
    }
    if (name.includes("remediation")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></svg>);
    }
    if (name.includes("validator")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>);
    }
    if (name.includes("visualization")) {
      return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>);
    }
    return (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /></svg>);
  };

  const getAgentColor = (agentName: string) => {
    const name = agentName.toLowerCase();
    if (name.includes("supervisor")) return { bg: "rgba(139, 92, 246, 0.2)", border: "#8b5cf6", text: "#a78bfa" };
    if (name.includes("kpi")) return { bg: "rgba(16, 185, 129, 0.2)", border: "#10b981", text: "#34d399" };
    if (name.includes("discovery")) return { bg: "rgba(6, 182, 212, 0.2)", border: "#06b6d4", text: "#22d3ee" };
    if (name.includes("profiling")) return { bg: "rgba(59, 130, 246, 0.2)", border: "#3b82f6", text: "#60a5fa" };
    if (name.includes("rules")) return { bg: "rgba(245, 158, 11, 0.2)", border: "#f59e0b", text: "#fbbf24" };
    if (name.includes("reporting")) return { bg: "rgba(16, 185, 129, 0.2)", border: "#10b981", text: "#34d399" };
    if (name.includes("remediation")) return { bg: "rgba(239, 68, 68, 0.2)", border: "#ef4444", text: "#f87171" };
    if (name.includes("validator")) return { bg: "rgba(234, 179, 8, 0.2)", border: "#eab308", text: "#facc15" };
    if (name.includes("visualization")) return { bg: "rgba(236, 72, 153, 0.2)", border: "#ec4899", text: "#f472b6" };
    return { bg: "rgba(107, 114, 128, 0.2)", border: "#6b7280", text: "#9ca3af" };
  };

  const isStageActive = (stageKey: string): boolean => {
    const agentNames = logs.map(l => l.agentName.toLowerCase());
    if (stageKey === "query" || stageKey === "response") return logs.length > 0;
    return agentNames.some(n => n.includes(stageKey));
  };

  if (isCollapsed) {
    return (
      <div className="agent-flow-panel collapsed">
        <div className="collapsed-icons">
          {logs.length === 0 ? (
            <div className="collapsed-empty">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
              </svg>
            </div>
          ) : (
            logs.map((log, index) => (
              <div key={log.id} className={`collapsed-icon ${log.status}`} title={`${log.agentName}: ${log.outputSummary}`} style={{ borderColor: getAgentColor(log.agentName).border }}>
                {getAgentIcon(log.agentName)}
                {index < logs.length - 1 && <div className="collapsed-connector" />}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  const renderLifecyclePipeline = () => {
    const stages = routingPath === "kpi" ? KPI_STAGES : LIFECYCLE_STAGES;

    return (
      <div className="premium-diagram">
        <div className="diagram-header">
          <div className="diagram-title-row">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span>{routingPath === "kpi" ? "KPI Pipeline" : "DQ Lifecycle Pipeline"}</span>
          </div>
          <div className="diagram-status">
            <span className="status-dot active" />
            <span>Active</span>
          </div>
        </div>

        <div className="lifecycle-pipeline">
          {stages.map((stage, index) => {
            const active = isStageActive(stage.key);
            const isLast = index === stages.length - 1;

            return (
              <div key={stage.key} className="lifecycle-stage-wrapper">
                <div className={`lifecycle-node ${stage.colorClass} ${active ? 'active' : 'skipped'}`}>
                  <div className="lifecycle-node-circle" style={{ borderColor: active ? stage.glowColor : undefined }}>
                    {active && (
                      <div className="node-glow-ring" style={{ background: stage.glowColor }} />
                    )}
                    <div className="lifecycle-node-icon" style={active ? { background: `linear-gradient(135deg, ${stage.glowColor}, ${stage.glowColor}dd)` } : undefined}>
                      {stage.icon}
                    </div>
                    {active && (
                      <div className="lifecycle-check">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="lifecycle-node-info">
                    <span className="lifecycle-node-label" style={active ? { color: stage.glowColor } : undefined}>
                      {stage.label}
                    </span>
                    {stage.sublabel && (
                      <span className="lifecycle-node-sublabel">{stage.sublabel}</span>
                    )}
                  </div>
                </div>

                {!isLast && (
                  <div className={`lifecycle-connector ${active && isStageActive(stages[index + 1].key) ? 'active' : ''}`}>
                    <div
                      className="lifecycle-connector-line"
                      style={
                        active && isStageActive(stages[index + 1].key)
                          ? { background: `linear-gradient(180deg, ${stage.glowColor} 0%, ${stages[index + 1].glowColor} 100%)` }
                          : undefined
                      }
                    />
                  </div>
                )}
              </div>
            );
          })}
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

  const renderRoadmap = () => {
    return (
      <div className="roadmap-scroll">
        {/* Section 1: DQ Lifecycle Pipeline */}
        <div className="roadmap-horizon">
          <div className="horizon-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span>DQ Lifecycle Pipeline</span>
            <span className="horizon-badge active">ACTIVE</span>
          </div>
          <div className="roadmap-nodes">
            <div className="roadmap-node today">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Discovery Agent</span>
                <span className="roadmap-node-desc">Scans tables, builds metadata catalog</span>
              </div>
            </div>
            <div className="roadmap-node today">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Profiling Agent</span>
                <span className="roadmap-node-desc">5-dimension quality scoring (Completeness, Accuracy, Uniqueness, Consistency, Timeliness)</span>
              </div>
            </div>
            <div className="roadmap-node today">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Rules Agent</span>
                <span className="roadmap-node-desc">Validates Collibra governance rules against data</span>
              </div>
            </div>
            <div className="roadmap-node today">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Reporting Agent</span>
                <span className="roadmap-node-desc">DQ scorecard, executive summary, visualizations</span>
              </div>
            </div>
            <div className="roadmap-node today">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Remediation Agent</span>
                <span className="roadmap-node-desc">Root cause analysis, prioritized fix recommendations</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Proactive Automation */}
        <div className="roadmap-horizon">
          <div className="horizon-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
            <span>Proactive Automation</span>
            <span className="horizon-badge coming-soon-amber">COMING SOON</span>
          </div>
          <div className="roadmap-nodes">
            <div className="roadmap-node next-quarter">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Scheduled DQ Runs</span>
                <span className="roadmap-node-desc">Automated daily/weekly lifecycle scans</span>
              </div>
            </div>
            <div className="roadmap-node next-quarter">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Steward Alerting</span>
                <span className="roadmap-node-desc">Email + Teams notifications on threshold breach</span>
              </div>
            </div>
            <div className="roadmap-node next-quarter">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Jira Auto-Ticketing</span>
                <span className="roadmap-node-desc">DQ violations auto-create Jira tickets with context</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Self-Healing Pipeline */}
        <div className="roadmap-horizon">
          <div className="horizon-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
            <span>Self-Healing Pipeline</span>
            <span className="horizon-badge coming-soon-purple">COMING SOON</span>
          </div>
          <div className="roadmap-nodes">
            <div className="roadmap-node future">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Anomaly Detection</span>
                <span className="roadmap-node-desc">Continuous monitoring for data drift</span>
              </div>
            </div>
            <div className="roadmap-node future">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Root Cause Tracing</span>
                <span className="roadmap-node-desc">Automated lineage analysis to corruption source</span>
              </div>
            </div>
            <div className="roadmap-node hitl">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">
                  Human-in-the-Loop
                  <span className="hitl-pulse" />
                </span>
                <span className="roadmap-node-desc">Data steward reviews and approves fix</span>
              </div>
            </div>
            <div className="roadmap-node future">
              <div className="roadmap-node-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                </svg>
              </div>
              <div className="roadmap-node-text">
                <span className="roadmap-node-label">Auto-Remediation</span>
                <span className="roadmap-node-desc">Apply fix with audit trail and rollback</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Agent Mesh */}
        <div className="roadmap-horizon">
          <div className="horizon-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
            <span>Agent Mesh</span>
            <span className="horizon-badge coming-soon-purple">COMING SOON</span>
          </div>
          <div className="agent-mesh-container">
            <div className="roadmap-subsection-label">Hub-and-Spoke Orchestration</div>
            <div className="mesh-satellites">
              <div className="mesh-agent-node">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                  <line x1="4" y1="22" x2="4" y2="15" />
                </svg>
                <span className="mesh-agent-label">MDM Agent</span>
                <span className="mesh-agent-desc">Master Data Management</span>
              </div>
              <div className="mesh-connector-vertical">{'\u2502'}</div>
              <div className="mesh-connector-row">
                <div className="mesh-agent-node">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                  </svg>
                  <span className="mesh-agent-label">Lineage Agent</span>
                  <span className="mesh-agent-desc">Data Lineage Tracking</span>
                </div>
                <span className="mesh-connector">{'\u2014'}</span>
                <div className="mesh-orchestrator">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
                  </svg>
                  <span>DQ Orchestrator</span>
                </div>
                <span className="mesh-connector">{'\u2014'}</span>
                <div className="mesh-agent-node">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  <span className="mesh-agent-label">Compliance Agent</span>
                  <span className="mesh-agent-desc">GxP Regulatory</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const hasLogs = sessionId && logs.length > 0;

  const renderEmptyState = () => (
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
  );

  const renderTimeline = () => (
    <div className="logs-section">
      <div className="flow-content">
        {logs.map((log, index) => {
          const displayedLogs = logs;
          const nextAgent = index < displayedLogs.length - 1 ? displayedLogs[index + 1].agentName : null;
          const isThinkingExpanded = expandedThinking.has(log.id);
          const isMessageExpanded = expandedMessages.has(log.id);
          const colors = getAgentColor(log.agentName);

          return (
            <div key={log.id} className={`flow-step ${log.status}`}>
              <div className="step-timeline">
                <div className="timeline-dot" style={{ background: colors.border, boxShadow: `0 0 12px ${colors.border}` }} />
                {index < displayedLogs.length - 1 && (
                  <div className="timeline-line" style={{ background: `linear-gradient(180deg, ${colors.border} 0%, ${getAgentColor(displayedLogs[index + 1].agentName).border} 100%)` }} />
                )}
              </div>

              <div className="step-card" style={{ borderColor: colors.border, background: colors.bg }}>
                <div className="card-header">
                  <div className="agent-badge" style={{ color: colors.text }}>
                    {getAgentIcon(log.agentName)}
                    <span>{log.agentName}</span>
                  </div>
                  <div className="card-meta">
                    <span className={`status-badge ${log.status}`}>
                      {log.status === "success" ? (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                      ) : (
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                      )}
                    </span>
                    <span className="timestamp">{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                  </div>
                </div>

                <p className="output-summary">{log.outputSummary}</p>

                <div className="card-actions">
                  {log.reasoningSummary && (
                    <button className={`action-btn thinking ${isThinkingExpanded ? 'expanded' : ''}`} onClick={() => toggleThinking(log.id)}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                      <span>Thinking</span>
                      <svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9" /></svg>
                    </button>
                  )}
                  {nextAgent && (
                    <button className={`action-btn message ${isMessageExpanded ? 'expanded' : ''}`} onClick={() => toggleMessage(log.id)}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" /></svg>
                      <span>{'\u2192'} {nextAgent}</span>
                      <svg className="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9" /></svg>
                    </button>
                  )}
                </div>

                {isThinkingExpanded && log.reasoningSummary && (
                  <div className="expandable-content thinking-content">
                    <div className="content-header">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                      <span>Agent Reasoning</span>
                    </div>
                    <p>{log.reasoningSummary}</p>
                  </div>
                )}

                {isMessageExpanded && nextAgent && (
                  <div className="expandable-content message-content">
                    <div className="message-flow">
                      <div className="flow-from" style={{ borderColor: colors.border }}>{log.agentName}</div>
                      <div className="flow-arrow">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="5" y1="12" x2="19" y2="12" />
                          <polyline points="12 5 19 12 12 19" />
                        </svg>
                      </div>
                      <div className="flow-to" style={{ borderColor: getAgentColor(nextAgent).border }}>{nextAgent}</div>
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
            <div className="step-timeline"><div className="timeline-dot loading" /></div>
            <div className="step-card loading-card">
              <div className="loading-pulse"><div className="pulse-dot" /><div className="pulse-dot" /><div className="pulse-dot" /></div>
              <span>Processing...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="agent-flow-panel">
      <div className="panel-tabs">
        <button className={`tab-btn ${activeTab === 'flow' ? 'active' : ''}`} onClick={() => setActiveTab('flow')}>Timeline</button>
        <button className={`tab-btn ${activeTab === 'diagram' ? 'active' : ''}`} onClick={() => setActiveTab('diagram')}>Diagram</button>
        <button className={`tab-btn roadmap-tab-btn ${activeTab === 'roadmap' ? 'active' : ''}`} onClick={() => setActiveTab('roadmap')}>Architecture</button>
        {hasLogs && <span className="steps-count">{logs.length} steps</span>}
      </div>

      {activeTab === 'roadmap' ? (
        renderRoadmap()
      ) : activeTab === 'diagram' ? (
        hasLogs ? renderLifecyclePipeline() : renderEmptyState()
      ) : (
        hasLogs ? renderTimeline() : renderEmptyState()
      )}
    </div>
  );
};

export default AgentFlowPanel;
