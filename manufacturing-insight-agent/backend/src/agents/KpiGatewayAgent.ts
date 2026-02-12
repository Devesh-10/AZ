import { KpiResult } from "../types";
import { callClaudeForJson } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import { getManufacturingDataRepository } from "../dataAccess/ManufacturingDataRepository";
import { loadPrompt, PROMPTS } from "../prompts";

// Load prompt template at module init (for documentation/reference)
const _kpiGatewayPromptTemplate = loadPrompt(PROMPTS.KPI_GATEWAY);

export interface KpiGatewayResult {
  kpiResults: KpiResult[];
  generatedSql: string;
}

// Data availability metadata interface
interface DataAvailabilityInfo {
  requestedMonths: number | null;
  availableMonths: number;
  skuFound: boolean;
  skuFilter: string | null;
  metricFound: boolean;
  metric: string;
  allAvailableSKUs: string[];
  allAvailableMonths: string[];
}

/**
 * KPI GATEWAY AGENT - FAST METRIC LOOKUP WITH SMART EDGE CASE HANDLING
 *
 * This agent handles SIMPLE queries that can be answered with direct data lookup.
 * Includes intelligent handling of:
 * - Data availability mismatches (requested vs available time ranges)
 * - Invalid SKU filters
 * - Missing metrics
 * - Empty results
 */

const PARSE_INTENT_PROMPT = `You are a query parser for a manufacturing KPI system.

EXTRACT the user's intent and return JSON.

AVAILABLE METRICS (use exact names):
- batch_yield_avg_pct (yield, batch yield)
- rft_pct (RFT, right first time)
- oee_packaging_pct (OEE, equipment effectiveness)
- avg_cycle_time_hr (cycle time)
- production_volume (volume, output)
- batch_count (batches, batch count)
- deviations_per_100_batches (deviations)
- schedule_adherence_pct (schedule adherence)
- alarms_per_1000_hours (alarms)
- stockouts_count (stockouts)

GROUPBY OPTIONS:
- "status" for batch status breakdown (Released/Rejected/Quarantined)
- "month" for monthly trend
- "site_id" for site comparison
- "equipment" for equipment breakdown
- null for overall average

Return JSON:
{
  "dataType": "weekly_kpi" | "monthly_kpi" | "batches",
  "metrics": ["metric_name"] or null for all,
  "groupBy": "status" | "month" | "equipment" | null
}

EXAMPLES:
"batch yield" → {"dataType": "weekly_kpi", "metrics": ["batch_yield_avg_pct"], "groupBy": null}
"OEE performance" → {"dataType": "weekly_kpi", "metrics": ["oee_packaging_pct"], "groupBy": null}
"show me RFT" → {"dataType": "weekly_kpi", "metrics": ["rft_pct"], "groupBy": null}
"batch status" → {"dataType": "batches", "metrics": null, "groupBy": "status"}
"all KPIs" → {"dataType": "weekly_kpi", "metrics": null, "groupBy": null}
"cycle time" → {"dataType": "weekly_kpi", "metrics": ["avg_cycle_time_hr"], "groupBy": null}`;

interface ManufacturingIntent {
  dataType: 'weekly_kpi' | 'monthly_kpi' | 'batches';
  metrics?: string[] | null;
  groupBy?: 'status' | 'month' | 'site_id' | 'equipment' | null;
}

// Human-readable metric names
const METRIC_LABELS: Record<string, string> = {
  'batch_yield_avg_pct': 'Batch Yield',
  'rft_pct': 'Right First Time (RFT)',
  'oee_packaging_pct': 'OEE Packaging',
  'avg_cycle_time_hr': 'Avg Cycle Time',
  'formulation_lead_time_hr': 'Formulation Lead Time',
  'production_volume': 'Production Volume',
  'batch_count': 'Batch Count',
  'deviations_per_100_batches': 'Deviations per 100 Batches',
  'schedule_adherence_pct': 'Schedule Adherence',
  'alarms_per_1000_hours': 'Alarms per 1000 Hours',
  'lab_turnaround_median_days': 'Lab Turnaround Time',
  'supplier_otif_pct': 'Supplier OTIF',
  'stockouts_count': 'Stockouts'
};

