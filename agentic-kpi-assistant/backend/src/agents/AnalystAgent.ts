/**
 * Analyst Agent
 *
 * DATA PERIMETER: Foundational (Master Data) + Transaction Data ONLY
 * This agent does NOT have access to KPI Summary tables.
 *
 * Purpose: Deep analysis, cross-domain correlations, root cause analysis
 */

import { AnalystResult, KpiResult } from "../types";
import { callClaudeForJson, callClaudeForText } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import { getAnalyticsDataRepository } from "../dataAccess/AnalyticsDataRepository";
import knowledgeGraphData from "../data/knowledgeGraph.json";

// Result type that includes SQL
export interface AnalystAgentResult {
  analystResult: AnalystResult;
  generatedSql: string;
}

interface AnalysisPlan {
  dataQueries: {
    description: string;
    dataType: 'fleet' | 'energy' | 'emissions' | 'waste' | 'water' | 'sites';
    queryType: 'summary' | 'by_site' | 'by_type' | 'detailed';
    filters?: {
      siteId?: number;
      siteName?: string;
      type?: string;
    };
  }[];
  analysisApproach: string;
}

const PLAN_ANALYSIS_PROMPT = `You are a Sustainability Analyst with access to FOUNDATIONAL and TRANSACTION-LEVEL data.

## YOUR DATA PERIMETER (What you CAN access):

### Master Data (Foundational):
- Sites: Site names, codes, countries, reporting scopes
- Indicators: Sustainability indicator definitions
- Measurement Types: Units and measurement definitions

### Transaction Data (Granular/Analytics):
- Fleet Asset Inventory: Individual vehicle records by site, asset type (Car, Van, Truck), powertrain type (Diesel, Petrol, Electric, Hybrid, PHEV, BEV)
- Fleet Fuel Consumption: Fuel usage by site and powertrain type
- Fleet Mileage: Distance traveled by site and asset type
- Energy Consumption: Detailed energy records by site and energy type
- GHG Emissions: Detailed emission records by site, scope (Scope 1, Scope 2), and source
- Waste Records: Waste data by site and waste type
- Water Usage: Water consumption by site and water source

## IMPORTANT: You do NOT have access to KPI Summary tables (those go to KPI Mart Agent)

## User Question: {userQuestion}

## Knowledge Graph (relationships):
{knowledgeGraph}

Plan your analysis by identifying what foundational/transaction data to query:

{
  "dataQueries": [
    {
      "description": "What this query shows",
      "dataType": "fleet" | "energy" | "emissions" | "waste" | "water" | "sites",
      "queryType": "summary" | "by_site" | "by_type" | "detailed",
      "filters": {
        "siteId": number | null,
        "siteName": "name" | null,
        "type": "specific type" | null
      }
    }
  ],
  "analysisApproach": "How you'll analyze and correlate the data"
}

Focus on transaction-level insights that KPI summaries can't provide (e.g., fleet composition by powertrain, site-specific patterns, granular breakdowns).`;

const GENERATE_NARRATIVE_PROMPT = `You are a Sustainability Analyst. Write a brief executive summary.

Question: {userQuestion}

Data: {dataResults}

Write ONLY 2-3 sentences:
1. State the key finding with the main number
2. Note the biggest contributor or trend
3. Give one specific recommendation

Keep it under 40 words total. Use **bold** for important numbers. Do NOT create tables - tables will be added automatically.`;

const EXTRACT_INSIGHTS_PROMPT = `Extract 2-3 key insights from this analysis as bullet points.

Analysis: {narrative}

Return JSON array of strings:
["Insight 1", "Insight 2", "Insight 3"]`;

