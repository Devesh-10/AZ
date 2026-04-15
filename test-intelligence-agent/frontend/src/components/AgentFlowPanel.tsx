import { useState } from "react";
import {
  Workflow, Clock, CheckCircle2, XCircle, AlertCircle,
  Loader2, SkipForward, ChevronDown, ChevronRight,
  GitBranch, FileSearch, TestTube2, Database, Play,
  Bug, Wrench, ClipboardCheck, Brain
} from "lucide-react";
import type { AgentLogEntry } from "../types";
import "./AgentFlowPanel.css";

const STEPS = [
  { num: 0, name: "Orchestrator", icon: Brain, color: "var(--step-0-color)", conditional: false },
  { num: 1, name: "Requirement Agent", icon: FileSearch, color: "var(--step-1-color)", conditional: false },
  { num: 2, name: "Test Case Generation", icon: TestTube2, color: "var(--step-2-color)", conditional: false },
  { num: 3, name: "Synthetic Data", icon: Database, color: "var(--step-3-color)", conditional: true, decision: "Need test data?" },
  { num: 4, name: "Execution Agent", icon: Play, color: "var(--step-4-color)", conditional: false },
  { num: 5, name: "Failure Analysis", icon: Bug, color: "var(--step-5-color)", conditional: true, decision: "All tests pass?" },
  { num: 6, name: "Code Refactor", icon: Wrench, color: "var(--step-6-color)", conditional: true, decision: "Code bug?" },
  { num: 7, name: "Reporting Agent", icon: ClipboardCheck, color: "var(--step-7-color)", conditional: false },
];

const TIMING_BADGES: Record<number, { agent: string; manual: string }> = {
  1: { agent: "30s", manual: "3 days" },
  2: { agent: "30s", manual: "3 days" },
  3: { agent: "15s", manual: "1 day" },
  4: { agent: "2 min", manual: "2 days" },
  5: { agent: "30s", manual: "1 day" },
  6: { agent: "25s", manual: "2 days" },
  7: { agent: "15s", manual: "1 day" },
};

