import { useState, useRef, useEffect } from "react";
import {
  Send, ArrowLeft, Plus, Loader2, Paperclip, X,
  FlaskConical, Brain, Shield, Microscope, Cpu
} from "lucide-react";
import type { ChatMessage, TestRunResponse, AgentLogEntry } from "../types";
import { runTestStreaming, runTestWithDocument } from "../api/chatApi";
import BottomLineTable from "./BottomLineTable";
import "./ChatInterface.css";

const PLATFORM_INFO: Record<string, { name: string; icon: any; color: string }> = {
  "3dp": { name: "3DP - Drug Development", icon: FlaskConical, color: "#3b82f6" },
  "bikg": { name: "BIKG - Knowledge Graph", icon: Brain, color: "#8b5cf6" },
  "patient_safety": { name: "Patient Safety", icon: Shield, color: "#ef4444" },
  "clinical_trials": { name: "Clinical Trials", icon: Microscope, color: "#10b981" },
  "hpc_environment": { name: "HPC Environment", icon: Cpu, color: "#f97316" },
};

const SAMPLE_QUERIES: Record<string, string[]> = {
  "3dp": [
    "Test Module 3 substance validation pipeline",
    "Validate CTD batch formula schema compliance",
    "Test eCTD cross-reference integrity",
  ],
  "bikg": [
    "Validate gene-disease relationship queries",
    "Test ontology boundary cases for drug targets",
    "Verify knowledge graph ingestion pipeline",
  ],
  "patient_safety": [
    "Test adverse event reporting for Patient Safety",
    "Validate ICSR mandatory field requirements",
    "Test MedDRA coding accuracy for severity",
  ],
  "clinical_trials": [
    "Validate SDTM domain conformance for DM dataset",
    "Test ADaM derivation rules for ADSL",
    "Run Pinnacle 21 validation checks",
  ],
  "hpc_environment": [
    "Validate HPC job scheduling fairness across genomics workloads",
    "Test computational reproducibility for PKPD modelling pipelines",
    "Check metadata-scenario consistency for population PK batch runs",
  ],
};

interface Props {
  platform: string;
  sessionId: string | null;
  onSessionIdChange: (id: string) => void;
  onAgentLogs: (logs: AgentLogEntry[]) => void;
  onResponse: (resp: TestRunResponse) => void;
  onBackToPlatforms: () => void;
  onLogout: () => void;
}

