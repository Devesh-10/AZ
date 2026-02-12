// Core types for the Agentic KPI Assistant

export interface KpiQuery {
  kpiNames: string[];
  startDate?: string;
  endDate?: string;
  filters?: Record<string, string>;
  groupBy?: "date" | "month" | "region" | "product" | "segment";
}

export interface KpiResult {
  kpiName: string;
  breakdownBy: "date" | "month" | "region" | "product" | "segment" | "site" | "quarter" | "year" | null;
  dataPoints: { label: string; value: number }[];
  explanation: string;
}

export interface AnalystResult {
  narrative: string;
  supportingKpiResults: KpiResult[];
  insights: string[];
}

export interface ValidationResult {
  isValid: boolean;
  issues: string[];
  followUpQuestion?: string;
}

export interface VisualizationConfig {
  chartType: "line" | "bar" | "pie";
  title: string;
  xLabel?: string;
  yLabel?: string;
  series: {
    name: string;
    data: { x: string | number; y: number }[];
  }[];
}

export type RoutingDecision =
  | { type: "REJECT"; reason: string }
  | { type: "KPI_SIMPLE"; reason: string }
  | { type: "KPI_COMPLEX"; reason: string };

export interface AgentLogEntry {
  id: string;
  sessionId: string;
  timestamp: string;
  agentName: "Supervisor" | "KPI Gateway" | "Analyst" | "Validator" | "Visualization";
  inputSummary: string;
  outputSummary: string;
  reasoningSummary?: string;
  status: "success" | "error";
}

export interface ParsedIntent {
  kpiNames: string[];
  timeRange?: { start: string; end: string };
  filters?: Record<string, string>;
  groupBy?: "date" | "month" | "region" | "product" | "segment";
  comparisonType?: "none" | "vs_previous_period" | "vs_same_period_last_year" | "vs_other_filter";
}

export interface KpiDataRow {
  date: string;
  region: string;
  product: string;
  segment?: string;
  kpi: string;
  value: number;
}

export interface OrchestratorResponse {
  answer: string;
  kpiResult?: KpiResult[];
  analystResult?: AnalystResult;
  validationResult?: ValidationResult;
  visualizationConfig?: VisualizationConfig;
  followUpQuestion?: string;
  generatedSql?: string;
}

export interface ChatRequest {
  sessionId?: string;
  message: string;
}

export interface ChatResponse {
  sessionId: string;
  answer: string;
  visualizationConfig?: VisualizationConfig;
  kpiResult?: KpiResult[];
  analystResult?: AnalystResult;
  validationResult?: ValidationResult;
  followUpQuestion?: string;
  generatedSql?: string;
}

// Knowledge Graph types
export interface KpiDefinition {
  name: string;
  description: string;
  unit: string;
  category: string;
  relatedKpis: string[];
}

export interface DimensionDefinition {
  name: string;
  description: string;
  values: string[];
}

export interface KnowledgeGraph {
  kpis: KpiDefinition[];
  dimensions: DimensionDefinition[];
  relationships: {
    from: string;
    to: string;
    type: string;
  }[];
}
