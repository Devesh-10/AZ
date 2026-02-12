import { v4 as uuidv4 } from "uuid";
import { ChatRequest, ChatResponse } from "./types";
import { handleUserQuery } from "./orchestrator/AgentOrchestrator";
import { getSessionLogs } from "./core/telemetryStore";
import { getManufacturingDataRepository } from "./dataAccess/ManufacturingDataRepository";
import knowledgeGraph from "./data/knowledgeGraph.json";

// Type definitions for Lambda-like events (for local testing)
interface APIGatewayProxyEvent {
  httpMethod: string;
  path: string;
  body?: string | null;
}

interface APIGatewayProxyResult {
  statusCode: number;
  headers: Record<string, string>;
  body: string;
}

/**
 * CORS headers for API responses
 */
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type,Authorization",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Content-Type": "application/json",
};

/**
 * Main Lambda handler
 */
export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  console.log("Received event:", JSON.stringify(event, null, 2));

  // Handle CORS preflight
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers: corsHeaders,
      body: "",
    };
  }

  const path = event.path;
  const method = event.httpMethod;

  try {
    // POST /api/chat/query - Main chat endpoint
    if (path === "/api/chat/query" && method === "POST") {
      return await handleChatQuery(event);
    }

    // GET /api/chat/telemetry/{sessionId} - Get telemetry logs
    if (path.startsWith("/api/chat/telemetry/") && method === "GET") {
      const sessionId = path.split("/").pop();
      if (!sessionId) {
        return errorResponse(400, "Session ID required");
      }
      return await handleGetTelemetry(sessionId);
    }

    // GET /api/meta/schema - Get available KPIs and dimensions
    if (path === "/api/meta/schema" && method === "GET") {
      return await handleGetSchema();
    }

    // GET /api/meta/knowledge-graph - Get knowledge graph
    if (path === "/api/meta/knowledge-graph" && method === "GET") {
      return handleGetKnowledgeGraph();
    }

    // GET /api/health - Health check
    if (path === "/api/health" && method === "GET") {
      return {
        statusCode: 200,
        headers: corsHeaders,
        body: JSON.stringify({ status: "healthy", timestamp: new Date().toISOString() }),
      };
    }

    return errorResponse(404, `Not found: ${method} ${path}`);
  } catch (error) {
    console.error("Handler error:", error);
    return errorResponse(500, `Internal server error: ${error}`);
  }
}

/**
 * Handle POST /api/chat/query
 */
async function handleChatQuery(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  if (!event.body) {
    return errorResponse(400, "Request body required");
  }

  let request: ChatRequest;
  try {
    request = JSON.parse(event.body);
  } catch {
    return errorResponse(400, "Invalid JSON body");
  }

  if (!request.message || typeof request.message !== "string") {
    return errorResponse(400, "Message field required");
  }

  // Generate or use provided session ID
  const sessionId = request.sessionId || uuidv4();

  console.log(`[Handler] Processing query for session ${sessionId}: ${request.message}`);

  // Process the query through the orchestrator
  const result = await handleUserQuery(sessionId, request.message);

  const response: ChatResponse = {
    sessionId,
    answer: result.answer,
    visualizationConfig: result.visualizationConfig,
    kpiResult: result.kpiResult,
    analystResult: result.analystResult,
    validationResult: result.validationResult,
    followUpQuestion: result.followUpQuestion,
    generatedSql: result.generatedSql,
  };

  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(response),
  };
}

/**
 * Handle GET /api/chat/telemetry/{sessionId}
 */
async function handleGetTelemetry(
  sessionId: string
): Promise<APIGatewayProxyResult> {
  const logs = await getSessionLogs(sessionId);

  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(logs),
  };
}

/**
 * Handle GET /api/meta/schema
 */
async function handleGetSchema(): Promise<APIGatewayProxyResult> {
  const repo = getManufacturingDataRepository();
  const summary = repo.getDataSummary();

  const schema = {
    kpis: summary.availableMetrics,
    dimensions: {
      sites: repo.getUniqueSiteIds(),
      months: repo.getUniqueMonths(),
    },
    tables: summary.tables,
  };

  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(schema),
  };
}

/**
 * Handle GET /api/meta/knowledge-graph
 */
function handleGetKnowledgeGraph(): APIGatewayProxyResult {
  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(knowledgeGraph),
  };
}

/**
 * Generate error response
 */
function errorResponse(
  statusCode: number,
  message: string
): APIGatewayProxyResult {
  return {
    statusCode,
    headers: corsHeaders,
    body: JSON.stringify({ error: message }),
  };
}