export default function ChatInterface({
  platform, sessionId, onSessionIdChange, onAgentLogs, onResponse,
  onBackToPlatforms, onLogout,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const platformInfo = PLATFORM_INFO[platform] || { name: platform, icon: FlaskConical, color: "#7c3a5c" };
  const Icon = platformInfo.icon;
  const sampleQueries = SAMPLE_QUERIES[platform] || [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const query = text || input.trim();
    if (!query || isLoading) return;
    setInput("");

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Clear previous run's agent logs to show fresh pipeline
    onAgentLogs([]);

    try {
      let resp: TestRunResponse;

      if (attachedFile) {
        // File upload uses the non-streaming endpoint (multipart form)
        resp = await runTestWithDocument(platform, query, sessionId, attachedFile);
        onAgentLogs(resp.agentLogs || []);
      } else {
        // Use SSE streaming endpoint for real-time agent progress
        const streamingLogs: AgentLogEntry[] = [];
        resp = await runTestStreaming(platform, query, sessionId, (log: AgentLogEntry) => {
          streamingLogs.push(log);
          onAgentLogs([...streamingLogs]);
        });
      }

      setAttachedFile(null);

      if (resp.sessionId && !sessionId) {
        onSessionIdChange(resp.sessionId);
      }

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: resp.answer,
        timestamp: new Date(),
        testResults: resp.testResults,
        failureAnalyses: resp.failureAnalyses,
        refactorSuggestions: resp.refactorSuggestions,
        visualizationConfig: resp.visualizationConfig,
        complianceReport: resp.complianceReport,
        timingComparison: resp.timingComparison,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Set final complete agent logs
      onAgentLogs(resp.agentLogs || []);
      onResponse(resp);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${err.message || "Failed to run test pipeline"}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewTest = () => {
    setMessages([]);
    onAgentLogs([]);
    onResponse({
      sessionId: "", answer: "", platform, agentLogs: [],
    });
  };

  const formatContent = (content: string) => {
    let html = content;
    // Headers
    html = html.replace(/^### (.*$)/gm, '<h4 class="resp-h3">$1</h4>');
    html = html.replace(/^## (.*$)/gm, '<h3 class="resp-h2">$1</h3>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Lists
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="resp-list">$&</ul>');
    // Inline code
    html = html.replace(/`(.*?)`/g, '<code class="resp-code">$1</code>');
    // Tables
    html = html.replace(/\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)/g, (_m, header, body) => {
      const headers = header.split('|').filter((h: string) => h.trim()).map((h: string) => `<th>${h.trim()}</th>`).join('');
      const rows = body.trim().split('\n').map((row: string) => {
        const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => `<td>${c.trim()}</td>`).join('');
        return `<tr>${cells}</tr>`;
      }).join('');
      return `<table class="resp-table"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`;
    });
    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = `<p>${html}</p>`;
    return html;
  };

  return (
    <div className="chat-interface">
      <div className="ci-header">
        <div className="ci-header-left">
          <button className="ci-back" onClick={onBackToPlatforms}>
            <ArrowLeft size={16} />
          </button>
          <div className="ci-platform-badge" style={{ background: platformInfo.color }}>
            <Icon size={16} />
          </div>
          <span className="ci-platform-name">{platformInfo.name}</span>
        </div>
        <div className="ci-header-right">
          <button className="ci-btn" onClick={handleNewTest}>
            <Plus size={14} /> New Test
          </button>
        </div>
      </div>

      <div className="ci-messages">
        {messages.length === 0 ? (
          <div className="ci-welcome">
            <div className="welcome-icon" style={{ background: platformInfo.color }}>
              <Icon size={32} />
            </div>
            <h2>Test {platformInfo.name}</h2>
            <p>Describe what you want to test. The 7-step AI pipeline will handle requirements, test generation, execution, and compliance reporting.</p>

            <div className="welcome-queries">
              {sampleQueries.map((q, i) => (
                <button key={i} className="welcome-query" onClick={() => handleSend(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                {msg.role === "assistant" && (
                  <div className="msg-avatar" style={{ background: platformInfo.color }}>
                    <Icon size={16} />
                  </div>
                )}
                <div className="msg-body">
                  <div
                    className="msg-content"
                    dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                  />
                  {msg.timingComparison && (
                    <BottomLineTable timingComparison={msg.timingComparison} />
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message assistant">
                <div className="msg-avatar" style={{ background: platformInfo.color }}>
                  <Icon size={16} />
                </div>
                <div className="msg-body">
                  <div className="typing-indicator">
                    <span className="typing-text">
                      {attachedFile ? "Analyzing document & running pipeline" : "Running 7-step pipeline"}
                    </span>
                    <div className="typing-dots">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ci-input-area">
        <div className="ci-quick-chips">
          {!isLoading && messages.length > 0 && sampleQueries.slice(0, 2).map((q, i) => (
            <button key={i} className="quick-chip" onClick={() => handleSend(q)}>{q}</button>
          ))}
        </div>

        {attachedFile && (
          <div className="ci-file-chip">
            <Paperclip size={14} />
            <span className="file-chip-name">{attachedFile.name}</span>
            <button className="file-chip-remove" onClick={() => setAttachedFile(null)}>
              <X size={12} />
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.csv,.txt,.docx"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setAttachedFile(f);
            e.target.value = "";
          }}
        />

        <form className="ci-input-form" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
          <button
            type="button"
            className="upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            title="Upload requirements document (PDF, CSV, TXT, DOCX)"
          >
            <Paperclip size={18} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={attachedFile
              ? `Describe what to test from ${attachedFile.name}...`
              : `Describe what to test on ${platformInfo.name}...`
            }
            disabled={isLoading}
          />
          <button type="submit" disabled={!input.trim() || isLoading} className="send-btn">
            {isLoading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}
