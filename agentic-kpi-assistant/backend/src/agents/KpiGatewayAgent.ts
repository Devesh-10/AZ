import { ParsedIntent, KpiResult } from "../types";
import { callClaudeForJson, callClaudeForText } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import { getSustainabilityDataRepository, SustainabilityResult } from "../dataAccess/SustainabilityDataRepository";

// SQL generation result
export interface KpiGatewayResult {
  kpiResults: KpiResult[];
  generatedSql: string;
}

const PARSE_INTENT_PROMPT = `You are a sustainability KPI query parser for AstraZeneca. Extract structured information from user questions about environmental and sustainability metrics.

Available Data Categories:
- Energy: consumption, renewable energy, imported energy (unit: MWh)
- GHG Emissions: Scope 1 (F-gases, road fleet), Scope 2 (market-based, location-based) (unit: tCO2)
- Water: groundwater usage, municipal supply (unit: Million m³)
- Waste: site waste, product waste (unit: Tonnes)
- EV Transition: BEV count, total fleet, electrification percentage

Specific Metrics (use these exact values in the metrics array):
- Energy: "total_energy", "renewable_energy", "imported_energy"
- GHG Emissions: "scope1_fgases", "scope1_fleet", "scope2_market", "scope2_location"
- Water: "groundwater", "municipal_supply"
- Waste: "site_waste", "product_waste"
- EV: "bev_count", "total_fleet", "bev_percentage"

Available Dimensions:
- site: AstraZeneca facility locations (e.g., Baar, Macclesfield, Gaithersburg)
- year: 2023, 2024, 2025
- quarter: 1, 2, 3, 4
- month: 1-12
- scope: Scope 1, Scope 2, Scope 1 & 2 (for emissions)
- market/geography: for fleet data

Parse the user's question and return a JSON object with:
{
  "dataType": "energy" | "ghg_emissions" | "water" | "waste" | "ev_transition",
  "metrics": ["specific_metric_name"] | null,
  "year": 2024 | null,
  "quarter": 1-4 | null,
  "month": 1-12 | null,
  "siteName": "site name" | null,
  "scope": "Scope 1" | "Scope 2" | null,
  "groupBy": "site" | "month" | "quarter" | "year" | null
}

Rules:
- Identify the main data category from the question
- If user asks about a SPECIFIC metric (like "imported energy", "renewable energy", "groundwater"), set metrics array with that specific metric
- If user asks about ALL metrics or "total" in a category, set metrics to null
- Extract time filters (year, quarter, month)
- Extract site filters if mentioned
- Set groupBy if user wants breakdown (e.g., "by site", "over time", "monthly trend")
- For emissions questions, identify if specific scope is requested

Examples:
"What is our total energy consumption?" → dataType: "energy", metrics: null
"How much is imported energy?" → dataType: "energy", metrics: ["imported_energy"]
"What is our renewable energy usage?" → dataType: "energy", metrics: ["renewable_energy"]
"Show me GHG emissions for 2024" → dataType: "ghg_emissions", metrics: null, year: 2024
"Water usage by site" → dataType: "water", metrics: null, groupBy: "site"
"How much groundwater do we use?" → dataType: "water", metrics: ["groundwater"]
"How many electric vehicles do we have?" → dataType: "ev_transition", metrics: ["bev_count"]
"Scope 1 emissions trend" → dataType: "ghg_emissions", scope: "Scope 1", groupBy: "month"
"Waste generated at Baar site" → dataType: "waste", metrics: null, siteName: "Baar"`;

const EXPLAIN_RESULTS_PROMPT = `You are a sustainability analyst. Given environmental KPI results, provide a brief, clear explanation.

Data Type: {dataType}
Metrics: {metrics}
Data points: {dataPoints}
Summary: {summary}

Write a 2-3 sentence explanation of what these numbers show. Include context about sustainability impact where relevant. Be specific with the actual values.`;

