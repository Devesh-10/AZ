import { Zap, Clock, TrendingDown } from "lucide-react";
import type { TimingComparison } from "../types";
import "./BottomLineTable.css";

interface Props {
  timingComparison: TimingComparison | null;
}

export default function BottomLineTable({ timingComparison }: Props) {
  if (!timingComparison) return null;

  const { manualTotalHours, agentTotalSeconds, savingsPercent, steps } = timingComparison;

  const formatManualDays = (hours: number) => {
    if (hours >= 24) return `${Math.round(hours / 8)} days`;
    return `${hours} hrs`;
  };

  const agentMinutes = agentTotalSeconds / 60;

  return (
    <div className="btl-container">
      <div className="btl-title">
        <TrendingDown size={16} />
        <span>THE BOTTOM LINE</span>
      </div>

      <table className="btl-table">
        <thead>
          <tr>
            <th>Task</th>
            <th className="manual">Manual</th>
            <th className="agent">With Agent</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((step, i) => (
            <tr key={i}>
              <td className="task-name">{step.stepName}</td>
              <td className="manual">{step.manualTime}</td>
              <td className="agent">{step.agentTime}</td>
            </tr>
          ))}
          <tr className="total-row">
            <td className="task-name">TOTAL</td>
            <td className="manual">{formatManualDays(manualTotalHours)}</td>
            <td className="agent">~{agentMinutes.toFixed(0)} min</td>
          </tr>
        </tbody>
      </table>

      <div className="btl-visual">
        <div className="btl-bar-container">
          <div className="btl-bar manual-bar">
            <Clock size={12} />
            <span>{formatManualDays(manualTotalHours)}</span>
          </div>
          <div className="btl-arrow">&rarr;</div>
          <div className="btl-bar agent-bar">
            <Zap size={12} />
            <span>~{agentMinutes.toFixed(0)} min</span>
          </div>
        </div>
        <div className="btl-savings">
          <span className="savings-value">{savingsPercent.toFixed(1)}%</span>
          <span className="savings-label">Time Reduction</span>
        </div>
      </div>
    </div>
  );
}
