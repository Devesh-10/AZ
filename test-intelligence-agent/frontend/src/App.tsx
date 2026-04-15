import { useState } from "react";
import LoginPage from "./components/LoginPage";
import PlatformSelector from "./components/PlatformSelector";
import ChatInterface from "./components/ChatInterface";
import AgentFlowPanel from "./components/AgentFlowPanel";
import ResultsTabPanel from "./components/ResultsTabPanel";
import type {
  AgentLogEntry, TestRunResponse, TestResult, TestCase,
  RequirementField, FailureAnalysis, CodeRefactorSuggestion,
  ComplianceReport, TimingComparison
} from "./types";
import "./App.css";

export default function App() {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Navigation state
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Agent flow state
  const [agentLogs, setAgentLogs] = useState<AgentLogEntry[]>([]);
  const [isAgentPanelCollapsed, setIsAgentPanelCollapsed] = useState(false);

  // Artifact state
  const [requirements, setRequirements] = useState<RequirementField[] | null>(null);
  const [testCases, setTestCases] = useState<TestCase[] | null>(null);
  const [testResults, setTestResults] = useState<TestResult[] | null>(null);
  const [failureAnalyses, setFailureAnalyses] = useState<FailureAnalysis[] | null>(null);
  const [refactorSuggestions, setRefactorSuggestions] = useState<CodeRefactorSuggestion[] | null>(null);
  const [passRate, setPassRate] = useState<number | null>(null);
  const [complianceReport, setComplianceReport] = useState<ComplianceReport | null>(null);
  const [timingComparison, setTimingComparison] = useState<TimingComparison | null>(null);

  const handleResponse = (resp: TestRunResponse) => {
    setRequirements(resp.requirements || null);
    setTestCases(resp.testCases || null);
    setTestResults(resp.testResults || null);
    setFailureAnalyses(resp.failureAnalyses || null);
    setRefactorSuggestions(resp.refactorSuggestions || null);
    setPassRate(resp.passRate ?? null);
    setComplianceReport(resp.complianceReport || null);
    setTimingComparison(resp.timingComparison || null);
  };

  const handleBackToPlatforms = () => {
    setSelectedPlatform(null);
    setSessionId(null);
    setAgentLogs([]);
    setRequirements(null);
    setTestCases(null);
    setTestResults(null);
    setFailureAnalyses(null);
    setRefactorSuggestions(null);
    setPassRate(null);
    setComplianceReport(null);
    setTimingComparison(null);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    handleBackToPlatforms();
  };

  // Screen 1: Login
  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  // Screen 2: Platform Selector
  if (!selectedPlatform) {
    return (
      <PlatformSelector
        onPlatformSelect={setSelectedPlatform}
        onLogout={handleLogout}
      />
    );
  }

  // Screen 3: Main Testing Interface (3-panel)
  return (
    <div className="app">
      <main className={`app-main ${isAgentPanelCollapsed ? "collapsed-agent" : ""}`}>
        <div className="chat-panel">
          <ChatInterface
            platform={selectedPlatform}
            sessionId={sessionId}
            onSessionIdChange={setSessionId}
            onAgentLogs={setAgentLogs}
            onResponse={handleResponse}
            onBackToPlatforms={handleBackToPlatforms}
            onLogout={handleLogout}
          />
        </div>

        <aside className="agent-panel">
          <AgentFlowPanel
            logs={agentLogs}
            isCollapsed={isAgentPanelCollapsed}
            onToggleCollapse={() => setIsAgentPanelCollapsed(!isAgentPanelCollapsed)}
          />
        </aside>

        <aside className="results-panel">
          <ResultsTabPanel
            requirements={requirements}
            testCases={testCases}
            testResults={testResults}
            failureAnalyses={failureAnalyses}
            refactorSuggestions={refactorSuggestions}
            passRate={passRate}
            complianceReport={complianceReport}
            platform={selectedPlatform}
          />
        </aside>
      </main>
    </div>
  );
}