interface Props {
  logs: AgentLogEntry[];
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function AgentFlowPanel({ logs, isCollapsed, onToggleCollapse }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"timeline" | "diagram">("timeline");

  const getLogForStep = (stepNum: number): AgentLogEntry | undefined =>
    logs.find((l) => l.stepNumber === stepNum);

  const getStepStatus = (stepNum: number) => {
    const log = getLogForStep(stepNum);
    if (!log) return "pending";
    if (log.status === "running") return "running";
    if (log.status === "skipped" || !log.wasExecuted) return "skipped";
    if (log.status === "error") return "error";
    return "completed";
  };

  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case "completed": return <CheckCircle2 size={14} />;
      case "running": return <Loader2 size={14} className="spin" />;
      case "error": return <XCircle size={14} />;
      case "skipped": return <SkipForward size={14} />;
      default: return <Clock size={14} />;
    }
  };

  if (isCollapsed) {
    return (
      <div className="agent-flow-collapsed" onClick={onToggleCollapse}>
        <Workflow size={18} />
        {logs.length > 0 && (
          <div className="collapsed-steps">
            {STEPS.map((s) => {
              const status = getStepStatus(s.num);
              return (
                <div key={s.num} className={`collapsed-dot ${status}`} style={{ background: status === "completed" ? s.color : undefined }} title={s.name} />
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="agent-flow-panel">
      <div className="afp-header">
        <div className="afp-header-left">
          <Workflow size={16} />
          <span>Agent Pipeline</span>
        </div>
        <div className="afp-tabs">
          <button className={`afp-tab ${viewMode === "timeline" ? "active" : ""}`} onClick={() => setViewMode("timeline")}>Flow</button>
          <button className={`afp-tab ${viewMode === "diagram" ? "active" : ""}`} onClick={() => setViewMode("diagram")}>Diagram</button>
        </div>
      </div>

      <div className="afp-body">
        {viewMode === "timeline" ? (
          <div className="timeline-view">
            {STEPS.map((step, i) => {
              const status = getStepStatus(step.num);
              const log = getLogForStep(step.num);
              const isExpanded = expandedStep === step.num;
              const Icon = step.icon;
              const timing = TIMING_BADGES[step.num];

              return (
                <div key={step.num}>
                  {step.conditional && step.decision && (
                    <div className="decision-diamond">
                      <div className="diamond-shape">
                        <GitBranch size={12} />
                      </div>
                      <span className="decision-text">{step.decision}</span>
                      {status === "skipped" && <span className="decision-skip">NO &raquo; Skip</span>}
                      {status !== "pending" && status !== "skipped" && <span className="decision-yes">YES &raquo;</span>}
                    </div>
                  )}

                  <div
                    className={`flow-step ${status} ${step.conditional ? "conditional" : ""}`}
                    style={{ "--step-color": step.color } as any}
                    onClick={() => setExpandedStep(isExpanded ? null : step.num)}
                  >
                    <div className="step-timeline">
                      <div className={`timeline-dot ${status}`} style={{ borderColor: step.color }}>
                        <Icon size={14} />
                      </div>
                      {i < STEPS.length - 1 && <div className="timeline-line" />}
                    </div>

                    <div className="step-content">
                      <div className="step-header">
                        <div className="step-title">
                          {step.num > 0 && <span className="step-num-badge" style={{ background: step.color }}>S{step.num}</span>}
                          <span className="step-name">{step.name}</span>
                          {step.conditional && <span className="conditional-tag">IF</span>}
                        </div>
                        <div className="step-right">
                          <div className={`status-badge ${status}`}>
                            <StatusIcon status={status} />
                            <span>{status}</span>
                          </div>
                          {log?.durationSeconds && (
                            <span className="duration">{log.durationSeconds.toFixed(1)}s</span>
                          )}
                        </div>
                      </div>

                      {timing && status === "completed" && (
                        <div className="timing-badge">
                          <span className="tb-agent">{timing.agent}</span>
                          <span className="tb-vs">vs</span>
                          <span className="tb-manual">{timing.manual}</span>
                        </div>
                      )}

                      {log && status !== "skipped" && (
                        <div className="step-summary">{log.outputSummary}</div>
                      )}

                      {log && log.reasoningSummary && (
                        <div className="step-expand-toggle">
                          {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                          <span>Agent Reasoning</span>
                        </div>
                      )}

                      {isExpanded && log?.reasoningSummary && (
                        <div className="step-reasoning">{log.reasoningSummary}</div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="diagram-view">
            <svg className="diagram-svg" viewBox="0 0 300 820" preserveAspectRatio="xMidYMid meet">
              {/* Connection lines */}
              <line x1="150" y1="40" x2="150" y2="75" stroke="rgba(255,255,255,0.15)" strokeWidth="2" />
              {STEPS.map((_, i) => {
                if (i >= STEPS.length - 1) return null;
                const y1 = 75 + i * 95 + 50;
                const y2 = 75 + (i + 1) * 95;
                const status = getStepStatus(STEPS[i].num);
                return (
                  <line key={i} x1="150" y1={y1} x2="150" y2={y2}
                    stroke={status === "completed" ? STEPS[i].color : "rgba(255,255,255,0.1)"}
                    strokeWidth="2"
                    strokeDasharray={STEPS[i + 1].conditional ? "6 3" : undefined}
                  />
                );
              })}

              {/* Start node */}
              <circle cx="150" cy="30" r="16" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
              <text x="150" y="35" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="10" fontWeight="600">Q</text>

              {/* Step nodes */}
              {STEPS.map((step, i) => {
                const y = 75 + i * 95;
                const status = getStepStatus(step.num);
                const isActive = status === "completed" || status === "running";
                const isSkipped = status === "skipped";

                return (
                  <g key={step.num}>
                    {/* Node rectangle */}
                    <rect
                      x="40" y={y} width="220" height="50" rx="8"
                      fill={isActive ? `${step.color}15` : "rgba(255,255,255,0.03)"}
                      stroke={isActive ? step.color : isSkipped ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.06)"}
                      strokeWidth={isActive ? "2" : "1"}
                      strokeDasharray={step.conditional && !isActive ? "4 3" : undefined}
                      opacity={isSkipped ? 0.4 : 1}
                    />

                    {/* Step number circle */}
                    <circle cx="65" cy={y + 25} r="12"
                      fill={isActive ? step.color : "rgba(255,255,255,0.08)"}
                    />
                    <text x="65" y={y + 29} textAnchor="middle"
                      fill="white" fontSize="10" fontWeight="700">
                      {step.num === 0 ? "R" : step.num}
                    </text>

                    {/* Name */}
                    <text x="85" y={y + 22} fill={isSkipped ? "rgba(255,255,255,0.3)" : "white"}
                      fontSize="11" fontWeight="600">{step.name}</text>

                    {/* Status text */}
                    <text x="85" y={y + 38}
                      fill={status === "completed" ? step.color : status === "skipped" ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.35)"}
                      fontSize="9">
                      {status === "completed" ? "Done" : status === "running" ? "Running..." : status === "skipped" ? "Skipped" : "Pending"}
                    </text>

                    {/* Timing badge */}
                    {TIMING_BADGES[step.num] && isActive && (
                      <g>
                        <rect x="195" y={y + 8} width="55" height="18" rx="9"
                          fill={step.color} opacity="0.2" />
                        <text x="222" y={y + 21} textAnchor="middle"
                          fill={step.color} fontSize="9" fontWeight="600">
                          {TIMING_BADGES[step.num].agent}
                        </text>
                      </g>
                    )}

                    {/* Conditional badge */}
                    {step.conditional && (
                      <g>
                        <rect x="195" y={y + 30} width="55" height="16" rx="8"
                          fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5" />
                        <text x="222" y={y + 41} textAnchor="middle"
                          fill="rgba(255,255,255,0.4)" fontSize="8" fontWeight="500">
                          IF NEEDED
                        </text>
                      </g>
                    )}

                    {/* Running animation */}
                    {status === "running" && (
                      <rect x="40" y={y} width="220" height="50" rx="8"
                        fill="none" stroke={step.color} strokeWidth="2"
                        className="pulse-border" />
                    )}
                  </g>
                );
              })}

              {/* End node */}
              <circle cx="150" cy={75 + STEPS.length * 95 - 30} r="16"
                fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
              <text x="150" y={75 + STEPS.length * 95 - 25} textAnchor="middle"
                fill="rgba(255,255,255,0.5)" fontSize="10" fontWeight="600">END</text>
            </svg>
          </div>
        )}
      </div>
    </div>
  );
}