interface SustainabilityIntent {
  dataType: 'energy' | 'ghg_emissions' | 'water' | 'waste' | 'ev_transition';
  metrics?: string[];
  year?: number;
  quarter?: number;
  month?: number;
  siteName?: string;
  scope?: string;
  groupBy?: 'site' | 'month' | 'quarter' | 'year';
}

// Generate SQL-like query for display
function generateSqlFromIntent(intent: SustainabilityIntent): string {
  const tableMap: Record<string, string> = {
    'energy': 'ENERGY_QUARTERLY_SUMMARY',
    'ghg_emissions': 'GHG_EMISSIONS_QUARTERLY_SUMMARY',
    'water': 'WATER_MONTHLY_SUMMARY',
    'waste': 'WASTE_MONTHLY_SUMMARY',
    'ev_transition': 'EV_TRANSITION_QUARTERLY_SUMMARY'
  };

  const columnsMap: Record<string, string[]> = {
    'energy': ['SHE_SITE_NAME', 'REPORTING_YEAR_NUMBER', 'REPORTING_QUARTER_NUMBER', 'ENERGY_SITE_MWH_QUANTITY', 'ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY', 'ENERGY_IMPORTED_MWH_QUANTITY'],
    'ghg_emissions': ['SHE_SITE_NAME', 'REPORTING_YEAR_NUMBER', 'REPORTING_QUARTER_NUMBER', 'SCOPE1_ROAD_FLEET_TCO2_QUANTITY', 'SCOPE1_F_GASES_TCO2_QUANTITY', 'SCOPE1_TOTAL_TCO2_QUANTITY', 'SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY', 'SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY'],
    'water': ['SHE_SITE_NAME', 'REPORTING_YEAR_NUMBER', 'REPORTING_MONTH_NUMBER', 'GROUNDWATER_MILLION_M3_QUANTITY', 'MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY'],
    'waste': ['SHE_SITE_NAME', 'REPORTING_YEAR_NUMBER', 'REPORTING_MONTH_NUMBER', 'WASTE_TONNES_SITE_QUANTITY', 'WASTE_TONNES_PRODUCT_QUANTITY'],
    'ev_transition': ['SHE_MARKET_NAME', 'SHE_GEOGRAPHY_NAME', 'REPORTING_YEAR_NUMBER', 'REPORTING_QUARTER_NUMBER', 'TOTAL_BEV_COUNT', 'TOTAL_FLEET_ASSET_COUNT']
  };

  const table = tableMap[intent.dataType] || 'SUSTAINABILITY_DATA';
  const columns = columnsMap[intent.dataType] || ['*'];

  let selectClause = 'SELECT';
  let groupByClause = '';

  if (intent.groupBy === 'site') {
    selectClause += `\n    SHE_SITE_NAME,`;
    groupByClause = '\nGROUP BY SHE_SITE_NAME';
  } else if (intent.groupBy === 'quarter') {
    selectClause += `\n    REPORTING_YEAR_NUMBER,\n    REPORTING_QUARTER_NUMBER,`;
    groupByClause = '\nGROUP BY REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER';
  } else if (intent.groupBy === 'month') {
    selectClause += `\n    REPORTING_YEAR_NUMBER,\n    REPORTING_MONTH_NUMBER,`;
    groupByClause = '\nGROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER';
  } else if (intent.groupBy === 'year') {
    selectClause += `\n    REPORTING_YEAR_NUMBER,`;
    groupByClause = '\nGROUP BY REPORTING_YEAR_NUMBER';
  }

  // Add aggregated columns
  const metricColumns = columns.filter(c =>
    c.includes('QUANTITY') || c.includes('COUNT')
  );

  if (groupByClause) {
    selectClause += metricColumns.map(c => `\n    SUM(${c}) AS TOTAL_${c}`).join(',');
  } else {
    selectClause += metricColumns.map(c => `\n    SUM(${c}) AS TOTAL_${c}`).join(',');
  }

  let whereClause = '';
  const conditions: string[] = [];

  if (intent.year) {
    conditions.push(`REPORTING_YEAR_NUMBER = ${intent.year}`);
  }
  if (intent.quarter) {
    conditions.push(`REPORTING_QUARTER_NUMBER = ${intent.quarter}`);
  }
  if (intent.month) {
    conditions.push(`REPORTING_MONTH_NUMBER = ${intent.month}`);
  }
  if (intent.siteName) {
    conditions.push(`SHE_SITE_NAME LIKE '%${intent.siteName}%'`);
  }
  if (intent.scope) {
    conditions.push(`REPORTING_SCOPE_NAME = '${intent.scope}'`);
  }

  if (conditions.length > 0) {
    whereClause = '\nWHERE ' + conditions.join('\n  AND ');
  }

  const orderByClause = intent.groupBy
    ? `\nORDER BY ${intent.groupBy === 'site' ? 'SHE_SITE_NAME' : intent.groupBy === 'quarter' ? 'REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER' : intent.groupBy === 'month' ? 'REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER' : 'REPORTING_YEAR_NUMBER'}`
    : '';

  return `${selectClause}\nFROM ${table}${whereClause}${groupByClause}${orderByClause};`;
}

