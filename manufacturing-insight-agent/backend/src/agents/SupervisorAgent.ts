import { RoutingDecision } from "../types";
import { callClaudeForJson } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import { loadPrompt, injectVariables, PROMPTS } from "../prompts";
import * as fs from "fs";
import * as path from "path";

// Conversation history store per session
const conversationHistory: Map<string, { role: string; content: string }[]> = new Map();

export function addToConversationHistory(sessionId: string, role: string, content: string) {
  if (!conversationHistory.has(sessionId)) {
    conversationHistory.set(sessionId, []);
  }
  const history = conversationHistory.get(sessionId)!;
  history.push({ role, content });
  if (history.length > 10) {
    history.shift();
  }
}

export function getConversationHistory(sessionId: string): { role: string; content: string }[] {
  return conversationHistory.get(sessionId) || [];
}

/**
 * Load KPI catalogue from JSON file
 */
function loadKpiCatalogue(): string {
  try {
    // Try multiple paths for different environments
    const possiblePaths = [
      path.resolve(__dirname, "../../data/KPI/kpi_data_schemas.json"),
      path.resolve(__dirname, "../data/KPI/kpi_data_schemas.json"),
      path.resolve(process.cwd(), "data/KPI/kpi_data_schemas.json"),
      path.resolve(process.cwd(), "backend/data/KPI/kpi_data_schemas.json"),
    ];

    for (const kpiSchemaPath of possiblePaths) {
      if (fs.existsSync(kpiSchemaPath)) {
        const kpiSchema = fs.readFileSync(kpiSchemaPath, "utf8");
        console.log(`[SupervisorAgent] Loaded KPI schema from: ${kpiSchemaPath}`);
        return kpiSchema;
      }
    }

    console.warn("[SupervisorAgent] KPI schema file not found, using fallback");
    return getFallbackKpiSchema();
  } catch (error) {
    console.error("[SupervisorAgent] Failed to load KPI schema:", error);
    return getFallbackKpiSchema();
  }
}

/**
 * Fallback KPI schema if file not found
 */
function getFallbackKpiSchema(): string {
  return JSON.stringify({
    category: "kpi_data_products",
    tables: {
      KPI_STORE_MONTHLY: {
        record_count: 13,
        fields: [
          { field_name: "MONTH", data_type: "datetime64[ns]", description: "Calendar month (YYYY-MM)" },
          { field_name: "SITE_ID", data_type: "object", description: "Manufacturing site identifier" },
          { field_name: "PRODUCTION_VOLUME", data_type: "int64", description: "Total production volume" },
          { field_name: "BATCH_COUNT", data_type: "int64", description: "Number of batches" },
          { field_name: "BATCH_YIELD_AVG_PCT", data_type: "float64", description: "Average batch yield %" },
          { field_name: "RFT_PCT", data_type: "float64", description: "Right First Time %" },
          { field_name: "SCHEDULE_ADHERENCE_PCT", data_type: "float64", description: "Schedule adherence %" },
          { field_name: "AVG_CYCLE_TIME_HR", data_type: "float64", description: "Average cycle time (hours)" },
          { field_name: "DEVIATIONS_PER_100_BATCHES", data_type: "float64", description: "Deviation rate" },
          { field_name: "ALARMS_PER_1000_HOURS", data_type: "float64", description: "Alarm frequency" },
          { field_name: "LAB_TURNAROUND_MEDIAN_DAYS", data_type: "float64", description: "Lab TAT (days)" },
          { field_name: "SUPPLIER_OTIF_PCT", data_type: "float64", description: "Supplier OTIF %" },
          { field_name: "OEE_PACKAGING_PCT", data_type: "float64", description: "OEE Packaging %" },
          { field_name: "TARGET_RFT_PCT", data_type: "int64", description: "RFT target" },
          { field_name: "TARGET_OEE_PACKAGING_PCT", data_type: "int64", description: "OEE target" },
          { field_name: "RFT_RAG", data_type: "object", description: "RFT RAG status" },
          { field_name: "OEE_RAG", data_type: "object", description: "OEE RAG status" }
        ]
      },
      KPI_STORE_WEEKLY: {
        record_count: 52,
        fields: [
          { field_name: "ISO_WEEK", data_type: "int64", description: "ISO week number (1-52)" },
          { field_name: "SITE_ID", data_type: "object", description: "Manufacturing site identifier" },
          { field_name: "PRODUCTION_VOLUME", data_type: "int64", description: "Weekly production volume" },
          { field_name: "BATCH_COUNT", data_type: "int64", description: "Weekly batch count" },
          { field_name: "BATCH_YIELD_AVG_PCT", data_type: "float64", description: "Weekly average yield %" },
          { field_name: "RFT_PCT", data_type: "float64", description: "Weekly RFT %" },
          { field_name: "OEE_PACKAGING_PCT", data_type: "float64", description: "Weekly OEE %" },
          { field_name: "AVG_CYCLE_TIME_HR", data_type: "float64", description: "Weekly cycle time (hours)" },
          { field_name: "STOCKOUTS_COUNT", data_type: "int64", description: "Stockout events count" }
        ]
      }
    }
  }, null, 2);
}

