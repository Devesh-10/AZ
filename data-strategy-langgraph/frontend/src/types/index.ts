// Frontend types (mirrored from backend)

export interface DataSource {
  type: 'collibra' | 'sap_mdg' | 'excel' | 'demo';
  name: string;
  assets: number;
  rules: number;
}

export interface KpiResult {
  kpiName: string;
  breakdownBy: string | null;
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
  agentName: "Supervisor" | "KPI Agent" | "Discovery" | "Profiling" | "Rules" | "Reporting" | "Remediation" | "Validator" | "Visualization";
  inputSummary: string;
  outputSummary: string;
  reasoningSummary?: string;
  status: "success" | "error";
}

export interface ChatResponse {
  sessionId: string;
  answer: string;
  routeType?: string;
  matchedKpi?: string;
  lifecycleStages?: string[];
  visualizationConfig?: VisualizationConfig;
  kpiResult?: KpiResult[];
  analystResult?: AnalystResult;
  validationResult?: ValidationResult;
  followUpQuestion?: string;
  generatedSql?: string;
  agentLogs?: AgentLogEntry[];
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
