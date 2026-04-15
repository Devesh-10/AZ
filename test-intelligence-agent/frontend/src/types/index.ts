// ============================================================
// Test Intelligence Agent - TypeScript Types
// ============================================================

// --- Platform Types ---

export interface Platform {
  id: string;
  name: string;
  description: string;
  depth: "deep" | "visual";
  icon: string;
  color: string;
  testDomains?: string[];
  sampleQueries?: string[];
  metrics: PlatformMetrics;
}

export interface PlatformMetrics {
  totalTests: number;
  passRate: number;
  avgExecutionTime: string;
  manualEquivalent: string;
}

// --- Requirement Types ---

export interface RequirementField {
  fieldId: string;
  fieldName: string;
  dataType: string;
  mandatory: boolean;
  validationRules: string[];
  sourceSpec: string;
}

// --- Test Case Types ---

export interface TestCase {
  testId: string;
  testName: string;
  description: string;
  preconditions: string[];
  testSteps: string[];
  expectedResult: string;
  priority: "Critical" | "High" | "Medium" | "Low";
  category: "Functional" | "Boundary" | "Negative" | "Compliance" | "Integration" | "Metadata-Scenario";
  requirementRefs: string[];
}

// --- Test Result Types ---

export interface TestResult {
  testId: string;
  testName: string;
  status: "PASS" | "FAIL" | "SKIP" | "ERROR";
  executionTimeSeconds: number;
  actualResult: string;
  errorMessage?: string;
}

// --- Failure Analysis Types ---

export interface FailureAnalysis {
  testId: string;
  rootCause: string;
  category: "Data Issue" | "Logic Bug" | "Configuration" | "Environment" | "Integration";
  severity: "Critical" | "High" | "Medium" | "Low";
  suggestedFix: string;
}

// --- Code Refactor Types ---

export interface CodeRefactorSuggestion {
  testId: string;
  filePath: string;
  originalCode: string;
  suggestedCode: string;
  explanation: string;
  confidence: number;
}

// --- Compliance Report Types ---

export interface ReportSection {
  title: string;
  content: string;
}

export interface ComplianceReport {
  reportId: string;
  platform: string;
  generatedAt: string;
  totalTests: number;
  passed: number;
  failed: number;
  passRate: number;
  complianceStatus: "Compliant" | "Non-Compliant" | "Partially Compliant";
  sections: ReportSection[];
}

// --- Visualization Types ---

export interface VisualizationConfig {
  chartType: "line" | "bar" | "pie" | "donut";
  title: string;
  xLabel?: string;
  yLabel?: string;
  series: {
    name: string;
    data: { x: string | number; y: number }[];
  }[];
}

// --- Agent Flow Types ---

export interface AgentLogEntry {
  id: string;
  sessionId: string;
  timestamp: string;
  agentName: string;
  stepNumber: number;
  inputSummary: string;
  outputSummary: string;
  reasoningSummary?: string;
  status: "success" | "error" | "skipped" | "running";
  durationSeconds?: number;
  isConditional: boolean;
  wasExecuted: boolean;
}

// --- Timing Comparison Types ---

export interface TimingStep {
  stepName: string;
  manualTime: string;
  agentTime: string;
}

export interface TimingComparison {
  manualTotalHours: number;
  agentTotalSeconds: number;
  savingsPercent: number;
  steps: TimingStep[];
}

// --- API Response Types ---

export interface TestRunResponse {
  sessionId: string;
  answer: string;
  platform: string;
  requirements?: RequirementField[];
  requirementsCount?: number;
  testCases?: TestCase[];
  testCasesCount?: number;
  testResults?: TestResult[];
  failureAnalyses?: FailureAnalysis[];
  refactorSuggestions?: CodeRefactorSuggestion[];
  passRate?: number;
  complianceStatus?: string;
  visualizationConfig?: VisualizationConfig;
  timingComparison?: TimingComparison;
  complianceReport?: ComplianceReport;
  agentLogs: AgentLogEntry[];
}

// --- Chat Types ---

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  testResults?: TestResult[];
  failureAnalyses?: FailureAnalysis[];
  refactorSuggestions?: CodeRefactorSuggestion[];
  visualizationConfig?: VisualizationConfig;
  complianceReport?: ComplianceReport;
  timingComparison?: TimingComparison;
}
