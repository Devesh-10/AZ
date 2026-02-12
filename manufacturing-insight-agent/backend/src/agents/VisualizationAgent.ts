import { KpiResult, AnalystResult, VisualizationConfig } from "../types";
import { logAgentStep } from "../core/telemetryStore";
import { loadPrompt, PROMPTS } from "../prompts";

/**
 * Visualization Agent
 *
 * Maps KPI results to appropriate visualization configurations.
 * Uses deterministic logic (no LLM calls) for speed and consistency.
 *
 * Uses external prompt file: prompts/visualization_agent.md
 */

// Load prompt template at module init (for documentation/reference)
const _visualizationPromptTemplate = loadPrompt(PROMPTS.VISUALIZATION);

export async function generateVisualization(
  sessionId: string,
  kpiResults?: KpiResult[],
  analystResult?: AnalystResult
): Promise<VisualizationConfig | undefined> {
  // Skip visualization for complex analyst queries - they have narrative answers
  if (analystResult?.narrative) {
    await logAgentStep({
      sessionId,
      agentName: "Visualization",
      inputSummary: "Complex analyst query",
      outputSummary: "Skipping chart - using tabular data in narrative",
      reasoningSummary: "Complex queries are better served with detailed narrative and tabular data rather than charts.",
      status: "success",
    });
    return undefined;
  }

  // Use direct KPI results only
  const results = kpiResults || [];

  if (results.length === 0) {
    await logAgentStep({
      sessionId,
      agentName: "Visualization",
      inputSummary: "No results to visualize",
      outputSummary: "Skipping visualization - no data",
      reasoningSummary: "No data available for visualization. The response will be text-only.",
      status: "success",
    });
    return undefined;
  }

  // Find the primary result (most data points or first one)
  const primaryResult = results.reduce((best, current) =>
    current.dataPoints.length > best.dataPoints.length ? current : best
  );

  if (primaryResult.dataPoints.length === 0) {
    return undefined;
  }

  // Determine chart type based on breakdown dimension
  const chartType = determineChartType(primaryResult);

  // Build series data - filter to show only the main KPI data (not breakdown duplicates)
  // Group by KPI and deduplicate to match table display
  const primaryKpiName = results[0]?.kpiName;
  const primaryResults = results.filter(r => r.kpiName === primaryKpiName);

  // Collect and dedupe data points (same logic as frontend table)
  const deduped = new Map<string, { label: string; value: number }>();
  primaryResults.forEach(result => {
    result.dataPoints.forEach(dp => {
      const lowerLabel = dp.label.toLowerCase();
      // Skip meta labels like "Total Records"
      if (lowerLabel.includes('record')) return;
      // Skip breakdown prefixed labels (e.g., "Site: Baar", "Month: 2024-01")
      if (dp.label.includes(':')) return;

      const existing = deduped.get(dp.label);
      if (!existing || dp.value > existing.value) {
        deduped.set(dp.label, { label: dp.label, value: dp.value });
      }
    });
  });

  // Convert to array and sort by value descending, limit to top 5
  const uniqueDataPoints = Array.from(deduped.values())
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  // Filter out total rows from chart - only show category data (same as table)
  const categoryDataPoints = uniqueDataPoints.filter(
    dp => !dp.label.toLowerCase().startsWith('total')
  );

  // If no category data points to show, skip visualization entirely
  if (categoryDataPoints.length === 0) {
    await logAgentStep({
      sessionId,
      agentName: "Visualization",
      inputSummary: `${results.length} KPI results`,
      outputSummary: "Skipping chart - only total/summary data available",
      reasoningSummary: "No category breakdown data available for visualization. The response will include table data only.",
      status: "success",
    });
    return undefined;
  }

  const series = [{
    name: formatKpiName(primaryKpiName || 'Data'),
    data: categoryDataPoints.map((dp) => ({
      x: dp.label,
      y: dp.value,
    })),
  }];

  const config: VisualizationConfig = {
    chartType,
    title: generateTitle(results),
    xLabel: primaryResult.breakdownBy
      ? formatDimensionLabel(primaryResult.breakdownBy)
      : undefined,
    yLabel: results.length === 1 ? getKpiUnit(results[0].kpiName) : "Value",
    series,
  };

  const totalDataPoints = series.reduce((sum, s) => sum + s.data.length, 0);
  await logAgentStep({
    sessionId,
    agentName: "Visualization",
    inputSummary: `${results.length} KPI results`,
    outputSummary: `Generated ${chartType} chart with ${series.length} series`,
    reasoningSummary: `Selected ${chartType} chart as the best visualization for this data. Rendering ${totalDataPoints} data points across ${series.length} series. Chart title: "${config.title}". Ready to display to user.`,
    status: "success",
  });

  return config;
}