// Units for metrics
const METRIC_UNITS: Record<string, string> = {
  'batch_yield_avg_pct': '%',
  'rft_pct': '%',
  'oee_packaging_pct': '%',
  'avg_cycle_time_hr': ' hours',
  'formulation_lead_time_hr': ' hours',
  'production_volume': ' units',
  'batch_count': ' batches',
  'deviations_per_100_batches': '',
  'schedule_adherence_pct': '%',
  'alarms_per_1000_hours': '',
  'lab_turnaround_median_days': ' days',
  'supplier_otif_pct': '%',
  'stockouts_count': ''
};

// Target values for context
const METRIC_TARGETS: Record<string, number> = {
  'batch_yield_avg_pct': 98,
  'rft_pct': 92,
  'oee_packaging_pct': 80,
  'schedule_adherence_pct': 95
};

function generateSql(intent: ManufacturingIntent, monthCount?: number | null, skuFilter?: string | null): string {
  const table = intent.dataType === 'batches' ? 'MES_PASX_BATCHES' :
                intent.dataType === 'monthly_kpi' ? 'KPI_STORE_MONTHLY' : 'KPI_STORE_WEEKLY';

  if (intent.groupBy === 'status') {
    return `SELECT status, COUNT(*) as count
FROM ${table}
GROUP BY status;`;
  }

  if (intent.groupBy === 'equipment') {
    return `SELECT primary_equipment_id, COUNT(*) as batch_count
FROM MES_PASX_BATCHES
GROUP BY primary_equipment_id
ORDER BY batch_count DESC;`;
  }

  const metrics = intent.metrics || ['batch_yield_avg_pct', 'rft_pct', 'oee_packaging_pct'];
  const whereClause = skuFilter ? `WHERE SKU = '${skuFilter}'` : '';

  // Monthly time range query - simple SELECT, no aggregation
  if (monthCount || intent.dataType === 'monthly_kpi') {
    const selectCols = ['SKU', 'month', ...metrics].join(', ');
    const limit = monthCount || 1;
    return `SELECT ${selectCols}
FROM KPI_STORE_MONTHLY
${whereClause}
ORDER BY month DESC
LIMIT ${limit};`;
  }

  // Simple metric query - direct value lookup
  const selectCols = metrics.join(', ');
  return `SELECT ${selectCols}
FROM ${table}
ORDER BY iso_week DESC
LIMIT 1;`;
}

/**
 * Generate smart explanation with data availability awareness
 */
