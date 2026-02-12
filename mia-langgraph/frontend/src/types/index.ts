// Frontend types (mirrored from backend)

export interface KpiResult {
  kpiName: string;
  breakdownBy: "date" | "month" | "region" | "product" | "segment" | "site" | "quarter" | "year" | "site_id" | "status" | "equipment" | "summary" | "by_site" | "by_status" | "by_equipment" | "detailed" | null;
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

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  visualizationConfig?: VisualizationConfig;
  kpiResult?: KpiResult[];
  analystResult?: AnalystResult;
}

export interface KnowledgeGraph {
  kpis: {
    name: string;
    description: string;
    unit: string;
    category: string;
    relatedKpis: string[];
  }[];
  dimensions: {
    name: string;
    description: string;
    values: string[];
  }[];
  relationships: {
    from: string;
    to: string;
    type: string;
  }[];
}
