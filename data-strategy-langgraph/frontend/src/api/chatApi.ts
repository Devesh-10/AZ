import { ChatResponse, AgentLogEntry } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
// Direct API Gateway URL for POST requests (update after deployment)
const API_GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL || "";

/**
 * Send a query to the Data Strategy Agent (LangGraph Backend)
 */
export async function sendQuery(
  sessionId: string | null,
  message: string
): Promise<ChatResponse> {
  const baseUrl = API_GATEWAY_URL || API_BASE_URL;
  const response = await fetch(`${baseUrl}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      question: message,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('API Error:', response.status, errorText);
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  console.log('API Response:', data);

  // Helper to transform backend KPI data to frontend format
  const transformKpiResults = (kpiResults: Array<{
    kpi_name: string;
    breakdown_by: string | null;
    data_points: Array<{ label?: string; sku?: string; site?: string; period?: string; value: number; unit?: string }>;
    explanation: string | null;
  }> | null) => {
    if (!kpiResults) return undefined;
    return kpiResults.map(kpi => ({
      kpiName: kpi.kpi_name,
      breakdownBy: kpi.breakdown_by as "site" | null,
      dataPoints: kpi.data_points?.map(dp => ({
        label: dp.label || `${dp.sku || ''} ${dp.site || ''} ${dp.period || ''}`.trim(),
        value: dp.value
      })) || [],
      explanation: kpi.explanation || ""
    }));
  };

  // Map backend response to frontend expected format
  return {
    sessionId: data.session_id,
    answer: data.answer,
    routeType: data.route_type,
    matchedKpi: data.matched_kpi,
    lifecycleStages: data.lifecycle_stages,
    visualizationConfig: data.visualization_config ? {
      chartType: data.visualization_config.chartType || "bar",
      title: data.visualization_config.title || "Data Quality Metrics",
      xLabel: data.visualization_config.xLabel,
      yLabel: data.visualization_config.yLabel,
      series: data.visualization_config.series || []
    } : undefined,
    kpiResult: transformKpiResults(data.kpi_results),
    analystResult: data.analyst_result ? {
      narrative: data.analyst_result.narrative,
      supportingKpiResults: transformKpiResults(data.analyst_result.supporting_kpi_results) || [],
      insights: data.analyst_result.insights || []
    } : undefined,
    validationResult: data.is_valid !== undefined ? {
      isValid: data.is_valid,
      issues: data.validation_issues || []
    } : undefined,
    generatedSql: data.generated_sql,
    agentLogs: data.agent_logs?.map((log: { agent_name: string; input_summary: string; output_summary: string; reasoning_summary?: string; status: string; timestamp: string }, idx: number) => ({
      id: `${data.session_id}-${idx}`,
      sessionId: data.session_id,
      timestamp: log.timestamp,
      agentName: log.agent_name,
      inputSummary: log.input_summary,
      outputSummary: log.output_summary,
      reasoningSummary: log.reasoning_summary,
      status: log.status
    }))
  };
}

/**
 * Get telemetry logs for a session
 */
export async function getTelemetry(sessionId: string): Promise<AgentLogEntry[]> {
  const baseUrl = API_GATEWAY_URL || API_BASE_URL;
  const response = await fetch(
    `${baseUrl}/api/sessions/${sessionId}/telemetry`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return data.map((log: {
    agent_name: string;
    input_summary: string;
    output_summary: string;
    reasoning_summary?: string;
    status: string;
    timestamp: string;
  }, index: number) => ({
    id: `${sessionId}-${index}`,
    sessionId: sessionId,
    timestamp: log.timestamp,
    agentName: log.agent_name === "KPI Agent" ? "KPI Gateway" : log.agent_name,
    inputSummary: log.input_summary,
    outputSummary: log.output_summary,
    reasoningSummary: log.reasoning_summary,
    status: log.status
  }));
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  const data = await response.json();
  return {
    status: data.status,
    timestamp: new Date().toISOString()
  };
}