function generateExplanationWithMetadata(
  metrics: string[],
  values: { label: string; value: number }[],
  groupBy?: string | null,
  isMonthly?: boolean,
  skuFilter?: string | null,
  availabilityInfo?: DataAvailabilityInfo | null
): string {
  const metric = metrics[0];
  const label = METRIC_LABELS[metric] || metric;
  const unit = METRIC_UNITS[metric] || '';

  // Build data availability note if there's a mismatch
  let availabilityNote = '';
  if (availabilityInfo) {
    const { requestedMonths, availableMonths, skuFound, skuFilter: sku, allAvailableSKUs } = availabilityInfo;

    // Handle SKU not found
    if (sku && !skuFound) {
      const suggestedSKUs = allAvailableSKUs.slice(0, 3).join(', ');
      return `**Data Not Found**\nNo data found for ${sku}. Available SKUs in the system: ${suggestedSKUs}.\n\n**Suggestions**\nTry querying for one of the available SKUs, or remove the SKU filter to see aggregated data across all products.`;
    }

    // Handle time range mismatch
    if (requestedMonths && availableMonths < requestedMonths) {
      if (availableMonths === 0) {
        return `**Data Not Available**\nNo monthly data is available${sku ? ` for ${sku}` : ''}. The requested time range of ${requestedMonths} months cannot be fulfilled.\n\n**Suggestions**\nTry a different SKU or check if the data has been loaded correctly.`;
      }
      availabilityNote = `\n\n**Note:** You requested data for the past ${requestedMonths} months, but only ${availableMonths} month${availableMonths !== 1 ? 's' : ''} of data is available${sku ? ` for ${sku}` : ''}. Showing all available data.`;
    }
  }

  // Handle empty results
  if (values.length === 0) {
    return `**No Data Found**\nNo data is available for the requested ${label.toLowerCase()}${skuFilter ? ` for ${skuFilter}` : ''}.\n\n**Suggestions**\nTry broadening your query or checking if the metric name is correct.`;
  }

  if (groupBy === 'status') {
    const total = values.reduce((sum, v) => sum + v.value, 0);
    const released = values.find(v => v.label === 'Released')?.value || 0;
    const rejected = values.find(v => v.label === 'Rejected')?.value || 0;
    const quarantined = values.find(v => v.label === 'Quarantined')?.value || 0;

    const summary = `Of ${total} total batches, ${released} (${((released/total)*100).toFixed(1)}%) are Released, ${quarantined} (${((quarantined/total)*100).toFixed(1)}%) are Quarantined, and ${rejected} (${((rejected/total)*100).toFixed(1)}%) are Rejected.`;
    const suggestion = `Consider investigating the quarantined batches to identify common issues and reduce rejection rates.`;
    return `**Summary**\n${summary}\n\n**Suggestions for Further Queries**\n${suggestion}${availabilityNote}`;
  }

  // Monthly trend explanation with breakdown
  if (isMonthly && values.length > 1) {
    const avgValue = values.reduce((sum, v) => sum + v.value, 0) / values.length;

    // Build breakdown string (e.g., "2026-01: 20.04 hrs, 2025-12: 18.85 hrs")
    const breakdown = values
      .sort((a, b) => b.label.localeCompare(a.label)) // Sort descending by month
      .map(v => `${v.label}: ${v.value.toFixed(2)}${unit}`)
      .join(', ');

    const skuText = skuFilter ? ` for ${skuFilter}` : '';
    const summary = `The average ${label.toLowerCase()}${skuText} over the past ${values.length} months is ${avgValue.toFixed(2)}${unit} (${breakdown}).`;

    const suggestion = `Consider analyzing the specific steps within the ${label.toLowerCase().replace(' hr', '').replace(' %', '')} process to identify areas for streamlining and efficiency improvements.`;

    return `**Summary**\n${summary}\n\n**Suggestions for Further Queries**\n${suggestion}${availabilityNote}`;
  }

  // Single value explanation
  if (values.length === 1) {
    const value = values[0].value;
    const monthText = values[0].label ? ` for ${values[0].label}` : '';
    const skuText = skuFilter ? ` for ${skuFilter}` : '';

    const summary = `The ${label.toLowerCase()}${skuText}${monthText} is ${value.toFixed(2)}${unit}.`;
    const suggestion = `Consider comparing this against historical trends or other SKUs to identify optimization opportunities.`;

    return `**Summary**\n${summary}\n\n**Suggestions for Further Queries**\n${suggestion}${availabilityNote}`;
  }

  // Multiple metrics overview
  const summaryParts = values.map(v => {
    const metricKey = metrics.find(m => METRIC_LABELS[m] === v.label || m.includes(v.label.toLowerCase().replace(/[^a-z]/g, '')));
    const metricUnit = metricKey ? METRIC_UNITS[metricKey] : '';
    return `${v.label}: ${v.value.toFixed(2)}${metricUnit}`;
  });

  const summary = `Current KPI values: ${summaryParts.join(', ')}.`;
  const suggestion = `Consider drilling down into specific metrics to identify improvement opportunities.`;

  return `**Summary**\n${summary}\n\n**Suggestions for Further Queries**\n${suggestion}${availabilityNote}`;
}

// Legacy function for backward compatibility
function generateExplanation(
  metrics: string[],
  values: { label: string; value: number }[],
  groupBy?: string | null,
  isMonthly?: boolean,
  skuFilter?: string | null
): string {
  return generateExplanationWithMetadata(metrics, values, groupBy, isMonthly, skuFilter, null);
}

// Helper to extract number of months from query
function extractMonthCount(query: string): number | null {
  // Handle "last 3 months", "past 3 months" etc.
  const numMatch = query.match(/(last|past)\s+(\d+)\s+months?/i);
  if (numMatch) {
    return parseInt(numMatch[2], 10);
  }
  // Handle "last three months", "past three months" etc.
  const wordMap: Record<string, number> = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12
  };
  const wordMatch = query.match(/(last|past)\s+(one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s+months?/i);
  if (wordMatch) {
    return wordMap[wordMatch[2].toLowerCase()] || null;
  }
  // Handle "over the last month" = 1 month
  if (/over\s+the\s+(last|past)\s+month/i.test(query) || /this\s+month/i.test(query)) {
    return 1;
  }
  return null;
}

