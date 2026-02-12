import { KpiResult, AnalystResult, ValidationResult } from "../types";
import { callClaudeForText } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";

/**
 * Validator Agent
 *
 * Validates KPI results and analyst outputs to ensure quality responses.
 * Can generate follow-up questions when more information is needed.
 */

export async function validateKpiResults(
  sessionId: string,
  originalQuery: string,
  results: KpiResult[]
): Promise<ValidationResult> {
  const issues: string[] = [];

  // Check for empty results
  const emptyResults = results.filter((r) => r.dataPoints.length === 0);
  if (emptyResults.length > 0) {
    issues.push(
      `No data found for: ${emptyResults.map((r) => r.kpiName).join(", ")}`
    );
  }

  // Check for results with only one data point when breakdown was expected
  const singlePointResults = results.filter(
    (r) => r.breakdownBy && r.dataPoints.length === 1
  );
  if (singlePointResults.length > 0) {
    issues.push(
      `Limited breakdown data for: ${singlePointResults.map((r) => r.kpiName).join(", ")}`
    );
  }

  // Check for potential data quality issues (all zeros, negative values where unexpected)
  for (const result of results) {
    const allZeros = result.dataPoints.every((dp) => dp.value === 0);
    if (allZeros && result.dataPoints.length > 0) {
      issues.push(`All values are zero for ${result.kpiName} - this may indicate missing data`);
    }
  }

  const isValid = issues.length === 0;

  // Generate follow-up question if needed
  let followUpQuestion: string | undefined;
  if (!isValid && emptyResults.length === results.length) {
    followUpQuestion = await generateFollowUpQuestion(
      sessionId,
      originalQuery,
      issues
    );
  }

  const totalDataPoints = results.reduce((sum, r) => sum + r.dataPoints.length, 0);
  await logAgentStep({
    sessionId,
    agentName: "Validator",
    inputSummary: `Validating ${results.length} KPI results`,
    outputSummary: isValid
      ? "Validation passed"
      : `Found ${issues.length} issues: ${issues.join("; ")}`,
    reasoningSummary: isValid
      ? `Quality check passed. Verified ${results.length} result sets with ${totalDataPoints} total data points. No missing data or anomalies detected. Ready for visualization.`
      : `Quality issues detected: ${issues.join('. ')}. May need to refine the query or handle missing data gracefully.`,
    status: isValid ? "success" : "error",
  });

  return {
    isValid,
    issues,
    followUpQuestion,
  };
}

export async function validateAnalystResult(
  sessionId: string,
  originalQuery: string,
  result: AnalystResult
): Promise<ValidationResult> {
  const issues: string[] = [];

  // Check narrative quality
  if (!result.narrative || result.narrative.length < 50) {
    issues.push("Analysis narrative is too brief or missing");
  }

  // Check for supporting data
  if (result.supportingKpiResults.length === 0) {
    issues.push("No supporting KPI data for the analysis");
  }

  // Check all supporting results have data
  const emptySupporting = result.supportingKpiResults.filter(
    (r) => r.dataPoints.length === 0
  );
  if (emptySupporting.length > 0) {
    issues.push(
      `Missing data for: ${emptySupporting.map((r) => r.kpiName).join(", ")}`
    );
  }

  // Check for insights
  if (!result.insights || result.insights.length === 0) {
    issues.push("No insights generated from analysis");
  }

  const isValid = issues.length === 0;

  // Generate follow-up if analysis seems incomplete
  let followUpQuestion: string | undefined;
  if (!isValid && result.supportingKpiResults.length === 0) {
    followUpQuestion = await generateFollowUpQuestion(
      sessionId,
      originalQuery,
      issues
    );
  }

  await logAgentStep({
    sessionId,
    agentName: "Validator",
    inputSummary: "Validating analyst result",
    outputSummary: isValid
      ? "Validation passed"
      : `Found ${issues.length} issues`,
    reasoningSummary: isValid
      ? `Quality check passed. Narrative has ${result.narrative.length} chars, ${result.supportingKpiResults.length} supporting data sets, and ${result.insights.length} insights. Analysis is comprehensive and ready for presentation.`
      : `Quality issues in analyst output: ${issues.join('. ')}. The analysis may be incomplete.`,
    status: isValid ? "success" : "error",
  });

  return {
    isValid,
    issues,
    followUpQuestion,
  };
}

/**
 * Generate a helpful follow-up question when validation fails
 */
async function generateFollowUpQuestion(
  sessionId: string,
  originalQuery: string,
  issues: string[]
): Promise<string> {
  const prompt = `The user asked: "${originalQuery}"

However, we encountered these issues:
${issues.map((i) => `- ${i}`).join("\n")}

Generate a brief, helpful follow-up question to clarify what the user needs.
The question should help us get better data to answer their original question.
Keep it to 1-2 sentences.`;

  try {
    const followUp = await callClaudeForText(
      "You are a helpful assistant asking clarifying questions.",
      prompt
    );

    await logAgentStep({
      sessionId,
      agentName: "Validator",
      inputSummary: "Generating follow-up question",
      outputSummary: followUp.trim().substring(0, 100),
      status: "success",
    });

    return followUp.trim();
  } catch {
    return "Could you please clarify your question? I need more information to provide accurate KPI data.";
  }
}

/**
 * Quick validation check without LLM calls (for performance)
 */
export function quickValidate(results: KpiResult[]): boolean {
  // At least one result with data
  return results.some((r) => r.dataPoints.length > 0);
}
