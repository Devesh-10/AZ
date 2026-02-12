import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const BEDROCK_REGION = process.env.BEDROCK_REGION || "us-east-1";
// Use Claude Opus 4.5 (latest model)
const BEDROCK_MODEL_ID = process.env.BEDROCK_MODEL_ID || "us.anthropic.claude-opus-4-5-20251101-v1:0";
const USE_MOCK = process.env.USE_MOCK === "true";
const REQUEST_TIMEOUT_MS = 30000; // 30 second timeout

let client: BedrockRuntimeClient | null = null;

console.log(`[BedrockClient] Initializing with region: ${BEDROCK_REGION}, model: ${BEDROCK_MODEL_ID}, USE_MOCK: ${USE_MOCK}`);

try {
  if (!USE_MOCK) {
    client = new BedrockRuntimeClient({
      region: BEDROCK_REGION,
      requestHandler: {
        requestTimeout: REQUEST_TIMEOUT_MS,
        httpsAgent: { timeout: REQUEST_TIMEOUT_MS }
      } as any
    });
    console.log("[BedrockClient] AWS Bedrock client initialized successfully");
  } else {
    console.log("[BedrockClient] Running in MOCK mode");
  }
} catch (e) {
  console.warn("[BedrockClient] Could not initialize AWS client, using mock mode:", e);
}

interface ClaudeMessage {
  role: "user" | "assistant";
  content: string;
}

interface ClaudeRequest {
  anthropic_version: string;
  max_tokens: number;
  system?: string;
  messages: ClaudeMessage[];
}

interface ClaudeResponse {
  content: { type: string; text: string }[];
  stop_reason: string;
}

/**
 * Mock responses for local development without AWS credentials
 */
function getMockJsonResponse(systemPrompt: string, userPrompt: string): any {
  const query = userPrompt.toLowerCase();

  // Routing/classification mock
  if (systemPrompt.includes("Supervisor") || systemPrompt.includes("classify")) {
    if (query.includes("energy") || query.includes("emission") || query.includes("water") ||
        query.includes("waste") || query.includes("ev") || query.includes("fleet") ||
        query.includes("carbon") || query.includes("ghg")) {
      return { type: "KPI_SIMPLE", reason: "Question about sustainability metrics" };
    }
    if (query.includes("why") || query.includes("trend") || query.includes("analysis")) {
      return { type: "KPI_COMPLEX", reason: "Question requires deeper analysis" };
    }
    return { type: "KPI_SIMPLE", reason: "General sustainability question" };
  }

  // Intent parsing mock
  if (systemPrompt.includes("parser") || systemPrompt.includes("Parse")) {
    if (query.includes("energy")) {
      return { dataType: "energy", year: null, quarter: null, month: null, siteName: null, groupBy: null };
    }
    if (query.includes("emission") || query.includes("ghg") || query.includes("carbon")) {
      return { dataType: "ghg_emissions", year: null, quarter: null, month: null, siteName: null, scope: null, groupBy: query.includes("site") ? "site" : null };
    }
    if (query.includes("water")) {
      return { dataType: "water", year: query.includes("2024") ? 2024 : null, quarter: null, month: null, siteName: null, groupBy: null };
    }
    if (query.includes("waste")) {
      return { dataType: "waste", year: null, quarter: null, month: null, siteName: null, groupBy: query.includes("quarter") ? "quarter" : null };
    }
    if (query.includes("ev") || query.includes("electric") || query.includes("fleet")) {
      return { dataType: "ev_transition", year: null, quarter: null };
    }
    return { dataType: "energy", year: null, quarter: null, month: null, siteName: null, groupBy: null };
  }

  // Visualization mock
  if (systemPrompt.includes("visualization") || systemPrompt.includes("chart")) {
    return {
      chartType: "bar",
      title: "Sustainability Metrics",
      xLabel: "Category",
      yLabel: "Value",
      series: []
    };
  }

  // Default
  return { type: "KPI_SIMPLE", reason: "Default response" };
}

function getMockTextResponse(systemPrompt: string, userPrompt: string): string {
  if (systemPrompt.includes("analyst") || systemPrompt.includes("explanation")) {
    return "Based on the data, the sustainability metrics show positive progress towards environmental targets. The values indicate ongoing efforts to reduce environmental impact across operations.";
  }
  return "Analysis of the requested sustainability data shows the current operational metrics.";
}

/**
 * Call Claude via Bedrock and expect a JSON response
 */