/**
 * Determine the best chart type based on the data
 */
function determineChartType(
  result: KpiResult
): "line" | "bar" | "pie" {
  const { breakdownBy, dataPoints } = result;

  // Time-based breakdowns → line chart
  if (breakdownBy === "date" || breakdownBy === "month") {
    return "line";
  }

  // Categorical breakdowns with few categories → pie chart (if single KPI)
  if (dataPoints.length <= 5 && dataPoints.length > 1) {
    // Check if it looks like a distribution
    const total = dataPoints.reduce((sum, dp) => sum + dp.value, 0);
    const isDistribution = dataPoints.every((dp) => dp.value > 0 && dp.value < total);
    if (isDistribution && breakdownBy) {
      return "pie";
    }
  }

  // Default to bar chart for categorical data
  if (breakdownBy === "region" || breakdownBy === "product" || breakdownBy === "segment") {
    return "bar";
  }

  // Single data point or unknown → bar
  return "bar";
}

/**
 * Generate a descriptive title for the chart
 */
function generateTitle(results: KpiResult[]): string {
  if (results.length === 0) return "KPI Data";

  const kpiNames = results.map((r) => formatKpiName(r.kpiName));
  const uniqueKpis = [...new Set(kpiNames)];

  const breakdownBy = results[0].breakdownBy;
  const breakdownStr = breakdownBy ? ` by ${formatDimensionLabel(breakdownBy)}` : "";

  if (uniqueKpis.length === 1) {
    return `${uniqueKpis[0]}${breakdownStr}`;
  }

  if (uniqueKpis.length <= 3) {
    return `${uniqueKpis.join(" vs ")}${breakdownStr}`;
  }

  return `KPI Comparison${breakdownStr}`;
}

/**
 * Format KPI name for display
 */
function formatKpiName(kpiName: string): string {
  const formatMap: Record<string, string> = {
    revenue: "Revenue",
    cost: "Cost",
    margin_pct: "Margin %",
    units_sold: "Units Sold",
    customer_count: "Customer Count",
  };

  return formatMap[kpiName] || kpiName
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Format dimension name for labels
 */
function formatDimensionLabel(dimension: string): string {
  const formatMap: Record<string, string> = {
    date: "Date",
    month: "Month",
    region: "Region",
    product: "Product",
    segment: "Segment",
  };

  return formatMap[dimension] || dimension.charAt(0).toUpperCase() + dimension.slice(1);
}

/**
 * Get the unit label for a KPI
 */
function getKpiUnit(kpiName: string): string {
  const unitMap: Record<string, string> = {
    revenue: "USD",
    cost: "USD",
    margin_pct: "%",
    units_sold: "Units",
    customer_count: "Customers",
  };

  return unitMap[kpiName] || "Value";
}

/**
 * Create a simple visualization for a single total value
 */
export function createSingleValueViz(
  kpiName: string,
  value: number
): VisualizationConfig {
  return {
    chartType: "bar",
    title: formatKpiName(kpiName),
    series: [
      {
        name: formatKpiName(kpiName),
        data: [{ x: "Total", y: value }],
      },
    ],
  };
}
