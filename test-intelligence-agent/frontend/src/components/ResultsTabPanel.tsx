import { useState } from "react";
import {
  FileText, FlaskConical, Play, Wrench, ClipboardCheck,
  ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertTriangle,
  Download, Clock, Activity, BarChart3, Code2, ShieldCheck,
  ArrowRight
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import type {
  RequirementField, TestCase, TestResult,
  FailureAnalysis, CodeRefactorSuggestion, ComplianceReport,
} from "../types";
import "./ResultsTabPanel.css";

interface Props {
  requirements: RequirementField[] | null;
  testCases: TestCase[] | null;
  testResults: TestResult[] | null;
  failureAnalyses: FailureAnalysis[] | null;
  refactorSuggestions: CodeRefactorSuggestion[] | null;
  passRate: number | null;
  complianceReport: ComplianceReport | null;
  platform: string;
}

type TabId = "requirements" | "test-suite" | "results" | "code-fixes" | "compliance";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "requirements", label: "Requirements", icon: <FileText size={13} /> },
  { id: "test-suite", label: "Test Suite", icon: <FlaskConical size={13} /> },
  { id: "results", label: "Results", icon: <Play size={13} /> },
  { id: "code-fixes", label: "Code Fixes", icon: <Wrench size={13} /> },
  { id: "compliance", label: "Compliance", icon: <ClipboardCheck size={13} /> },
];

const STATUS_COLORS = {
  PASS: "#10b981",
  FAIL: "#ef4444",
  SKIP: "#6b7280",
  ERROR: "#f59e0b",
};

const PRIORITY_COLORS: Record<string, string> = {
  Critical: "#ef4444",
  High: "#f59e0b",
  Medium: "#3b82f6",
  Low: "#6b7280",
};

const CATEGORY_COLORS: Record<string, string> = {
  Functional: "#8b5cf6",
  Boundary: "#f59e0b",
  Negative: "#ef4444",
  Compliance: "#10b981",
  Integration: "#3b82f6",
  "Metadata-Scenario": "#f97316",
};

