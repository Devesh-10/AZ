import { useState } from "react";
import {
  CheckCircle2, XCircle, AlertTriangle, ChevronDown, ChevronRight,
  Activity, Clock, BarChart3
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import type { TestResult, FailureAnalysis, CodeRefactorSuggestion } from "../types";
import "./TestResultsDashboard.css";

interface Props {
  testResults: TestResult[] | null;
  failureAnalyses: FailureAnalysis[] | null;
  refactorSuggestions: CodeRefactorSuggestion[] | null;
  passRate: number | null;
  platform: string;
}

const STATUS_COLORS = {
  PASS: "#10b981",
  FAIL: "#ef4444",
  SKIP: "#6b7280",
  ERROR: "#f59e0b",
};

export default function TestResultsDashboard({
  testResults, failureAnalyses, refactorSuggestions, passRate, platform
}: Props) {
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  if (!testResults) {
    return (
      <div className="trd-panel">
        <div className="trd-header">
          <BarChart3 size={14} />
          <span>Test Results</span>
        </div>
        <div className="trd-empty">
          <Activity size={32} />
          <p>Run a test to see results</p>
        </div>
      </div>
    );
  }

  const passed = testResults.filter((t) => t.status === "PASS").length;
  const failed = testResults.filter((t) => t.status === "FAIL").length;
  const total = testResults.length;
  const totalTime = testResults.reduce((s, t) => s + t.executionTimeSeconds, 0);

  const pieData = [
    { name: "Pass", value: passed, color: STATUS_COLORS.PASS },
    { name: "Fail", value: failed, color: STATUS_COLORS.FAIL },
  ];

  const getAnalysis = (testId: string) =>
    failureAnalyses?.find((a) => a.testId === testId);

  const getRefactor = (testId: string) =>
    refactorSuggestions?.find((r) => r.testId === testId);

  return (
    <div className="trd-panel">
      <div className="trd-header">
        <BarChart3 size={14} />
        <span>Test Results</span>
        <span className={`trd-badge ${failed > 0 ? "fail" : "pass"}`}>
          {passed}/{total} Passed
        </span>
      </div>

      <div className="trd-body">
        <div className="trd-summary">
          <div className="trd-chart">
            <ResponsiveContainer width="100%" height={100}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={28}
                  outerRadius={42}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="chart-center">
              <span className="chart-pct">{passRate?.toFixed(0) || Math.round((passed / total) * 100)}%</span>
            </div>
          </div>

          <div className="trd-metrics">
            <div className="trd-metric">
              <CheckCircle2 size={14} style={{ color: STATUS_COLORS.PASS }} />
              <span className="tm-value">{passed}</span>
              <span className="tm-label">Passed</span>
            </div>
            <div className="trd-metric">
              <XCircle size={14} style={{ color: STATUS_COLORS.FAIL }} />
              <span className="tm-value">{failed}</span>
              <span className="tm-label">Failed</span>
            </div>
            <div className="trd-metric">
              <Clock size={14} style={{ color: "#60a5fa" }} />
              <span className="tm-value">{totalTime.toFixed(1)}s</span>
              <span className="tm-label">Total</span>
            </div>
          </div>
        </div>

        <div className="trd-table">
          {testResults.map((tr) => {
            const isExpanded = expandedTest === tr.testId;
            const analysis = getAnalysis(tr.testId);
            const refactor = getRefactor(tr.testId);

            return (
              <div key={tr.testId} className={`trd-row ${tr.status.toLowerCase()}`}>
                <div className="trd-row-main" onClick={() => setExpandedTest(isExpanded ? null : tr.testId)}>
                  <div className={`trd-status ${tr.status.toLowerCase()}`}>
                    {tr.status === "PASS" ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                  </div>
                  <div className="trd-row-info">
                    <span className="trd-test-id">{tr.testId}</span>
                    <span className="trd-test-name">{tr.testName}</span>
                  </div>
                  <span className="trd-time">{tr.executionTimeSeconds.toFixed(1)}s</span>
                  {(analysis || tr.status === "FAIL") && (
                    isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                  )}
                </div>

                {isExpanded && (
                  <div className="trd-row-detail">
                    <div className="detail-item">
                      <span className="di-label">Result:</span>
                      <span className="di-value">{tr.actualResult}</span>
                    </div>
                    {tr.errorMessage && (
                      <div className="detail-item error">
                        <span className="di-label">Error:</span>
                        <span className="di-value">{tr.errorMessage}</span>
                      </div>
                    )}
                    {analysis && (
                      <div className="detail-analysis">
                        <div className="da-header">
                          <AlertTriangle size={12} />
                          <span>Failure Analysis</span>
                          <span className={`severity-badge ${analysis.severity.toLowerCase()}`}>
                            {analysis.severity}
                          </span>
                        </div>
                        <div className="detail-item">
                          <span className="di-label">Root Cause:</span>
                          <span className="di-value">{analysis.rootCause}</span>
                        </div>
                        <div className="detail-item">
                          <span className="di-label">Category:</span>
                          <span className="di-value">{analysis.category}</span>
                        </div>
                        <div className="detail-item">
                          <span className="di-label">Fix:</span>
                          <span className="di-value">{analysis.suggestedFix}</span>
                        </div>
                      </div>
                    )}
                    {refactor && (
                      <div className="detail-refactor">
                        <div className="da-header">
                          <span>Code Fix Suggestion</span>
                          <span className="confidence">{(refactor.confidence * 100).toFixed(0)}% confidence</span>
                        </div>
                        <pre className="code-block original">{refactor.originalCode}</pre>
                        <pre className="code-block suggested">{refactor.suggestedCode}</pre>
                        <p className="refactor-explanation">{refactor.explanation}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
