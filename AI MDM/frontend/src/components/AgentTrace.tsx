import type { AgentStep } from "../api/chatApi";
import "./AgentTrace.css";

interface Props {
  steps: AgentStep[];
}

function summarizeArgs(args?: Record<string, unknown>): string {
  if (!args) return "";
  return Object.entries(args)
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(", ");
}

function summarizeResult(content: string): string {
  try {
    const parsed = JSON.parse(content);
    if (parsed.count !== undefined) return `${parsed.count} result(s)`;
    if (parsed.status) return parsed.status;
    if (parsed.error) return `error: ${parsed.error}`;
  } catch {
    /* not JSON */
  }
  return content.length > 80 ? content.slice(0, 80) + "..." : content;
}

export function AgentTrace({ steps }: Props) {
  const tooling = steps.filter((s) => s.type !== "ai_message");
  if (tooling.length === 0) return null;
  return (
    <details className="agent-trace">
      <summary>Agent reasoning ({tooling.length} steps)</summary>
      <ol>
        {tooling.map((step, i) => (
          <li key={i} className={`step step-${step.type}`}>
            {step.type === "tool_call" ? (
              <>
                <span className="badge">CALL</span>
                <code>{step.name}</code>
                <span className="args">{summarizeArgs(step.args)}</span>
              </>
            ) : (
              <>
                <span className="badge badge-result">RESULT</span>
                <code>{step.name}</code>
                <span className="args">{summarizeResult(step.content)}</span>
              </>
            )}
          </li>
        ))}
      </ol>
    </details>
  );
}
