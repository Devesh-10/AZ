import type {
  TestRunResponse,
  Platform,
  AgentLogEntry,
  TestResult,
  TestCase,
  RequirementField,
  TimingComparison,
  ComplianceReport,
  ReportSection,
  FailureAnalysis,
  CodeRefactorSuggestion,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";
// Direct Lambda Function URL for POST requests (bypasses API Gateway 29s timeout)
const LAMBDA_URL = "https://xqxrip2ry35mrc44rry3mixeni0xcohm.lambda-url.us-east-1.on.aws";

function transformTestResult(raw: any): TestResult {
  return {
    testId: raw.test_id,
    testName: raw.test_name,
    status: raw.status,
    executionTimeSeconds: raw.execution_time_seconds,
    actualResult: raw.actual_result,
    errorMessage: raw.error_message,
  };
}

function transformFailureAnalysis(raw: any): FailureAnalysis {
  return {
    testId: raw.test_id,
    rootCause: raw.root_cause,
    category: raw.category,
    severity: raw.severity,
    suggestedFix: raw.suggested_fix,
  };
}

function transformRefactorSuggestion(raw: any): CodeRefactorSuggestion {
  return {
    testId: raw.test_id,
    filePath: raw.file_path,
    originalCode: raw.original_code,
    suggestedCode: raw.suggested_code,
    explanation: raw.explanation,
    confidence: raw.confidence,
  };
}

function transformRequirement(raw: any): RequirementField {
  return {
    fieldId: raw.field_id,
    fieldName: raw.field_name,
    dataType: raw.data_type,
    mandatory: raw.mandatory,
    validationRules: raw.validation_rules || [],
    sourceSpec: raw.source_spec,
  };
}

function transformTestCase(raw: any): TestCase {
  return {
    testId: raw.test_id,
    testName: raw.test_name,
    description: raw.description,
    preconditions: raw.preconditions || [],
    testSteps: raw.test_steps || [],
    expectedResult: raw.expected_result,
    priority: raw.priority,
    category: raw.category,
    requirementRefs: raw.requirement_refs || [],
  };
}

function transformAgentLog(raw: any): AgentLogEntry {
  return {
    id: `${raw.agent_name}-${raw.timestamp}`,
    sessionId: raw.session_id || "",
    timestamp: raw.timestamp,
    agentName: raw.agent_name,
    stepNumber: raw.step_number,
    inputSummary: raw.input_summary,
    outputSummary: raw.output_summary,
    reasoningSummary: raw.reasoning_summary,
    status: raw.status,
    durationSeconds: raw.duration_seconds,
    isConditional: raw.is_conditional,
    wasExecuted: raw.was_executed,
  };
}

function transformTimingComparison(raw: any): TimingComparison {
  return {
    manualTotalHours: raw.manual_total_hours,
    agentTotalSeconds: raw.agent_total_seconds,
    savingsPercent: raw.savings_percent,
    steps: (raw.steps || []).map((s: any) => ({
      stepName: s.step_name,
      manualTime: s.manual_time,
      agentTime: s.agent_time,
    })),
  };
}

function transformComplianceReport(raw: any): ComplianceReport {
  return {
    reportId: raw.report_id,
    platform: raw.platform,
    generatedAt: raw.generated_at,
    totalTests: raw.total_tests,
    passed: raw.passed,
    failed: raw.failed,
    passRate: raw.pass_rate,
    complianceStatus: raw.compliance_status,
    sections: (raw.sections || []).map((s: any): ReportSection => ({
      title: s.title,
      content: s.content,
    })),
  };
}

/**
 * Run test via Lambda Function URL to bypass API Gateway 29s timeout.
 * Uses the standard /api/test endpoint (not SSE streaming) since Mangum
 * does not support streaming responses. Lambda Function URL allows up to
 * 180s (matching Lambda timeout).
 */
export async function runTestStreaming(
  platform: string,
  message: string,
  sessionId: string | null,
  _onAgentLog: (log: AgentLogEntry) => void
): Promise<TestRunResponse> {
  // Use Lambda Function URL directly to bypass API Gateway 29s timeout
  const baseUrl = LAMBDA_URL || API_BASE_URL;
  const response = await fetch(`${baseUrl}/api/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform,
      question: message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return transformFinalResult(data);
}

function transformFinalResult(data: any): TestRunResponse {
  return {
    sessionId: data.session_id,
    answer: data.answer,
    platform: data.platform,
    requirements: data.requirements?.map(transformRequirement),
    requirementsCount: data.requirements_count,
    testCases: data.test_cases?.map(transformTestCase),
    testCasesCount: data.test_cases_count,
    testResults: data.test_results?.map(transformTestResult),
    failureAnalyses: data.failure_analyses?.map(transformFailureAnalysis),
    refactorSuggestions: data.refactor_suggestions?.map(transformRefactorSuggestion),
    passRate: data.pass_rate,
    complianceStatus: data.compliance_status,
    visualizationConfig: data.visualization_config,
    timingComparison: data.timing_comparison
      ? transformTimingComparison(data.timing_comparison)
      : undefined,
    complianceReport: data.compliance_report
      ? transformComplianceReport(data.compliance_report)
      : undefined,
    agentLogs: (data.agent_logs || []).map(transformAgentLog),
  };
}

export async function runTest(
  platform: string,
  message: string,
  sessionId: string | null
): Promise<TestRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      platform,
      question: message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();

  return transformFinalResult(data);
}

export async function runTestWithDocument(
  platform: string,
  message: string,
  sessionId: string | null,
  file: File
): Promise<TestRunResponse> {
  const formData = new FormData();
  formData.append("platform", platform);
  formData.append("question", message);
  if (sessionId) {
    formData.append("session_id", sessionId);
  }
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/test/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();

  return {
    sessionId: data.session_id,
    answer: data.answer,
    platform: data.platform,
    requirements: data.requirements?.map(transformRequirement),
    requirementsCount: data.requirements_count,
    testCases: data.test_cases?.map(transformTestCase),
    testCasesCount: data.test_cases_count,
    testResults: data.test_results?.map(transformTestResult),
    failureAnalyses: data.failure_analyses?.map(transformFailureAnalysis),
    refactorSuggestions: data.refactor_suggestions?.map(transformRefactorSuggestion),
    passRate: data.pass_rate,
    complianceStatus: data.compliance_status,
    visualizationConfig: data.visualization_config,
    timingComparison: data.timing_comparison
      ? transformTimingComparison(data.timing_comparison)
      : undefined,
    complianceReport: data.compliance_report
      ? transformComplianceReport(data.compliance_report)
      : undefined,
    agentLogs: (data.agent_logs || []).map(transformAgentLog),
  };
}

export async function getPlatforms(): Promise<Platform[]> {
  const response = await fetch(`${API_BASE_URL}/api/platforms`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  const data = await response.json();
  return (data.platforms || []).map((p: any) => ({
    id: p.id,
    name: p.name,
    description: p.description,
    depth: p.depth,
    icon: p.icon,
    color: p.color,
    testDomains: p.test_domains,
    sampleQueries: p.sample_queries,
    metrics: {
      totalTests: p.metrics?.total_tests,
      passRate: p.metrics?.pass_rate,
      avgExecutionTime: p.metrics?.avg_execution_time,
      manualEquivalent: p.metrics?.manual_equivalent,
    },
  }));
}

export async function getTelemetry(
  sessionId: string
): Promise<AgentLogEntry[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/telemetry`
  );
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  const data = await response.json();
  return (data || []).map(transformAgentLog);
}

export async function healthCheck(): Promise<{
  status: string;
  timestamp: string;
}> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
