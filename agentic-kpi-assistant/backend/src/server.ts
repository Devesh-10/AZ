/**
 * Local development server for the KPI Assistant backend
 * Run with: npx ts-node src/server.ts
 */

import express, { Request, Response } from "express";
import cors from "cors";
import { v4 as uuidv4 } from "uuid";
import { ChatRequest, ChatResponse } from "./types";
import { handleUserQuery } from "./orchestrator/AgentOrchestrator";
import { getSessionLogs } from "./core/telemetryStore";
import { getSustainabilityDataRepository } from "./dataAccess/SustainabilityDataRepository";
import knowledgeGraph from "./data/knowledgeGraph.json";

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Request logging
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Health check
app.get("/api/health", (req: Request, res: Response) => {
  res.json({ status: "healthy", timestamp: new Date().toISOString() });
});

// Main chat endpoint
app.post("/api/chat/query", async (req: Request, res: Response) => {
  try {
    const request: ChatRequest = req.body;

    if (!request.message || typeof request.message !== "string") {
      return res.status(400).json({ error: "Message field required" });
    }

    const sessionId = request.sessionId || uuidv4();
    console.log(`[Server] Processing query for session ${sessionId}: ${request.message}`);

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

    res.json(response);
  } catch (error) {
    console.error("[Server] Error processing query:", error);
    res.status(500).json({ error: `Internal server error: ${error}` });
  }
});

// Get telemetry logs
app.get("/api/chat/telemetry/:sessionId", async (req: Request, res: Response) => {
  try {
    const sessionId = req.params.sessionId as string;
    const logs = await getSessionLogs(sessionId);
    res.json(logs);
  } catch (error) {
    console.error("[Server] Error fetching telemetry:", error);
    res.status(500).json({ error: `Internal server error: ${error}` });
  }
});

// Get schema/metadata
app.get("/api/meta/schema", (req: Request, res: Response) => {
  const repo = getSustainabilityDataRepository();
  const summary = repo.getDataSummary();

  res.json({
    kpis: summary.availableMetrics,
    dimensions: {
      sites: repo.getAvailableSites().slice(0, 10),
      years: repo.getAvailableYears(),
    },
    tables: summary.tables,
  });
});

// Get knowledge graph
app.get("/api/meta/knowledge-graph", (req: Request, res: Response) => {
  res.json(knowledgeGraph);
});

// Export app for Lambda
export default app;

// Start server only when run directly (not imported)
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║  Sustainability KPI Assistant Backend                     ║
║  Running on http://localhost:${PORT}                         ║
╚═══════════════════════════════════════════════════════════╝

Available endpoints:
  GET  /api/health              - Health check
  POST /api/chat/query          - Send a query
  GET  /api/chat/telemetry/:id  - Get session telemetry
  GET  /api/meta/schema         - Get data schema
  GET  /api/meta/knowledge-graph - Get knowledge graph
`);

    // Initialize data repository on startup
    const repo = getSustainabilityDataRepository();
    const summary = repo.getDataSummary();
    console.log(`Loaded ${summary.tables.length} data tables with ${summary.availableMetrics.length} metrics\n`);
  });
}
