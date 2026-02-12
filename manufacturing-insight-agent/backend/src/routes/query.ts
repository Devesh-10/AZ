import { Router } from "express";
import { v4 as uuidv4 } from "uuid";
import { handleUserQuery } from "../orchestrator/AgentOrchestrator";
import { getSessionLogs } from "../core/telemetryStore";

export const queryRouter = Router();

queryRouter.post("/query", async (req, res) => {
  const { question } = req.body;
  // Handle both null and undefined sessionId
  const sessionId = req.body.sessionId || uuidv4();

  if (!question) {
    return res.status(400).json({ error: "Question is required" });
  }

  try {
    const result = await handleUserQuery(sessionId, question);

    // Get logs from telemetry store
    const logs = await getSessionLogs(sessionId);

    res.json({
      sessionId,
      ...result,
      agentLogs: logs,
      queries: result.generatedSql ? [result.generatedSql] : [],
    });
  } catch (error: any) {
    console.error("Query error:", error);
    res.status(500).json({ error: error.message || "Query failed" });
  }
});

// Get agent logs for a session (telemetry endpoint)
queryRouter.get("/telemetry/:sessionId", async (req, res) => {
  const { sessionId } = req.params;
  const logs = await getSessionLogs(sessionId);
  res.json(logs);
});