/**
 * Build the system prompt with injected KPI catalogue
 * Uses external markdown prompt file for maintainability
 */
function buildSystemPrompt(): string {
  const kpiCatalogue = loadKpiCatalogue();

  // Try to load from external prompt file first
  const promptTemplate = loadPrompt(PROMPTS.SUPERVISOR);

  if (promptTemplate) {
    return injectVariables(promptTemplate, { KPI_CATALOGUE: kpiCatalogue });
  }

  // Fallback to inline prompt if file not found
  console.warn("[SupervisorAgent] Using fallback inline prompt");
  return getFallbackPrompt(kpiCatalogue);
}

/**
 * Fallback inline prompt if external file not found
 */
function getFallbackPrompt(kpiCatalogue: string): string {
  return `You are the Supervisor Agent for AstraZeneca's Manufacturing Insight Agent. Route user queries to the correct downstream agent.

## KPI Catalogue

\`\`\`json
${kpiCatalogue}
\`\`\`

## Field Aliases

| User Says | Maps To |
|-----------|---------|
| yield, batch yield | BATCH_YIELD_AVG_PCT |
| RFT, right first time | RFT_PCT |
| OEE, equipment effectiveness | OEE_PACKAGING_PCT |
| cycle time | AVG_CYCLE_TIME_HR |
| deviations | DEVIATIONS_PER_100_BATCHES |
| alarms | ALARMS_PER_1000_HOURS |
| production, volume | PRODUCTION_VOLUME |
| batches | BATCH_COUNT |
| schedule adherence | SCHEDULE_ADHERENCE_PCT |
| lab turnaround, TAT | LAB_TURNAROUND_MEDIAN_DAYS |
| supplier OTIF | SUPPLIER_OTIF_PCT |
| stockouts | STOCKOUTS_COUNT |

## Routing Rules

1. **Extract** from query: metric, time range, batch_id, filters
2. **Match** extracted metric against KPI_CATALOGUE.tables[*].fields[].field_name
3. **Route** based on:

| Match? | Query Type | Route |
|--------|------------|-------|
| Yes | Simple lookup (show, what is, get) | KPI_SIMPLE |
| Yes | Analysis (why, improve, root cause) | KPI_COMPLEX |
| No | Batch-level, equipment, deviations | KPI_COMPLEX |
| - | Not manufacturing related | REJECT |

## Output

Return ONLY valid JSON:
{
  "type": "KPI_SIMPLE" | "KPI_COMPLEX" | "REJECT",
  "reason": "brief explanation",
  "matched_field": "FIELD_NAME or null",
  "matched_table": "KPI_STORE_MONTHLY or KPI_STORE_WEEKLY or null"
}`;
}

// Cache the built prompt (KPI schema doesn't change at runtime)
let cachedSystemPrompt: string | null = null;

function getSystemPrompt(): string {
  if (!cachedSystemPrompt) {
    cachedSystemPrompt = buildSystemPrompt();
    console.log("[SupervisorAgent] System prompt built with KPI catalogue injection");
  }
  return cachedSystemPrompt;
}

// Extended routing decision with match info
interface ExtendedRoutingDecision {
  type: "KPI_SIMPLE" | "KPI_COMPLEX" | "REJECT";
  reason: string;
  matched_field?: string | null;
  matched_table?: string | null;
}