// Generate SQL from analysis plan
function generateSqlFromPlan(plan: AnalysisPlan): string {
  const tableMap: Record<string, string> = {
    'fleet': 'FLEET_ASSET_INVENTORY',
    'energy': 'ENERGY_CONSUMPTION_TRANSACTIONS',
    'emissions': 'GHG_EMISSIONS_TRANSACTIONS',
    'waste': 'WASTE_TRANSACTIONS',
    'water': 'WATER_USAGE_TRANSACTIONS',
    'sites': 'SHE_SITES_MASTER'
  };

  const columnsMap: Record<string, string[]> = {
    'fleet': ['ASSET_ID', 'SHE_SITE_NAME', 'ASSET_TYPE_NAME', 'POWERTRAIN_TYPE_NAME', 'ASSET_COUNT'],
    'energy': ['TRANSACTION_ID', 'SHE_SITE_NAME', 'ENERGY_TYPE_NAME', 'CONSUMPTION_VALUE', 'REPORTING_YEAR'],
    'emissions': ['TRANSACTION_ID', 'SHE_SITE_NAME', 'SCOPE_NAME', 'SOURCE_NAME', 'TCO2_VALUE', 'REPORTING_YEAR'],
    'waste': ['TRANSACTION_ID', 'SHE_SITE_NAME', 'WASTE_TYPE_NAME', 'TONNES_VALUE', 'REPORTING_YEAR'],
    'water': ['TRANSACTION_ID', 'SHE_SITE_NAME', 'WATER_SOURCE_NAME', 'MILLION_M3_VALUE', 'REPORTING_YEAR'],
    'sites': ['SITE_ID', 'SHE_SITE_NAME', 'COUNTRY_NAME', 'REPORTING_SCOPE_NAME']
  };

  const sqlStatements: string[] = [];

  for (const query of plan.dataQueries) {
    const table = tableMap[query.dataType] || 'SUSTAINABILITY_DATA';
    const columns = columnsMap[query.dataType] || ['*'];

    let selectClause = 'SELECT';
    let groupByClause = '';

    if (query.queryType === 'by_site') {
      selectClause += '\n    SHE_SITE_NAME,';
      groupByClause = '\nGROUP BY SHE_SITE_NAME';
    } else if (query.queryType === 'by_type') {
      const typeColumn = query.dataType === 'fleet' ? 'POWERTRAIN_TYPE_NAME' :
                         query.dataType === 'energy' ? 'ENERGY_TYPE_NAME' :
                         query.dataType === 'emissions' ? 'SCOPE_NAME' :
                         query.dataType === 'waste' ? 'WASTE_TYPE_NAME' :
                         query.dataType === 'water' ? 'WATER_SOURCE_NAME' : 'TYPE_NAME';
      selectClause += `\n    ${typeColumn},`;
      groupByClause = `\nGROUP BY ${typeColumn}`;
    }

    // Add aggregated columns
    const valueColumn = query.dataType === 'fleet' ? 'ASSET_COUNT' :
                        query.dataType === 'energy' ? 'CONSUMPTION_VALUE' :
                        query.dataType === 'emissions' ? 'TCO2_VALUE' :
                        query.dataType === 'waste' ? 'TONNES_VALUE' :
                        query.dataType === 'water' ? 'MILLION_M3_VALUE' : 'VALUE';

    if (groupByClause) {
      selectClause += `\n    SUM(${valueColumn}) AS TOTAL_VALUE,\n    COUNT(*) AS RECORD_COUNT`;
    } else {
      selectClause += `\n    ${columns.join(',\n    ')}`;
    }

    let whereClause = '';
    const conditions: string[] = [];

    if (query.filters?.siteName) {
      conditions.push(`SHE_SITE_NAME LIKE '%${query.filters.siteName}%'`);
    }
    if (query.filters?.type) {
      const typeColumn = query.dataType === 'fleet' ? 'POWERTRAIN_TYPE_NAME' :
                         query.dataType === 'emissions' ? 'SCOPE_NAME' : 'TYPE_NAME';
      conditions.push(`${typeColumn} = '${query.filters.type}'`);
    }

    if (conditions.length > 0) {
      whereClause = '\nWHERE ' + conditions.join('\n  AND ');
    }

    const orderByClause = groupByClause ? '\nORDER BY TOTAL_VALUE DESC' : '';

    sqlStatements.push(`-- ${query.description}\n${selectClause}\nFROM ${table}${whereClause}${groupByClause}${orderByClause};`);
  }

  return sqlStatements.join('\n\n');
}