export async function parseAndFetchKpi(
  sessionId: string,
  userQuery: string
): Promise<KpiGatewayResult> {
  const repo = getSustainabilityDataRepository();

  // Step 1: Parse the user's intent
  let parsedIntent: SustainabilityIntent;

  try {
    parsedIntent = await callClaudeForJson<SustainabilityIntent>(
      PARSE_INTENT_PROMPT,
      `Parse this query: "${userQuery}"`
    );

    const filtersApplied = [
      parsedIntent.year && `year: ${parsedIntent.year}`,
      parsedIntent.quarter && `Q${parsedIntent.quarter}`,
      parsedIntent.siteName && `site: ${parsedIntent.siteName}`,
      parsedIntent.scope && parsedIntent.scope,
      parsedIntent.groupBy && `grouped by ${parsedIntent.groupBy}`,
    ].filter(Boolean).join(", ") || "no filters";

    await logAgentStep({
      sessionId,
      agentName: "KPI Gateway",
      inputSummary: userQuery,
      outputSummary: `Parsed intent: dataType=${parsedIntent.dataType}, year=${parsedIntent.year || 'all'}, groupBy=${parsedIntent.groupBy || 'none'}`,
      reasoningSummary: `I identified this as a ${parsedIntent.dataType.replace('_', ' ')} query. Extracting data with filters: ${filtersApplied}. Will query the ${parsedIntent.dataType.replace('_', ' ').toUpperCase()} summary table.`,
      status: "success",
    });
  } catch (error) {
    await logAgentStep({
      sessionId,
      agentName: "KPI Gateway",
      inputSummary: userQuery,
      outputSummary: `Parse error: ${error}`,
      status: "error",
    });
    throw error;
  }

  // Generate SQL from parsed intent
  const generatedSql = generateSqlFromIntent(parsedIntent);

  // Step 2: Query the appropriate data based on parsed intent
  let sustainabilityResult: SustainabilityResult;

  const queryOptions = {
    year: parsedIntent.year,
    quarter: parsedIntent.quarter,
    month: parsedIntent.month,
    siteName: parsedIntent.siteName,
    groupBy: parsedIntent.groupBy,
  };

  switch (parsedIntent.dataType) {
    case 'energy':
      sustainabilityResult = repo.getEnergyConsumption(queryOptions);
      break;
    case 'ghg_emissions':
      sustainabilityResult = repo.getGHGEmissions({
        ...queryOptions,
        scope: parsedIntent.scope,
      });
      break;
    case 'water':
      sustainabilityResult = repo.getWaterUsage(queryOptions);
      break;
    case 'waste':
      sustainabilityResult = repo.getWaste(queryOptions);
      break;
    case 'ev_transition':
      sustainabilityResult = repo.getEVTransition({
        year: parsedIntent.year,
        quarter: parsedIntent.quarter,
      });
      break;
    default:
      sustainabilityResult = {
        dataType: 'unknown',
        metrics: [],
        dataPoints: [],
        summary: 'Could not determine the data type requested.',
      };
  }

  // Step 3: Filter data points if specific metrics were requested
  let filteredDataPoints = sustainabilityResult.dataPoints;
  let customSummary = sustainabilityResult.summary;

  if (parsedIntent.metrics && parsedIntent.metrics.length > 0) {
    // Map metric names to data point labels
    const metricLabelMap: Record<string, string[]> = {
      // Energy
      'total_energy': ['Total Energy'],
      'renewable_energy': ['Renewable Energy'],
      'imported_energy': ['Imported Energy'],
      // GHG Emissions
      'scope1_fgases': ['Scope 1 F-Gases'],
      'scope1_fleet': ['Scope 1 Road Fleet'],
      'scope2_market': ['Scope 2 Market-Based'],
      'scope2_location': ['Scope 2 Location-Based'],
      // Water
      'groundwater': ['Groundwater'],
      'municipal_supply': ['Municipal Supply'],
      // Waste
      'site_waste': ['Site Waste'],
      'product_waste': ['Product Waste'],
      // EV
      'bev_count': ['Battery Electric Vehicles'],
      'total_fleet': ['Total Fleet'],
      'bev_percentage': ['BEV Percentage'],
    };

    const requestedLabels: string[] = [];
    parsedIntent.metrics.forEach(metric => {
      const labels = metricLabelMap[metric] || [];
      requestedLabels.push(...labels);
    });

    if (requestedLabels.length > 0) {
      filteredDataPoints = sustainabilityResult.dataPoints.filter(dp =>
        requestedLabels.some(label => dp.label.toLowerCase().includes(label.toLowerCase()))
      );

      // Generate custom summary for filtered data
      if (filteredDataPoints.length > 0) {
        const summaryParts = filteredDataPoints.map(dp => `${dp.label}: ${dp.value.toLocaleString()} ${dp.unit}`);
        customSummary = summaryParts.join(', ');
      }
    }
  }

  // Use the filtered data summary
  const explanation = customSummary;

  const kpiResult: KpiResult = {
    kpiName: sustainabilityResult.dataType,
    breakdownBy: parsedIntent.groupBy || null,
    dataPoints: filteredDataPoints.map((dp) => ({
      label: dp.label,
      value: dp.value,
    })),
    explanation: explanation.trim(),
  };

  // Add breakdown data if available
  if (sustainabilityResult.breakdown) {
    kpiResult.dataPoints = [
      ...kpiResult.dataPoints,
      ...sustainabilityResult.breakdown.data.map((d) => ({
        label: `${sustainabilityResult.breakdown!.dimension}: ${d.label}`,
        value: d.value,
      })),
    ];
  }

  await logAgentStep({
    sessionId,
    agentName: "KPI Gateway",
    inputSummary: `Fetched ${parsedIntent.dataType} data`,
    outputSummary: `Retrieved ${sustainabilityResult.dataPoints.length} metrics: ${sustainabilityResult.summary}`,
    reasoningSummary: `Successfully queried ${parsedIntent.dataType.replace('_', ' ')} data. Found ${sustainabilityResult.dataPoints.length} data points. Generating natural language explanation for the user.`,
    status: "success",
  });

  return {
    kpiResults: [kpiResult],
    generatedSql
  };
}

/**
 * Handle comparison queries (vs previous period, etc.)
 */
export async function handleComparison(
  sessionId: string,
  userQuery: string,
  currentResults: KpiResult[]
): Promise<KpiResult[]> {
  // For now, return the current results
  // A more sophisticated implementation would fetch comparison period data
  // and calculate deltas/percentages

  await logAgentStep({
    sessionId,
    agentName: "KPI Gateway",
    inputSummary: "Comparison analysis",
    outputSummary: "Comparison feature placeholder - returning current results",
    status: "success",
  });

  return currentResults;
}
