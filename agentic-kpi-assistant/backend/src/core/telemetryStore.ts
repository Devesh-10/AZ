import { AgentLogEntry } from "../types";
import { v4 as uuidv4 } from "uuid";

/**
 * In-memory telemetry store (Option A - fastest for demo)
 *
 * Note: This store is not persistent across Lambda cold starts.
 * For production, switch to DynamoDB (Option B) by uncommenting
 * the DynamoDB implementation below.
 */

// In-memory store keyed by sessionId
const telemetryStore: Map<string, AgentLogEntry[]> = new Map();

/**
 * Log an agent step to the telemetry store
 */
export async function logAgentStep(
  entry: Omit<AgentLogEntry, "id" | "timestamp">
): Promise<AgentLogEntry> {
  const fullEntry: AgentLogEntry = {
    ...entry,
    id: uuidv4(),
    timestamp: new Date().toISOString(),
  };

  const sessionLogs = telemetryStore.get(entry.sessionId) || [];
  sessionLogs.push(fullEntry);
  telemetryStore.set(entry.sessionId, sessionLogs);

  console.log(`[Telemetry] ${fullEntry.agentName}: ${fullEntry.outputSummary}`);

  return fullEntry;
}

/**
 * Get all logs for a session
 */
export async function getSessionLogs(sessionId: string): Promise<AgentLogEntry[]> {
  return telemetryStore.get(sessionId) || [];
}

/**
 * Clear logs for a session (useful for testing)
 */
export async function clearSessionLogs(sessionId: string): Promise<void> {
  telemetryStore.delete(sessionId);
}

/**
 * Get all session IDs (useful for debugging)
 */
export function getAllSessionIds(): string[] {
  return Array.from(telemetryStore.keys());
}

/*
// ============================================================
// DynamoDB Implementation (Option B) - Uncomment if needed
// ============================================================

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  PutCommand,
  QueryCommand
} from "@aws-sdk/lib-dynamodb";

const TELEMETRY_TABLE = process.env.TELEMETRY_TABLE || "AgentTelemetry";
const ddbClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(ddbClient);

export async function logAgentStep(
  entry: Omit<AgentLogEntry, "id" | "timestamp">
): Promise<AgentLogEntry> {
  const fullEntry: AgentLogEntry = {
    ...entry,
    id: uuidv4(),
    timestamp: new Date().toISOString(),
  };

  await docClient.send(new PutCommand({
    TableName: TELEMETRY_TABLE,
    Item: fullEntry,
  }));

  return fullEntry;
}

export async function getSessionLogs(sessionId: string): Promise<AgentLogEntry[]> {
  const result = await docClient.send(new QueryCommand({
    TableName: TELEMETRY_TABLE,
    KeyConditionExpression: "sessionId = :sid",
    ExpressionAttributeValues: {
      ":sid": sessionId,
    },
    ScanIndexForward: true, // oldest first
  }));

  return (result.Items || []) as AgentLogEntry[];
}
*/
