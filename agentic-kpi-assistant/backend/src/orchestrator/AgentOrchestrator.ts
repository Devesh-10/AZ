import { OrchestratorResponse, KpiResult, AnalystResult } from "../types";
import { callClaudeForText } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import {
  classifyQuery,
  parseAndFetchKpi,
  analyzeComplexQuery,
  validateKpiResults,
  validateAnalystResult,
  generateVisualization,
} from "../agents";
import { KpiGatewayResult } from "../agents/KpiGatewayAgent";
import { AnalystAgentResult } from "../agents/AnalystAgent";

/**
 * Agent Orchestrator
 *
 * Coordinates the flow between agents based on query classification.
 *
 * Flow:
 * 1. Supervisor classifies query
 * 2. Route to appropriate agent (KPI Gateway or Analyst)
 * 3. Validator checks results
 * 4. Visualization generates charts
 * 5. Final answer is synthesized
 */

export async function handleUserQuery(
  sessionId: string,
  userMessage: string
): Promise<OrchestratorResponse> {
  console.log(`[Orchestrator] Processing query for session ${sessionId}`);

  // Step 1: Classify the query
  const routing = await classifyQuery(sessionId, userMessage);

  // Handle rejection
  if (routing.type === "REJECT") {
    await logAgentStep({
      sessionId,
      agentName: "Supervisor",
      inputSummary: userMessage,
      outputSummary: `Query rejected: ${routing.reason}`,
      status: "success",
    });

    return {
      answer: `I'm sorry, but I can only help with KPI and business metrics questions. ${routing.reason}`,
    };
  }

  let kpiResult: KpiResult[] | undefined;
  let analystResult: AnalystResult | undefined;
  let generatedSql: string | undefined;

  // Step 2: Route to appropriate agent
  if (routing.type === "KPI_SIMPLE") {
    // Simple KPI queries go through KPI Gateway
    try {
      const gatewayResult: KpiGatewayResult = await parseAndFetchKpi(sessionId, userMessage);
      kpiResult = gatewayResult.kpiResults;
      generatedSql = gatewayResult.generatedSql;
    } catch (error) {
      console.error("[Orchestrator] KPI Gateway error:", error);
      return {
        answer: "I encountered an error while fetching the KPI data. Please try rephrasing your question.",
      };
    }
  } else if (routing.type === "KPI_COMPLEX") {
    // Complex queries go through Analyst
    try {
      const analystAgentResult: AnalystAgentResult = await analyzeComplexQuery(sessionId, userMessage);
      analystResult = analystAgentResult.analystResult;
      generatedSql = analystAgentResult.generatedSql;
      kpiResult = analystResult.supportingKpiResults;
    } catch (error) {
      console.error("[Orchestrator] Analyst error:", error);
      return {
        answer: "I encountered an error while analyzing your question. Please try a simpler query or rephrase.",
      };
    }
  }

  // Step 3: Validate results
  let validationResult;
  if (analystResult) {
    validationResult = await validateAnalystResult(sessionId, userMessage, analystResult);
  } else if (kpiResult) {
    validationResult = await validateKpiResults(sessionId, userMessage, kpiResult);
  }

  // If validation failed with a follow-up question, return it
  if (validationResult && !validationResult.isValid && validationResult.followUpQuestion) {
    return {
      answer: validationResult.followUpQuestion,
      validationResult,
      followUpQuestion: validationResult.followUpQuestion,
    };
  }

  // Step 4: Generate visualization
  const visualizationConfig = await generateVisualization(
    sessionId,
    kpiResult,
    analystResult
  );

  // Step 5: Generate final answer
  const answer = await generateFinalAnswer(
    sessionId,
    userMessage,
    kpiResult,
    analystResult,
    validationResult?.issues
  );

  return {
    answer,
    kpiResult,
    analystResult,
    validationResult,
    visualizationConfig,
    generatedSql,
  };
}

/**
 * Truncate text to approximately word limit while keeping complete sentences
 */
function truncateToWordLimit(text: string, wordLimit: number = 100): string {
  const words = text.split(/\s+/);
  if (words.length <= wordLimit) {
    return text;
  }

  // Find a good break point near the word limit
  const truncated = words.slice(0, wordLimit).join(' ');

  // Try to end at a sentence boundary
  const lastPeriod = truncated.lastIndexOf('.');
  const lastExclaim = truncated.lastIndexOf('!');
  const lastQuestion = truncated.lastIndexOf('?');
  const lastBoundary = Math.max(lastPeriod, lastExclaim, lastQuestion);

  if (lastBoundary > truncated.length * 0.5) {
    return truncated.substring(0, lastBoundary + 1);
  }

  return truncated + '...';
}

/**
 * Generate a natural language answer summarizing the results
 */
async function generateFinalAnswer(
  sessionId: string,
  userQuestion: string,
  kpiResult?: KpiResult[],
  analystResult?: AnalystResult,
  validationIssues?: string[]
): Promise<string> {
  let answer: string;

  // If we have an analyst narrative, use it
  if (analystResult?.narrative) {
    answer = analystResult.narrative;

    // Add insights as bullet points (limit to top 3)
    if (analystResult.insights && analystResult.insights.length > 0) {
      const topInsights = analystResult.insights.slice(0, 3);
      answer += "\n\n**Key Insights:**\n";
      // Strip any leading bullet characters from insights to avoid double bullets
      answer += topInsights.map((i) => {
        const cleaned = i.replace(/^[•\-\*]\s*/, '').trim();
        return `• ${cleaned}`;
      }).join("\n");
    }

    return truncateToWordLimit(answer, 100);
  }

  // For simple KPI results, generate a summary WITHOUT extra LLM call for speed
  if (kpiResult && kpiResult.length > 0) {
    // Use explanation from KPI result directly (already contains summary)
    const explanations = kpiResult
      .filter((r) => r.explanation)
      .map((r) => r.explanation)
      .join(" ");

    if (explanations) {
      await logAgentStep({
        sessionId,
        agentName: "Supervisor",
        inputSummary: "Generating final answer",
        outputSummary: "Answer generated from KPI data",
        status: "success",
      });
      return truncateToWordLimit(explanations, 100);
    }

    // Fallback: build a simple answer from data points
    const dataContext = kpiResult
      .map((r) => {
        const points = r.dataPoints
          .map((dp) => `**${dp.label}**: ${dp.value.toLocaleString()}`)
          .join(", ");
        return `${r.kpiName.replace(/_/g, ' ')}: ${points}`;
      })
      .join(". ");

    return truncateToWordLimit(`Based on the KPI data, ${dataContext}.`, 100);
  }

  return "I couldn't find relevant data to answer your question. Please try a different query.";
}