// Helper to extract SKU from query
function extractSku(query: string): string | null {
  const skuMatch = query.match(/SKU[_-]?(\d+)/i);
  if (skuMatch) {
    return `SKU_${skuMatch[1]}`;
  }
  return null;
}

// Helper to extract batch ID from query
function extractBatchId(query: string): string | null {
  const batchMatch = query.match(/\b(B\d{4}-\d{5})\b/i);
  if (batchMatch) {
    return batchMatch[1].toUpperCase();
  }
  return null;
}

// Helper to validate and suggest similar SKUs
function findSimilarSKUs(requestedSku: string, availableSKUs: string[]): string[] {
  const requested = requestedSku.toLowerCase();
  return availableSKUs
    .filter(sku => {
      const skuLower = sku.toLowerCase();
      // Match if starts with same prefix or contains similar numbers
      return skuLower.includes(requested.replace('sku_', '').replace('sku', '')) ||
             requested.includes(skuLower.replace('sku_', '').replace('sku', ''));
    })
    .slice(0, 3);
}

export async function parseAndFetchKpi(
  sessionId: string,
  userQuery: string
): Promise<KpiGatewayResult> {
  const repo = getManufacturingDataRepository();
  const lowerQuery = userQuery.toLowerCase();

  // Check for time range query (last N months)
  const monthCount = extractMonthCount(lowerQuery);
  const isTimeRangeQuery = monthCount !== null;

  // Check for SKU-specific query
  const skuFilter = extractSku(userQuery);

  // Check for batch-specific query
  const batchId = extractBatchId(userQuery);

  // Handle batch-specific queries (waiting time, lead time)
  if (batchId && (lowerQuery.includes('waiting time') || lowerQuery.includes('wait time') || lowerQuery.includes('lead time'))) {
    // Determine if it's a waiting time between steps or overall lead time
    if (lowerQuery.includes('between') || lowerQuery.includes('formulation') || lowerQuery.includes('packaging')) {
      const result = repo.getWaitingTimeBetweenSteps(batchId, 'formulation', 'packaging');

      if (result) {
        const explanation = `**Summary**\nFor batch ${batchId}, the Actual Lead Time is ${result.actualDays} days and the Planned Lead Time is ${result.plannedDays} day${result.plannedDays !== 1 ? 's' : ''}.\n\n**Suggestions for Further Queries**\nConsider investigating batches with lead times exceeding planned values to identify process bottlenecks.`;

        return {
          kpiResults: [{
            kpiName: `waiting_time_${batchId}`,
            breakdownBy: null,
            dataPoints: [
              { label: 'Actual Lead Time (days)', value: result.actualDays },
              { label: 'Planned Lead Time (days)', value: result.plannedDays }
            ],
            explanation
          }],
          generatedSql: `SELECT step_name, step_start, step_end, wait_before_min\nFROM MES_PASX_BATCH_STEPS\nWHERE batch_id = '${batchId}'\nORDER BY sequence;`
        };
      }
    } else {
      const result = repo.getBatchLeadTime(batchId);

      if (result) {
        const explanation = `**Summary**\nFor batch ${batchId}, the Actual Lead Time is ${result.actualLeadTimeDays} days and the Planned Lead Time is ${result.plannedLeadTimeDays} days.\n\n**Suggestions for Further Queries**\nConsider comparing this batch's lead time against similar batches to identify optimization opportunities.`;

        return {
          kpiResults: [{
            kpiName: `lead_time_${batchId}`,
            breakdownBy: null,
            dataPoints: [
              { label: 'Actual Lead Time (days)', value: result.actualLeadTimeDays },
              { label: 'Planned Lead Time (days)', value: result.plannedLeadTimeDays }
            ],
            explanation
          }],
          generatedSql: `SELECT batch_id, step_name, step_start, step_end, duration_min\nFROM MES_PASX_BATCH_STEPS\nWHERE batch_id = '${batchId}'\nORDER BY sequence;`
        };
      }
    }

    // Batch not found - provide helpful suggestions
    const allBatches = repo.getBatches({});
    const sampleBatchIds = allBatches.slice(0, 3).map(b => b.batch_id).join(', ');

    return {
      kpiResults: [{
        kpiName: 'batch_not_found',
        breakdownBy: null,
        dataPoints: [],
        explanation: `**Batch Not Found**\nBatch ${batchId} was not found in the system.\n\n**Available Batches**\nSample batch IDs: ${sampleBatchIds || 'No batches available'}\n\n**Suggestions**\nPlease verify the batch ID format (e.g., B2025-00007) and try again with a valid batch ID.`
      }],
      generatedSql: `SELECT * FROM MES_PASX_BATCH_STEPS WHERE batch_id = '${batchId}';`
    };
  }

  // FAST PATH: Direct pattern matching for common queries
  let parsedIntent: ManufacturingIntent;

  // Batch status query
  if (lowerQuery.includes('status') || (lowerQuery.includes('breakdown') && !isTimeRangeQuery)) {
    parsedIntent = { dataType: 'batches', metrics: null, groupBy: 'status' };
  }
  // OEE query
  else if (lowerQuery.includes('oee') || lowerQuery.includes('equipment effectiveness')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['oee_packaging_pct'], groupBy: null };
  }
  // Yield query - use monthly_kpi if SKU specified
  else if (lowerQuery.includes('yield')) {
    const dataType = skuFilter || isTimeRangeQuery ? 'monthly_kpi' : 'weekly_kpi';
    parsedIntent = { dataType, metrics: ['batch_yield_avg_pct'], groupBy: null };
  }
  // RFT query
  else if (lowerQuery.includes('rft') || lowerQuery.includes('right first time')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['rft_pct'], groupBy: null };
  }
  // Cycle time query
  else if (lowerQuery.includes('cycle time')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['avg_cycle_time_hr'], groupBy: null };
  }
  // Production/volume query
  else if (lowerQuery.includes('production') || lowerQuery.includes('volume')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['production_volume', 'batch_count'], groupBy: null };
  }
  // Deviation query
  else if (lowerQuery.includes('deviation')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['deviations_per_100_batches'], groupBy: null };
  }
  // Schedule adherence
  else if (lowerQuery.includes('schedule') || lowerQuery.includes('adherence')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['schedule_adherence_pct'], groupBy: null };
  }
  // Batch count
  else if (lowerQuery.includes('batch') && (lowerQuery.includes('count') || lowerQuery.includes('how many'))) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['batch_count'], groupBy: null };
  }
  // Stockouts
  else if (lowerQuery.includes('stockout')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['stockouts_count'], groupBy: null };
  }
  // Alarms
  else if (lowerQuery.includes('alarm')) {
    parsedIntent = { dataType: 'weekly_kpi', metrics: ['alarms_per_1000_hours'], groupBy: null };
  }
  // Formulation lead time
  else if (lowerQuery.includes('formulation') || lowerQuery.includes('lead time')) {
    parsedIntent = { dataType: 'monthly_kpi', metrics: ['formulation_lead_time_hr'], groupBy: null };
  }
  // Lab turnaround
  else if (lowerQuery.includes('lab') || lowerQuery.includes('turnaround')) {
    parsedIntent = { dataType: 'monthly_kpi', metrics: ['lab_turnaround_median_days'], groupBy: null };
  }
  // Supplier OTIF
  else if (lowerQuery.includes('supplier') || lowerQuery.includes('otif')) {
    parsedIntent = { dataType: 'monthly_kpi', metrics: ['supplier_otif_pct'], groupBy: null };
  }
  // Default: All KPIs
  else {
    // Use LLM for ambiguous queries
    try {
      parsedIntent = await callClaudeForJson<ManufacturingIntent>(
        PARSE_INTENT_PROMPT,
        `Parse: "${userQuery}"`
      );
    } catch {
      // Fallback to all main KPIs
      parsedIntent = {
        dataType: 'weekly_kpi',
        metrics: ['batch_yield_avg_pct', 'rft_pct', 'oee_packaging_pct', 'avg_cycle_time_hr'],
        groupBy: null
      };
    }
  }

  await logAgentStep({
    sessionId,
    agentName: "KPI Gateway",
    inputSummary: userQuery,
    outputSummary: `Parsed: ${parsedIntent.dataType}, metrics: ${parsedIntent.metrics?.join(', ') || 'all'}, groupBy: ${parsedIntent.groupBy || 'none'}`,
    reasoningSummary: "Extracting requested KPI metrics from data store.",
    status: "success",
  });

  // Generate SQL
  const generatedSql = generateSql(parsedIntent, monthCount, skuFilter);

  // Fetch data based on intent with metadata for edge case handling
  let dataPoints: { label: string; value: number }[] = [];
  let kpiName = 'kpi_summary';
  let availabilityInfo: DataAvailabilityInfo | null = null;

  if (parsedIntent.groupBy === 'status') {
    // Batch status breakdown
    const byStatus = repo.getBatchesByStatus();
    dataPoints = byStatus.map(s => ({ label: s.status, value: s.count }));
    kpiName = 'batch_status';
  } else if (parsedIntent.groupBy === 'equipment') {
    // Equipment breakdown
    const byEquipment = repo.getBatchesByEquipment();
    dataPoints = byEquipment.slice(0, 8).map(e => ({ label: e.equipment, value: e.count }));
    kpiName = 'equipment_batches';
  } else if (isTimeRangeQuery && monthCount) {
    // Time range query - get monthly breakdown with metadata
    const metric = parsedIntent.metrics?.[0] || 'oee_packaging_pct';
    const result = repo.getKpiByMonthWithMetadata(metric, monthCount, skuFilter);
    dataPoints = result.dataPoints;
    availabilityInfo = result.metadata;
    kpiName = skuFilter ? `${metric}_${skuFilter}` : `${metric}_monthly`;
  } else if (parsedIntent.dataType === 'monthly_kpi') {
    // Monthly KPI query (e.g., formulation lead time) - get latest month with metadata
    const metric = parsedIntent.metrics?.[0] || 'formulation_lead_time_hr';
    const result = repo.getKpiByMonthWithMetadata(metric, 1, skuFilter);
    dataPoints = result.dataPoints;
    availabilityInfo = result.metadata;
    kpiName = skuFilter ? `${metric}_${skuFilter}` : metric;
  } else {
    // Direct KPI metrics
    const metrics = parsedIntent.metrics || ['batch_yield_avg_pct', 'rft_pct', 'oee_packaging_pct', 'avg_cycle_time_hr'];

    for (const metric of metrics) {
      const summary = repo.getKpiSummary(metric);
      if (summary.count > 0) {
        dataPoints.push({
          label: METRIC_LABELS[metric] || metric,
          value: Math.round(summary.average * 100) / 100
        });
      }
    }
    kpiName = metrics.length === 1 ? metrics[0] : 'kpi_overview';
  }

  // Generate explanation with data availability awareness
  const explanation = generateExplanationWithMetadata(
    parsedIntent.metrics || ['batch_yield_avg_pct', 'rft_pct', 'oee_packaging_pct'],
    dataPoints,
    parsedIntent.groupBy,
    isTimeRangeQuery || parsedIntent.dataType === 'monthly_kpi',
    skuFilter,
    availabilityInfo
  );

  const kpiResult: KpiResult = {
    kpiName,
    breakdownBy: parsedIntent.groupBy || null,
    dataPoints,
    explanation,
  };

  await logAgentStep({
    sessionId,
    agentName: "KPI Gateway",
    inputSummary: `Retrieved ${dataPoints.length} data points`,
    outputSummary: explanation.substring(0, 100),
    reasoningSummary: availabilityInfo && availabilityInfo.requestedMonths && availabilityInfo.availableMonths < availabilityInfo.requestedMonths
      ? `Data availability: requested ${availabilityInfo.requestedMonths} months, available ${availabilityInfo.availableMonths} months`
      : "Successfully retrieved KPI data. Returning formatted response.",
    status: "success",
  });

  return {
    kpiResults: [kpiResult],
    generatedSql
  };
}

export async function handleComparison(
  sessionId: string,
  _userQuery: string,
  currentResults: KpiResult[]
): Promise<KpiResult[]> {
  await logAgentStep({
    sessionId,
    agentName: "KPI Gateway",
    inputSummary: "Comparison analysis",
    outputSummary: "Returning current results",
    status: "success",
  });
  return currentResults;
}
