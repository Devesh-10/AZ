import { ChatResponse, AgentLogEntry, KnowledgeGraph } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Send a query to the Manufacturing Insight Agent (LangGraph Backend)
 */
export async function sendQuery(
  sessionId: string | null,
  message: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
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
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();

  // Helper to transform backend KPI data to frontend format
  const transformKpiResults = (kpiResults: Array<{
    kpi_name: string;
    breakdown_by: string | null;
    data_points: Array<{ sku: string; site: string; period: string; value: number; unit: string }>;
    explanation: string | null;
  }> | null) => {
    if (!kpiResults) return undefined;
    return kpiResults.map(kpi => ({
      kpiName: kpi.kpi_name,
      breakdownBy: kpi.breakdown_by as "site" | null,
      dataPoints: kpi.data_points?.map(dp => ({
        label: `${dp.sku} (${dp.site}) - ${dp.period}`,
        value: dp.value
      })) || [],
      explanation: kpi.explanation || ""
    }));
  };

  // Map backend response to frontend expected format
  return {
    sessionId: data.session_id,
    answer: data.answer,
    visualizationConfig: data.visualization_config ? {
      chartType: "bar" as const,
      title: data.visualization_config.kpi_name || "KPI Data",
      series: [{
        name: data.visualization_config.kpi_name || "Value",
        data: data.visualization_config.data?.map((d: { sku: string; site: string; period: string; value: number }) => ({
          x: d.period || `${d.sku} (${d.site})`,  // Use period for x-axis if available
          y: d.value
        })) || []
      }]
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
    generatedSql: data.generated_sql
  };
}

/**
 * Get telemetry logs for a session
 */
export async function getTelemetry(sessionId: string): Promise<AgentLogEntry[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/telemetry`,
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

  // Map backend telemetry to frontend format
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
 * Get the knowledge graph schema (placeholder for now)
 */
export async function getKnowledgeGraph(): Promise<KnowledgeGraph> {
  // Return static placeholder since LangGraph backend doesn't have this endpoint yet
  return {
    kpis: [
      { name: "Batch Yield", description: "Average batch yield percentage", unit: "%", category: "Quality", relatedKpis: ["RFT"] },
      { name: "RFT", description: "Right First Time percentage", unit: "%", category: "Quality", relatedKpis: ["Batch Yield"] },
      { name: "OEE", description: "Overall Equipment Effectiveness", unit: "%", category: "Efficiency", relatedKpis: ["Cycle Time"] },
    ],
    dimensions: [
      { name: "SKU", description: "Product SKU", values: ["SKU_123", "SKU_456"] },
      { name: "Site", description: "Manufacturing site", values: ["FCTN-PLANT-01"] },
    ],
    relationships: [
      { from: "Batch Yield", to: "RFT", type: "correlates" },
    ]
  };
}

/**
 * Get available KPIs
 */
export async function getSchema(): Promise<{
  kpis: string[];
  dimensions: Record<string, string[]>;
}> {
  const response = await fetch(`${API_BASE_URL}/api/kpis`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return {
    kpis: data.kpis?.map((k: { name: string }) => k.name) || [],
    dimensions: {
      sku: ["SKU_123", "SKU_456"],
      site: ["FCTN-PLANT-01"]
    }
  };
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