export async function callClaudeForJson<T>(
  systemPrompt: string,
  userPrompt: string
): Promise<T> {
  // Use mock in local development
  if (USE_MOCK || !client) {
    console.log("[BedrockClient] Using mock response (set USE_MOCK=false and configure AWS credentials for real API)");
    return getMockJsonResponse(systemPrompt, userPrompt) as T;
  }

  const request: ClaudeRequest = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 4096,
    system: systemPrompt,
    messages: [
      {
        role: "user",
        content: userPrompt,
      },
    ],
  };

  const command = new InvokeModelCommand({
    modelId: BEDROCK_MODEL_ID,
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify(request),
  });

  try {
    console.log(`[BedrockClient] Sending JSON request to Bedrock (${userPrompt.substring(0, 50)}...)`);
    const startTime = Date.now();

    // Add timeout wrapper
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error(`Bedrock request timed out after ${REQUEST_TIMEOUT_MS}ms`)), REQUEST_TIMEOUT_MS);
    });

    const response = await Promise.race([client.send(command), timeoutPromise]);
    const elapsed = Date.now() - startTime;
    console.log(`[BedrockClient] Response received in ${elapsed}ms`);

    const responseBody = JSON.parse(
      new TextDecoder().decode(response.body)
    ) as ClaudeResponse;

    const text = responseBody.content[0]?.text || "";
    console.log(`[BedrockClient] Response text length: ${text.length}`);

    // Extract JSON from the response (handle markdown code blocks)
    let jsonStr = text;
    const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) {
      jsonStr = jsonMatch[1].trim();
    } else {
      // Try to find JSON object or array directly
      const objectMatch = text.match(/\{[\s\S]*\}/);
      const arrayMatch = text.match(/\[[\s\S]*\]/);
      if (objectMatch) {
        jsonStr = objectMatch[0];
      } else if (arrayMatch) {
        jsonStr = arrayMatch[0];
      }
    }

    // Sanitize control characters that can break JSON parsing
    // Replace all control characters (except valid JSON whitespace: \t, \n, \r) with spaces
    jsonStr = jsonStr.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, ' ');

    return JSON.parse(jsonStr) as T;
  } catch (error: any) {
    console.error("[BedrockClient] Error calling Claude for JSON:", error?.message || error);
    console.error("[BedrockClient] Error details:", JSON.stringify(error, null, 2));
    // Fall back to mock on error
    console.log("[BedrockClient] Falling back to mock response due to error");
    return getMockJsonResponse(systemPrompt, userPrompt) as T;
  }
}

/**
 * Call Claude via Bedrock and expect a text response
 */
export async function callClaudeForText(
  systemPrompt: string,
  userPrompt: string
): Promise<string> {
  // Use mock in local development
  if (USE_MOCK || !client) {
    console.log("[BedrockClient] Using mock text response");
    return getMockTextResponse(systemPrompt, userPrompt);
  }

  const request: ClaudeRequest = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 4096,
    system: systemPrompt,
    messages: [
      {
        role: "user",
        content: userPrompt,
      },
    ],
  };

  const command = new InvokeModelCommand({
    modelId: BEDROCK_MODEL_ID,
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify(request),
  });

  try {
    console.log(`[BedrockClient] Sending text request to Bedrock (${userPrompt.substring(0, 50)}...)`);
    const startTime = Date.now();

    // Add timeout wrapper
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error(`Bedrock request timed out after ${REQUEST_TIMEOUT_MS}ms`)), REQUEST_TIMEOUT_MS);
    });

    const response = await Promise.race([client.send(command), timeoutPromise]);
    const elapsed = Date.now() - startTime;
    console.log(`[BedrockClient] Text response received in ${elapsed}ms`);

    const responseBody = JSON.parse(
      new TextDecoder().decode(response.body)
    ) as ClaudeResponse;

    return responseBody.content[0]?.text || "";
  } catch (error: any) {
    console.error("[BedrockClient] Error calling Claude for text:", error?.message || error);
    console.error("[BedrockClient] Error details:", JSON.stringify(error, null, 2));
    return getMockTextResponse(systemPrompt, userPrompt);
  }
}

/**
 * Call Claude with conversation history
 */
export async function callClaudeWithHistory(
  systemPrompt: string,
  messages: ClaudeMessage[]
): Promise<string> {
  if (USE_MOCK || !client) {
    return getMockTextResponse(systemPrompt, messages[messages.length - 1]?.content || "");
  }

  const request: ClaudeRequest = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 4096,
    system: systemPrompt,
    messages,
  };

  const command = new InvokeModelCommand({
    modelId: BEDROCK_MODEL_ID,
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify(request),
  });

  try {
    const response = await client.send(command);
    const responseBody = JSON.parse(
      new TextDecoder().decode(response.body)
    ) as ClaudeResponse;

    return responseBody.content[0]?.text || "";
  } catch (error) {
    console.error("Error calling Claude with history:", error);
    return getMockTextResponse(systemPrompt, messages[messages.length - 1]?.content || "");
  }
}
