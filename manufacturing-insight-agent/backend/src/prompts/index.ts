/**
 * Agent Prompt Loader for Manufacturing Insight Agent
 *
 * Loads agent definitions from markdown files and injects dynamic data.
 * The markdown files serve as the "source of truth" for agent behavior.
 */

import * as fs from "fs";
import * as path from "path";

// Cache for loaded agent prompts
const agentCache: Map<string, string> = new Map();

/**
 * Available agents (markdown files in /agents directory)
 */
export const AGENTS = {
  SUPERVISOR: "SupervisorAgent",
  KPI_GATEWAY: "KpiGatewayAgent",
  ANALYST: "AnalystAgent",
  VALIDATOR: "ValidatorAgent",
  VISUALIZATION: "VisualizationAgent",
} as const;

export type AgentName = (typeof AGENTS)[keyof typeof AGENTS];

/**
 * Load an agent's prompt from its markdown file
 */
export function loadAgentPrompt(agentName: string): string {
  // Check cache first
  if (agentCache.has(agentName)) {
    return agentCache.get(agentName)!;
  }

  // Try multiple paths for different environments
  const possiblePaths = [
    // Development: src/agents/
    path.resolve(__dirname, `../agents/${agentName}.md`),
    // Production: dist/agents/
    path.resolve(__dirname, `../../agents/${agentName}.md`),
    // Alternative paths
    path.resolve(process.cwd(), `src/agents/${agentName}.md`),
    path.resolve(process.cwd(), `dist/agents/${agentName}.md`),
  ];

  for (const agentPath of possiblePaths) {
    if (fs.existsSync(agentPath)) {
      const content = fs.readFileSync(agentPath, "utf8");
      agentCache.set(agentName, content);
      console.log(`[AgentLoader] Loaded agent: ${agentName} from ${agentPath}`);
      return content;
    }
  }

  console.warn(`[AgentLoader] Agent markdown not found: ${agentName}`);
  return "";
}

/**
 * Inject variables into an agent prompt template
 *
 * Variables use {{VARIABLE_NAME}} syntax
 */
export function injectVariables(
  template: string,
  variables: Record<string, string | number | object>
): string {
  let result = template;

  for (const [key, value] of Object.entries(variables)) {
    const placeholder = `{{${key}}}`;
    const stringValue =
      typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
    // Escape special regex characters in placeholder
    const escapedPlaceholder = placeholder.replace(/[{}]/g, '\\$&');
    result = result.replace(new RegExp(escapedPlaceholder, "g"), stringValue);
  }

  return result;
}

/**
 * Load agent and inject variables in one step
 */
export function getAgentPrompt(
  agentName: string,
  variables?: Record<string, string | number | object>
): string {
  const template = loadAgentPrompt(agentName);
  if (!variables) return template;
  return injectVariables(template, variables);
}

/**
 * Extract a specific section from an agent markdown file
 *
 * Sections are delimited by ## headers
 */
export function extractSection(agentPrompt: string, sectionName: string): string {
  const regex = new RegExp(`## ${sectionName}\\s*\\n([\\s\\S]*?)(?=\\n## |$)`, "i");
  const match = agentPrompt.match(regex);
  return match ? match[1].trim() : "";
}

/**
 * Parse the output format section to get expected JSON structure
 */
export function getExpectedOutputFormat(agentPrompt: string): object | null {
  const section = extractSection(agentPrompt, "Output Format");
  const jsonMatch = section.match(/```json\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[1]);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Clear agent cache (useful for development/testing)
 */
export function clearAgentCache(): void {
  agentCache.clear();
}

/**
 * Get all loaded agents (for debugging)
 */
export function getLoadedAgents(): string[] {
  return Array.from(agentCache.keys());
}

// Legacy exports for backward compatibility with existing code
export const PROMPTS = AGENTS;
export const loadPrompt = loadAgentPrompt;
export const getPrompt = getAgentPrompt;
export function clearPromptCache(): void {
  clearAgentCache();
}