export async function analyzeComplexQuery(
  sessionId: string,
  userQuery: string
): Promise<AnalystAgentResult> {
  const repo = getAnalyticsDataRepository();
  const summary = repo.getDataSummary();

  // Format knowledge graph for context
  const kgSummary = knowledgeGraphData.kpis
    .map((k) => `${k.name}: ${k.description} (related to: ${k.relatedKpis.join(", ")})`)
    .join("\n");

  // Step 1: Plan the analysis
  const planPrompt = PLAN_ANALYSIS_PROMPT
    .replace("{knowledgeGraph}", kgSummary)
    .replace("{userQuestion}", userQuery);

  let plan: AnalysisPlan;

  try {
    plan = await callClaudeForJson<AnalysisPlan>(planPrompt, "Create analysis plan");

    // Validate plan structure
    if (!plan || !plan.dataQueries || !Array.isArray(plan.dataQueries)) {
      plan = {
        dataQueries: [
          { description: "Get emissions overview", dataType: "emissions", queryType: "by_type" },
          { description: "Get energy consumption", dataType: "energy", queryType: "by_type" }
        ],
        analysisApproach: "Analyze emissions and energy patterns to identify main contributors"
      };
    }

    const dataTypesQueried = [...new Set(plan.dataQueries.map(q => q.dataType))].join(", ");
    await logAgentStep({
      sessionId,
      agentName: "Analyst",
      inputSummary: userQuery,
      outputSummary: `Planned ${plan.dataQueries.length} queries on transaction data: ${plan.analysisApproach}`,
      reasoningSummary: `I'm analyzing this complex query using foundational + transaction-level data (NOT pre-aggregated KPI summaries). Planning to query: ${dataTypesQueried}. My approach: ${plan.analysisApproach}`,
      status: "success",
    });
  } catch (error) {
    // Fallback plan if LLM call fails
    plan = {
      dataQueries: [
        { description: "Get emissions by scope", dataType: "emissions", queryType: "by_type" },
        { description: "Get energy by type", dataType: "energy", queryType: "by_type" },
        { description: "Get fleet analysis", dataType: "fleet", queryType: "summary" }
      ],
      analysisApproach: "Analyze emissions, energy, and fleet data to identify patterns and contributors"
    };

    await logAgentStep({
      sessionId,
      agentName: "Analyst",
      inputSummary: userQuery,
      outputSummary: `Using fallback analysis plan due to: ${error}`,
      status: "success",
    });
  }

  // Step 2: Execute data queries against transaction/master data
  const supportingResults: KpiResult[] = [];
  const rawDataResults: string[] = [];

  for (const query of plan.dataQueries) {
    let result: { label: string; value: number }[] = [];
    let rawData = "";

    switch (query.dataType) {
      case 'fleet':
        if (query.queryType === 'summary') {
          const evAnalysis = repo.getEVAnalysis();
          result = [
            { label: "Total Fleet", value: evAnalysis.totalFleet },
            { label: "Electric Vehicles", value: evAnalysis.electricVehicles },
            { label: "Hybrid Vehicles", value: evAnalysis.hybridVehicles },
            { label: "Conventional Vehicles", value: evAnalysis.conventionalVehicles },
            { label: "EV Percentage", value: evAnalysis.evPercentage }
          ];
          rawData = `Fleet Analysis: ${evAnalysis.totalFleet} total vehicles, ${evAnalysis.electricVehicles} EVs (${evAnalysis.evPercentage}%), ${evAnalysis.hybridVehicles} hybrids, ${evAnalysis.conventionalVehicles} conventional`;
        } else if (query.queryType === 'by_type') {
          const byPowertrain = repo.getFleetByPowertrainType();
          result = byPowertrain.map(p => ({ label: p.powertrainType, value: p.totalCount }));
          rawData = `Fleet by Powertrain: ${byPowertrain.map(p => `${p.powertrainType}: ${p.totalCount}`).join(", ")}`;
        } else {
          const inventory = repo.getFleetInventory();
          const totalCount = inventory.reduce((sum, i) => sum + i.count, 0);
          result = [{ label: "Total Fleet Assets", value: totalCount }];
          rawData = `Fleet Inventory: ${inventory.length} records, total count: ${totalCount}`;
        }
        break;

      case 'energy':
        if (query.queryType === 'by_type') {
          const byType = repo.getEnergyByType();
          result = byType.map(e => ({ label: e.energyType, value: e.totalValue }));
          rawData = `Energy by Type: ${byType.map(e => `${e.energyType}: ${e.totalValue}`).join(", ")}`;
        } else {
          const details = repo.getEnergyConsumptionDetails();
          const total = details.reduce((sum, d) => sum + d.value, 0);
          result = [{ label: "Total Energy Records", value: details.length }, { label: "Total Consumption", value: total }];
          rawData = `Energy: ${details.length} transaction records, total consumption: ${total}`;
        }
        break;

      case 'emissions':
        if (query.queryType === 'by_type') {
          const byScope = repo.getEmissionsByScope();
          result = byScope.map(e => ({ label: e.scopeType, value: e.totalValue }));
          rawData = `Emissions by Scope: ${byScope.map(e => `${e.scopeType}: ${e.totalValue}`).join(", ")}`;
        } else {
          const details = repo.getEmissionsDetails();
          const total = details.reduce((sum, d) => sum + d.value, 0);
          result = [{ label: "Total Emission Records", value: details.length }, { label: "Total Emissions", value: total }];
          rawData = `Emissions: ${details.length} transaction records, total: ${total}`;
        }
        break;

      case 'waste':
        const wasteDetails = repo.getWasteDetails();
        const wasteTotal = wasteDetails.reduce((sum, d) => sum + d.value, 0);
        result = [{ label: "Total Waste Records", value: wasteDetails.length }, { label: "Total Waste", value: wasteTotal }];
        rawData = `Waste: ${wasteDetails.length} transaction records, total: ${wasteTotal}`;
        break;

      case 'water':
        const waterDetails = repo.getWaterUsageDetails();
        const waterTotal = waterDetails.reduce((sum, d) => sum + d.value, 0);
        result = [{ label: "Total Water Records", value: waterDetails.length }, { label: "Total Water Usage", value: waterTotal }];
        rawData = `Water: ${waterDetails.length} transaction records, total: ${waterTotal}`;
        break;

      case 'sites':
        const sites = repo.getUniqueSiteNames();
        result = [{ label: "Total Sites", value: sites.length }];
        rawData = `Sites: ${sites.slice(0, 10).join(", ")}${sites.length > 10 ? ` and ${sites.length - 10} more` : ""}`;
        break;
    }

    if (result.length > 0) {
      supportingResults.push({
        kpiName: query.dataType,
        breakdownBy: query.queryType as any,
        dataPoints: result,
        explanation: query.description
      });
      rawDataResults.push(`${query.description}: ${rawData}`);
    }
  }

  await logAgentStep({
    sessionId,
    agentName: "Analyst",
    inputSummary: "Executing transaction data queries",
    outputSummary: `Retrieved ${supportingResults.length} result sets from foundational/transaction data`,
    reasoningSummary: `Executed all planned queries against transaction-level data. Collected raw data for: ${rawDataResults.slice(0, 3).map(r => r.split(':')[0]).join(', ')}${rawDataResults.length > 3 ? ` and ${rawDataResults.length - 3} more` : ''}. Now synthesizing insights.`,
    status: "success",
  });

  // Step 3: Generate narrative from transaction-level insights
  const narrativePrompt = GENERATE_NARRATIVE_PROMPT
    .replace("{userQuestion}", userQuery)
    .replace("{dataResults}", rawDataResults.join("\n"));

  const narrative = await callClaudeForText(narrativePrompt, "Generate narrative");

  // Step 4: Extract insights
  let insights: string[];
  try {
    insights = await callClaudeForJson<string[]>(
      EXTRACT_INSIGHTS_PROMPT.replace("{narrative}", narrative),
      "Extract insights"
    );
  } catch {
    insights = ["Analysis completed based on transaction-level data"];
  }

  await logAgentStep({
    sessionId,
    agentName: "Analyst",
    inputSummary: "Generating analysis",
    outputSummary: `Generated narrative with ${insights.length} insights from transaction data`,
    reasoningSummary: `Synthesized findings into a comprehensive narrative. Key insights: ${insights.slice(0, 2).join('; ')}${insights.length > 2 ? '...' : ''}. Sending results to Validator for quality check.`,
    status: "success",
  });

  // Generate SQL from the analysis plan
  const generatedSql = generateSqlFromPlan(plan);

  return {
    analystResult: {
      narrative: narrative.trim(),
      supportingKpiResults: supportingResults,
      insights,
    },
    generatedSql,
  };
}