export async function classifyQuery(
  sessionId: string,
  userQuery: string
): Promise<RoutingDecision> {
  const history = getConversationHistory(sessionId);
  const lowerQuery = userQuery.toLowerCase().trim();

  // =========================================================================
  // FAST PATH: Pattern matching for instant routing (skip LLM)
  // =========================================================================

  // Time qualifier pattern (optional at the end of queries)
  const timeQualifier = `(\\s+(this|last|current|previous)\\s+(month|week|quarter|year))?`;

  // FAST: Batch ID detected
  const batchIdPattern = /\bB\d{4}-\d{5}\b/i;
  const hasBatchId = batchIdPattern.test(lowerQuery);

  // Check if this is a simple batch lookup (lead time, waiting time) - route to KPI_SIMPLE
  const isBatchLeadTimeQuery = hasBatchId && (
    /lead\s*time/i.test(lowerQuery) ||
    /waiting\s*time/i.test(lowerQuery) ||
    /wait\s*time/i.test(lowerQuery)
  );

  if (isBatchLeadTimeQuery) {
    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userQuery,
      outputSummary: "Classified as KPI_SIMPLE: Batch lead time lookup",
      reasoningSummary: "Fast path: Batch lead time query. Routing to KPI Gateway for direct lookup.",
      status: "success",
    });
    return { type: "KPI_SIMPLE", reason: "Batch lead time lookup - direct data retrieval" };
  }

  // Other batch queries → KPI_COMPLEX (needs analysis)
  if (hasBatchId) {
    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userQuery,
      outputSummary: "Classified as KPI_COMPLEX: Batch-level query",
      reasoningSummary: "Fast path: Batch ID detected. Requires analysis from transactional data.",
      status: "success",
    });
    return { type: "KPI_COMPLEX", reason: "Batch-level query requires transactional data analysis" };
  }

  // FAST: Waiting time / step timing (without batch ID) → KPI_COMPLEX
  if (/waiting\s*time/i.test(lowerQuery) || /step\s*(timing|duration)/i.test(lowerQuery)) {
    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userQuery,
      outputSummary: "Classified as KPI_COMPLEX: Step timing query",
      reasoningSummary: "Fast path: Step timing not in KPI tables. Requires MES_PASX_BATCH_STEPS.",
      status: "success",
    });
    return { type: "KPI_COMPLEX", reason: "Step timing requires transactional batch step data" };
  }

  // FAST: Simple metric requests → KPI_SIMPLE
  const simplePatterns = [
    // Direct metric questions - with optional time qualifier
    new RegExp(`^(show|what('?s| is| are)?|get|display|tell me)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?(current\\s*)?(overall\\s*)?(batch\\s*)?yield${timeQualifier}\\??$`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?oee${timeQualifier}`, 'i'),
    new RegExp(`^oee\\s*(performance|percentage|%|packaging)?${timeQualifier}\\??$`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?rft${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?right\\s*first\\s*time${timeQualifier}`, 'i'),
    new RegExp(`^right\\s*first\\s*time\\s*(rate|percentage|%)?${timeQualifier}\\??$`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?cycle\\s*time${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|how many)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?batch(es)?(\\s*count)?(\\s*status)?${timeQualifier}\\??$`, 'i'),
    /^batch\s*status/i,
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?production${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?deviation${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?schedule${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?stockout${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?|get)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?alarm${timeQualifier}`, 'i'),
    new RegExp(`^(show|get|what are)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?(all\\s*)?kpi${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?performance${timeQualifier}`, 'i'),
    new RegExp(`^(show|what('?s| is)?)?\\s*(me\\s*)?(the\\s*)?(our\\s*)?quality${timeQualifier}`, 'i'),
    new RegExp(`yield\\s*(pct|percent|percentage|%)?${timeQualifier}\\??$`, 'i'),
    new RegExp(`rft\\s*(pct|percent|percentage|%)?${timeQualifier}\\??$`, 'i'),
    // SKU-specific KPI queries
    /what\s+is\s+the\s+.*(lead\s*time|yield|oee|rft)\s+(for|of)\s+sku/i,
    /show\s+.*(lead\s*time|yield|oee|rft)\s+(for|of)\s+sku/i,
    /(formulation|lead\s*time)\s+(for|of)/i,
    /what\s+is\s+the\s+(batch\s+)?yield\s+for/i,
    /^how many/i,
    /^total\s*(batch|production|volume)/i,
    /lab\s*turnaround/i,
    /supplier\s*otif/i,
    /schedule\s*adherence/i,
  ];

  for (const pattern of simplePatterns) {
    if (pattern.test(lowerQuery)) {
      await logAgentStep({
        sessionId,
        agentName: "Supervisor",
        inputSummary: userQuery,
        outputSummary: "Classified as KPI_SIMPLE: Direct metric lookup",
        reasoningSummary: "Fast path: Pattern matched KPI field in catalogue. Routing to KPI Gateway.",
        status: "success",
      });
      return { type: "KPI_SIMPLE", reason: "Direct KPI metric lookup - field exists in KPI catalogue" };
    }
  }

  // FAST: Analysis/Why questions → KPI_COMPLEX
  const complexPatterns = [
    /\bwhy\s+(is|are|do|did|has|have|was|were)\b/i,
    /\bwhy\b.*\b(low|high|bad|poor|failing|rejected|issue)/i,
    /\bhow\s+(can|do|should|could|would)\s+(we|i|you)\b/i,
    /\bimprove\b/i,
    /\bfix\b/i,
    /\bcaus(e|es|ed|ing)\b/i,
    /\broot\s*cause/i,
    /\banalyze\b/i,
    /\banalysis\b/i,
    /\bexplain\b/i,
    /\binvestigat/i,
    /\brecommend/i,
    /\bwhat\s+should\b/i,
    /\bwhat\s+can\s+we\s+do\b/i,
    /\bunderperform/i,
    /\bproblem/i,
    /\bissue/i,
    /\bwhat('?s| is)\s+wrong/i,
    /\bwhat('?s| is)\s+causing/i,
    /equipment\s*(performance|breakdown|specific)/i,
  ];

  for (const pattern of complexPatterns) {
    if (pattern.test(lowerQuery)) {
      await logAgentStep({
        sessionId,
        agentName: "Supervisor",
        inputSummary: userQuery,
        outputSummary: "Classified as KPI_COMPLEX: Analysis required",
        reasoningSummary: "Fast path: Analysis/root cause query. Requires transactional data.",
        status: "success",
      });
      return { type: "KPI_COMPLEX", reason: "Analysis or root cause investigation required" };
    }
  }

  // FAST: Follow-up questions with conversation history → KPI_COMPLEX
  if (history.length > 0 && userQuery.length < 50) {
    const followUpPatterns = [
      /^(and|so|then|now|ok|okay|yes|yeah)/i,
      /^how\s+(do|can|should)/i,
      /^what\s+(should|can|do)/i,
      /improve/i,
      /fix/i,
    ];

    for (const pattern of followUpPatterns) {
      if (pattern.test(lowerQuery)) {
        await logAgentStep({
          sessionId,
          agentName: "Supervisor",
          inputSummary: userQuery,
          outputSummary: "Classified as KPI_COMPLEX: Follow-up question",
          reasoningSummary: "Follow-up detected in conversation. Routing to Analyst for contextual analysis.",
          status: "success",
        });
        return { type: "KPI_COMPLEX", reason: "Follow-up question requiring contextual analysis" };
      }
    }
  }

  // =========================================================================
  // SLOW PATH: Use LLM with KPI catalogue for ambiguous queries
  // =========================================================================

  let contextString = "";
  if (history.length > 0) {
    contextString = "\n\nConversation context:\n" + history.slice(-2).map(h =>
      `${h.role}: ${h.content.substring(0, 100)}`
    ).join("\n");
  }

  const userPrompt = `Classify this query: "${userQuery}"${contextString}

Instructions:
1. Check if requested metric exists in KPI_CATALOGUE.tables[*].fields[].field_name
2. Use Field Aliases to map user terms to field names
3. Route based on:
   - MATCH found + simple lookup → KPI_SIMPLE
   - MATCH found + analysis needed → KPI_COMPLEX
   - NO MATCH (batch-level, equipment) → KPI_COMPLEX
   - Not manufacturing related → REJECT`;

  try {
    const systemPrompt = getSystemPrompt();
    const result = await callClaudeForJson<ExtendedRoutingDecision>(systemPrompt, userPrompt);

    const matchInfo = result.matched_field
      ? ` (matched: ${result.matched_field} in ${result.matched_table})`
      : result.matched_field === null
      ? " (no KPI match)"
      : "";

    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userQuery,
      outputSummary: `Classified as ${result.type}: ${result.reason}${matchInfo}`,
      reasoningSummary: result.type === "KPI_SIMPLE"
        ? `Routing to KPI Gateway. Field found in KPI catalogue.`
        : result.type === "KPI_COMPLEX"
        ? "Routing to Analyst Agent. Requires transactional data or analysis."
        : "Query outside manufacturing scope.",
      status: "success",
    });

    // Return standard RoutingDecision
    return { type: result.type, reason: result.reason };
  } catch (error) {
    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userQuery,
      outputSummary: `LLM Error, using fallback: ${error}`,
      status: "success",
    });

    // Default to KPI_SIMPLE for faster response
    return { type: "KPI_SIMPLE", reason: "Default routing (fallback)" };
  }
}