export default function ResultsTabPanel({
  requirements, testCases, testResults,
  failureAnalyses, refactorSuggestions, passRate, complianceReport, platform
}: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("requirements");
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<number | null>(0);

  const hasData = requirements || testCases || testResults;

  // Determine badge counts for tabs
  const tabBadges: Partial<Record<TabId, number>> = {};
  if (requirements) tabBadges["requirements"] = requirements.length;
  if (testCases) tabBadges["test-suite"] = testCases.length;
  if (testResults) tabBadges["results"] = testResults.length;
  if (refactorSuggestions?.length) tabBadges["code-fixes"] = refactorSuggestions.length;
  if (complianceReport) tabBadges["compliance"] = complianceReport.sections.length;

  // Auto-switch to first populated tab
  const getActiveTab = () => {
    if (!hasData) return activeTab;
    return activeTab;
  };

  const toggleItem = (id: string) => {
    setExpandedItem(expandedItem === id ? null : id);
  };

  return (
    <div className="rtp-panel">
      <div className="rtp-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`rtp-tab ${getActiveTab() === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tabBadges[tab.id] !== undefined && (
              <span className="rtp-tab-badge">{tabBadges[tab.id]}</span>
            )}
          </button>
        ))}
      </div>

      <div className="rtp-content">
        {!hasData ? (
          <div className="rtp-empty">
            <Activity size={36} />
            <h3>Waiting for test execution</h3>
            <p>Select a platform and run a query to see generated artifacts</p>
          </div>
        ) : (
          <>
            {getActiveTab() === "requirements" && (
              <RequirementsView
                requirements={requirements}
                expandedItem={expandedItem}
                onToggle={toggleItem}
              />
            )}
            {getActiveTab() === "test-suite" && (
              <TestSuiteView
                testCases={testCases}
                expandedItem={expandedItem}
                onToggle={toggleItem}
              />
            )}
            {getActiveTab() === "results" && (
              <TestResultsView
                testResults={testResults}
                failureAnalyses={failureAnalyses}
                passRate={passRate}
                expandedItem={expandedItem}
                onToggle={toggleItem}
              />
            )}
            {getActiveTab() === "code-fixes" && (
              <CodeFixesView
                refactorSuggestions={refactorSuggestions}
                expandedItem={expandedItem}
                onToggle={toggleItem}
              />
            )}
            {getActiveTab() === "compliance" && (
              <ComplianceView
                report={complianceReport}
                expandedSection={expandedSection}
                onToggleSection={(i) => setExpandedSection(expandedSection === i ? null : i)}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}


// ============================================================
// Tab 1: Requirements
// ============================================================

function RequirementsView({ requirements, expandedItem, onToggle }: {
  requirements: RequirementField[] | null;
  expandedItem: string | null;
  onToggle: (id: string) => void;
}) {
  if (!requirements || requirements.length === 0) {
    return (
      <div className="rtp-empty-tab">
        <FileText size={28} />
        <p>No requirements extracted yet</p>
      </div>
    );
  }

  const mandatory = requirements.filter((r) => r.mandatory).length;

  return (
    <div className="rtp-tab-content">
      <div className="rtp-tab-summary">
        <div className="rtp-stat">
          <span className="rtp-stat-value">{requirements.length}</span>
          <span className="rtp-stat-label">Total Fields</span>
        </div>
        <div className="rtp-stat mandatory">
          <span className="rtp-stat-value">{mandatory}</span>
          <span className="rtp-stat-label">Mandatory</span>
        </div>
        <div className="rtp-stat">
          <span className="rtp-stat-value">{requirements.length - mandatory}</span>
          <span className="rtp-stat-label">Optional</span>
        </div>
      </div>

      <div className="rtp-list">
        {requirements.map((req) => (
          <div key={req.fieldId} className={`rtp-card ${expandedItem === req.fieldId ? "expanded" : ""}`}>
            <div className="rtp-card-header" onClick={() => onToggle(req.fieldId)}>
              <div className="rtp-card-left">
                <span className="rtp-card-id">{req.fieldId}</span>
                <span className="rtp-card-title">{req.fieldName}</span>
                {req.mandatory && <span className="badge mandatory">Required</span>}
              </div>
              <div className="rtp-card-right">
                <span className="badge data-type">{req.dataType}</span>
                {expandedItem === req.fieldId ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </div>
            </div>
            {expandedItem === req.fieldId && (
              <div className="rtp-card-body">
                <div className="detail-row">
                  <span className="detail-label">Source Spec:</span>
                  <span className="detail-value">{req.sourceSpec}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Data Type:</span>
                  <span className="detail-value">{req.dataType}</span>
                </div>
                {req.validationRules.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Validation Rules:</span>
                    <ul className="validation-list">
                      {req.validationRules.map((rule, i) => (
                        <li key={i}>{rule}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


// ============================================================
// Tab 2: Test Suite
// ============================================================

function TestSuiteView({ testCases, expandedItem, onToggle }: {
  testCases: TestCase[] | null;
  expandedItem: string | null;
  onToggle: (id: string) => void;
}) {
  if (!testCases || testCases.length === 0) {
    return (
      <div className="rtp-empty-tab">
        <FlaskConical size={28} />
        <p>No test cases generated yet</p>
      </div>
    );
  }

  const categories = testCases.reduce((acc, tc) => {
    acc[tc.category] = (acc[tc.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="rtp-tab-content">
      <div className="rtp-tab-summary">
        <div className="rtp-stat">
          <span className="rtp-stat-value">{testCases.length}</span>
          <span className="rtp-stat-label">Test Cases</span>
        </div>
        {Object.entries(categories).map(([cat, count]) => (
          <div key={cat} className="rtp-stat">
            <span className="rtp-stat-value" style={{ color: CATEGORY_COLORS[cat] || "#fff" }}>{count}</span>
            <span className="rtp-stat-label">{cat}</span>
          </div>
        ))}
      </div>

      <div className="rtp-list">
        {testCases.map((tc) => (
          <div key={tc.testId} className={`rtp-card ${expandedItem === tc.testId ? "expanded" : ""}`}>
            <div className="rtp-card-header" onClick={() => onToggle(tc.testId)}>
              <div className="rtp-card-left">
                <span className="rtp-card-id">{tc.testId}</span>
                <span className="rtp-card-title">{tc.testName}</span>
              </div>
              <div className="rtp-card-right">
                <span className="badge category" style={{ background: CATEGORY_COLORS[tc.category] || "#6b7280" }}>
                  {tc.category}
                </span>
                <span className="badge priority" style={{ borderColor: PRIORITY_COLORS[tc.priority] || "#6b7280", color: PRIORITY_COLORS[tc.priority] || "#6b7280" }}>
                  {tc.priority}
                </span>
                {expandedItem === tc.testId ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </div>
            </div>
            {expandedItem === tc.testId && (
              <div className="rtp-card-body">
                <div className="detail-row">
                  <span className="detail-label">Description:</span>
                  <span className="detail-value">{tc.description}</span>
                </div>

                {tc.preconditions.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Preconditions:</span>
                    <ol className="step-list">
                      {tc.preconditions.map((p, i) => <li key={i}>{p}</li>)}
                    </ol>
                  </div>
                )}

                <div className="detail-row">
                  <span className="detail-label">Test Steps:</span>
                  <ol className="step-list numbered">
                    {tc.testSteps.map((step, i) => <li key={i}>{step}</li>)}
                  </ol>
                </div>

                <div className="detail-row expected">
                  <span className="detail-label">Expected Result:</span>
                  <span className="detail-value highlight">{tc.expectedResult}</span>
                </div>

                {tc.requirementRefs.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Requirement Refs:</span>
                    <div className="ref-tags">
                      {tc.requirementRefs.map((ref, i) => (
                        <span key={i} className="ref-tag">{ref}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


// ============================================================
// Tab 3: Test Results
// ============================================================

function TestResultsView({ testResults, failureAnalyses, passRate, expandedItem, onToggle }: {
  testResults: TestResult[] | null;
  failureAnalyses: FailureAnalysis[] | null;
  passRate: number | null;
  expandedItem: string | null;
  onToggle: (id: string) => void;
}) {
  if (!testResults || testResults.length === 0) {
    return (
      <div className="rtp-empty-tab">
        <Play size={28} />
        <p>No test results yet</p>
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

  return (
    <div className="rtp-tab-content">
      <div className="rtp-results-header">
        <div className="rtp-donut">
          <ResponsiveContainer width="100%" height={90}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={25}
                outerRadius={38}
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
          <div className="donut-center">
            <span>{passRate?.toFixed(0) || Math.round((passed / total) * 100)}%</span>
          </div>
        </div>
        <div className="rtp-result-stats">
          <div className="rtp-stat pass">
            <CheckCircle2 size={14} />
            <span className="rtp-stat-value">{passed}</span>
            <span className="rtp-stat-label">Passed</span>
          </div>
          <div className="rtp-stat fail">
            <XCircle size={14} />
            <span className="rtp-stat-value">{failed}</span>
            <span className="rtp-stat-label">Failed</span>
          </div>
          <div className="rtp-stat">
            <Clock size={14} />
            <span className="rtp-stat-value">{totalTime.toFixed(1)}s</span>
            <span className="rtp-stat-label">Total</span>
          </div>
        </div>
      </div>

      <div className="rtp-list">
        {testResults.map((tr) => {
          const analysis = getAnalysis(tr.testId);
          const isExpanded = expandedItem === tr.testId;

          return (
            <div key={tr.testId} className={`rtp-result-row ${tr.status.toLowerCase()}`}>
              <div className="rtp-result-main" onClick={() => onToggle(tr.testId)}>
                <div className={`rtp-result-status ${tr.status.toLowerCase()}`}>
                  {tr.status === "PASS" ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                </div>
                <div className="rtp-result-info">
                  <span className="rtp-result-id">{tr.testId}</span>
                  <span className="rtp-result-name">{tr.testName}</span>
                </div>
                <span className={`rtp-result-badge ${tr.status.toLowerCase()}`}>{tr.status}</span>
                <span className="rtp-result-time">{tr.executionTimeSeconds.toFixed(1)}s</span>
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </div>
              {isExpanded && (
                <div className="rtp-result-detail">
                  <div className="detail-row">
                    <span className="detail-label">Actual Result:</span>
                    <span className="detail-value">{tr.actualResult}</span>
                  </div>
                  {tr.errorMessage && (
                    <div className="detail-row error-row">
                      <span className="detail-label">Error:</span>
                      <span className="detail-value">{tr.errorMessage}</span>
                    </div>
                  )}
                  {analysis && (
                    <div className="rtp-analysis-box">
                      <div className="rtp-analysis-header">
                        <AlertTriangle size={13} />
                        <span>Root Cause Analysis</span>
                        <span className={`severity-badge ${analysis.severity.toLowerCase()}`}>{analysis.severity}</span>
                        <span className="category-badge">{analysis.category}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Root Cause:</span>
                        <span className="detail-value">{analysis.rootCause}</span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Suggested Fix:</span>
                        <span className="detail-value">{analysis.suggestedFix}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}


// ============================================================
// Tab 4: Code Fixes
// ============================================================

function CodeFixesView({ refactorSuggestions, expandedItem, onToggle }: {
  refactorSuggestions: CodeRefactorSuggestion[] | null;
  expandedItem: string | null;
  onToggle: (id: string) => void;
}) {
  if (!refactorSuggestions || refactorSuggestions.length === 0) {
    return (
      <div className="rtp-empty-tab">
        <Wrench size={28} />
        <p>No code fixes needed — all tests passed or no logic bugs detected</p>
      </div>
    );
  }

  return (
    <div className="rtp-tab-content">
      <div className="rtp-tab-summary">
        <div className="rtp-stat">
          <span className="rtp-stat-value">{refactorSuggestions.length}</span>
          <span className="rtp-stat-label">Code Fixes</span>
        </div>
        <div className="rtp-stat">
          <span className="rtp-stat-value">
            {Math.round(refactorSuggestions.reduce((s, r) => s + r.confidence, 0) / refactorSuggestions.length * 100)}%
          </span>
          <span className="rtp-stat-label">Avg Confidence</span>
        </div>
      </div>

      <div className="rtp-list">
        {refactorSuggestions.map((fix) => {
          const isExpanded = expandedItem === `fix-${fix.testId}`;
          return (
            <div key={fix.testId} className={`rtp-card code-fix ${isExpanded ? "expanded" : ""}`}>
              <div className="rtp-card-header" onClick={() => onToggle(`fix-${fix.testId}`)}>
                <div className="rtp-card-left">
                  <Code2 size={14} />
                  <span className="rtp-card-id">{fix.testId}</span>
                  <span className="rtp-card-title">{fix.filePath}</span>
                </div>
                <div className="rtp-card-right">
                  <span className="confidence-bar">
                    <span className="confidence-fill" style={{ width: `${fix.confidence * 100}%` }}></span>
                  </span>
                  <span className="confidence-pct">{(fix.confidence * 100).toFixed(0)}%</span>
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </div>
              </div>
              {isExpanded && (
                <div className="rtp-card-body code-fix-body">
                  <p className="fix-explanation">{fix.explanation}</p>

                  <div className="code-diff">
                    <div className="code-block-wrapper original">
                      <div className="code-block-label">
                        <XCircle size={12} />
                        <span>Original (Bug)</span>
                      </div>
                      <pre className="code-block">{fix.originalCode}</pre>
                    </div>
                    <div className="code-diff-arrow">
                      <ArrowRight size={18} />
                    </div>
                    <div className="code-block-wrapper suggested">
                      <div className="code-block-label">
                        <CheckCircle2 size={12} />
                        <span>Fixed</span>
                      </div>
                      <pre className="code-block">{fix.suggestedCode}</pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}


// ============================================================
// Tab 5: Compliance
// ============================================================

function ComplianceView({ report, expandedSection, onToggleSection }: {
  report: ComplianceReport | null;
  expandedSection: number | null;
  onToggleSection: (i: number) => void;
}) {
  if (!report) {
    return (
      <div className="rtp-empty-tab">
        <ClipboardCheck size={28} />
        <p>GxP compliance report will appear after test execution</p>
      </div>
    );
  }

  const statusClass = report.complianceStatus.toLowerCase().replace(/[- ]/g, "");

  return (
    <div className="rtp-tab-content">
      <div className={`rtp-compliance-status ${statusClass}`}>
        <ShieldCheck size={20} />
        <div className="compliance-info">
          <span className="compliance-label">{report.complianceStatus}</span>
          <span className="compliance-detail">
            {report.passed}/{report.totalTests} passed &middot; {report.passRate.toFixed(1)}% &middot; {report.reportId}
          </span>
        </div>
      </div>

      <div className="rtp-compliance-meta">
        <span>Platform: {report.platform}</span>
        <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
      </div>

      <div className="rtp-list">
        {report.sections.map((section, i) => (
          <div key={i} className="rtp-section">
            <div className="rtp-section-header" onClick={() => onToggleSection(i)}>
              {expandedSection === i ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <span>{section.title}</span>
            </div>
            {expandedSection === i && (
              <div
                className="rtp-section-content"
                dangerouslySetInnerHTML={{ __html: formatContent(section.content) }}
              />
            )}
          </div>
        ))}
      </div>

      <button className="rtp-download-btn" disabled>
        <Download size={14} />
        <span>Export PDF Report</span>
      </button>
    </div>
  );
}

function formatContent(content: string): string {
  let html = content;
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^- (.*$)/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="section-list">$&</ul>');
  html = html.replace(/\n/g, "<br />");
  return html;
}
