import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const BEDROCK_REGION = process.env.BEDROCK_REGION || "us-east-1";
const BEDROCK_MODEL_ID = process.env.BEDROCK_MODEL_ID || "us.anthropic.claude-sonnet-4-20250514-v1:0";

let client: BedrockRuntimeClient | null = null;

console.log(`[BedrockClient] Initializing with region: ${BEDROCK_REGION}, model: ${BEDROCK_MODEL_ID}`);

try {
  client = new BedrockRuntimeClient({
    region: BEDROCK_REGION,
  });
  console.log("[BedrockClient] AWS Bedrock client initialized successfully");
} catch (e) {
  console.warn("[BedrockClient] Could not initialize AWS client:", e);
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

export async function callClaude(
  systemPrompt: string,
  userMessage: string,
  maxTokens: number = 4096
): Promise<string> {
  if (!client) {
    throw new Error("Bedrock client not initialized");
  }

  const request: ClaudeRequest = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: maxTokens,
    system: systemPrompt,
    messages: [
      {
        role: "user",
        content: userMessage,
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
    console.log(`[BedrockClient] Sending request (${userMessage.substring(0, 50)}...)`);
    const startTime = Date.now();

    const response = await client.send(command);
    const elapsed = Date.now() - startTime;
    console.log(`[BedrockClient] Response received in ${elapsed}ms`);

    const responseBody = JSON.parse(
      new TextDecoder().decode(response.body)
    ) as ClaudeResponse;

    return responseBody.content[0]?.text || "";
  } catch (error: any) {
    console.error("[BedrockClient] Error calling Claude:", error?.message || error);
    throw error;
  }
}

export async function callClaudeForJson<T>(
  systemPrompt: string,
  userPrompt: string
): Promise<T> {
  const text = await callClaude(systemPrompt, userPrompt);

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

  return JSON.parse(jsonStr) as T;
}
