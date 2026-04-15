import React, { useState } from "react";
import "./DataSourcePanel.css";

interface DataSourcePanelProps {
  onConnect: (source: {
    type: string;
    name: string;
    assets: number;
    rules: number;
  }) => void;
}

type ConnectionState = "idle" | "pick-source" | "pick-schema" | "connecting" | "success" | "error";

const API_BASE =
  import.meta.env.VITE_API_GATEWAY_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8001";

const DataSourcePanel: React.FC<DataSourcePanelProps> = ({ onConnect }) => {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("idle");
  const [connectingSource, setConnectingSource] = useState("");
  const [selectedSchema, setSelectedSchema] = useState("MANUFACTURING");
  const [errorMessage, setErrorMessage] = useState("");

  const handleLaunchDQ = () => {
    setConnectionState("pick-source");
  };

  const handlePickSource = async (sourceName: string) => {
    setConnectionState("connecting");
    setConnectingSource(sourceName);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_BASE}/api/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "demo" }),
      });

      const data = await response.json();
      setConnectionState("success");

      setTimeout(() => {
        onConnect({
          type: data.type || "demo",
          name: sourceName,
          assets: data.assets || 14,
          rules: data.rules || 15,
        });
      }, 1000);
    } catch {
      setConnectionState("error");
      setErrorMessage("Connection failed. Please try again.");
    }
  };

  return (
    <div className="mesh-page">
      {/* Ambient background */}
      <div className="mesh-bg">
        <div className="mesh-glow mesh-glow-1" />
        <div className="mesh-glow mesh-glow-2" />
        <div className="mesh-glow mesh-glow-3" />
        <div className="mesh-grid" />
      </div>

      <div className="mesh-content">
        {/* Top bar */}
        <header className="mesh-topbar">
          <div className="mesh-brand">
            <div className="mesh-logo">
              <svg viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="1.2" opacity="0.5" />
                <path d="M8 16C8 11.58 11.58 8 16 8C20.42 8 24 11.58 24 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <path d="M24 16C24 20.42 20.42 24 16 24C11.58 24 8 20.42 8 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
                <circle cx="16" cy="16" r="2.5" fill="currentColor" />
              </svg>
            </div>
            <span className="mesh-brand-name">AstraZeneca</span>
            <span className="mesh-brand-sep" />
            <span className="mesh-brand-sub">Enterprise Data Office</span>
          </div>
        </header>

        {/* Hero */}
        <section className="mesh-hero">
          <h1 className="mesh-title">
            Enterprise Data <span className="mesh-accent">Office Automation</span>
          </h1>
          <p className="mesh-subtitle">
            An <strong>intelligence layer</strong> that sits on top of your existing stack —
            SAP MDG, Informatica, Collibra, Snowflake, AWS.{" "}
            <strong>We don't replace anything. We make everything smarter.</strong>
          </p>
        </section>

        {/* Process flow bar */}
        <div className="mesh-flow-bar">
          <div className="mesh-flow-track">
            <div className="mesh-flow-step mesh-flow-gov">Data Governance</div>
            <div className="mesh-flow-arrow" />
            <div className="mesh-flow-step mesh-flow-dq">Data Quality Assurance</div>
            <div className="mesh-flow-arrow" />
            <div className="mesh-flow-step mesh-flow-dm">Data Management</div>
            <div className="mesh-flow-arrow" />
            <div className="mesh-flow-step mesh-flow-dc">Data Consumption — AI / Analytics</div>
          </div>
        </div>

        {/* Enterprise Orchestration Layer */}
        <div className="mesh-orch-layer">
          <div className="mesh-layer-label">ENTERPRISE ORCHESTRATION LAYER</div>
          <div className="mesh-orch-node">
            <div className="mesh-orch-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
              </svg>
            </div>
            <span>Enterprise Orchestration Layer</span>
          </div>
          {/* Connection lines */}
          <div className="mesh-orch-lines">
            <div className="mesh-line mesh-line-1" />
            <div className="mesh-line mesh-line-2" />
            <div className="mesh-line mesh-line-3" />
            <div className="mesh-line mesh-line-4" />
          </div>
        </div>

        {/* Domain Orchestrators */}
        <div className="mesh-layer-label mesh-domain-label">DOMAIN ORCHESTRATORS</div>

        <div className="mesh-domains">
          {/* Data Governance */}
          <div className="mesh-domain mesh-domain-gov">
            <div className="mesh-domain-header">
              <div className="mesh-domain-icon mesh-icon-gov">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
              </div>
              <div className="mesh-domain-info">
                <h3>Governance</h3>
                <span className="mesh-domain-role">ORCHESTRATOR</span>
              </div>
              <span className="mesh-badge mesh-badge-soon">Coming Soon</span>
            </div>
            <div className="mesh-agents">
              <div className="mesh-agent">Policy</div>
              <div className="mesh-agent">Metadata Discovery</div>
              <div className="mesh-agent">Lineage</div>
              <div className="mesh-agent">Observability</div>
              <div className="mesh-agent">PII / GxP Classification</div>
            </div>
          </div>

          {/* Data Quality — LIVE */}
          <button
            className="mesh-domain mesh-domain-dq mesh-domain-live"
            onClick={handleLaunchDQ}
          >
            <div className="mesh-domain-header">
              <div className="mesh-domain-icon mesh-icon-dq">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <div className="mesh-domain-info">
                <h3>Data Quality</h3>
                <span className="mesh-domain-role">ORCHESTRATOR</span>
              </div>
              <span className="mesh-badge mesh-badge-live">
                <span className="mesh-badge-dot" />
                Live
              </span>
            </div>
            <div className="mesh-agents">
              <div className="mesh-agent mesh-agent-live">Data Discovery</div>
              <div className="mesh-agent mesh-agent-live">Profiling</div>
              <div className="mesh-agent mesh-agent-live">Rule Evaluation</div>
              <div className="mesh-agent mesh-agent-live">Issue Resolution</div>
              <div className="mesh-agent mesh-agent-live">Escalation</div>
              <div className="mesh-agent mesh-agent-live">DQ Drift / Anomaly Monitoring</div>
            </div>
            <div className="mesh-domain-cta">
              <span>Launch Data Quality Agent</span>
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="4" y1="10" x2="16" y2="10" />
                <polyline points="11 5 16 10 11 15" />
              </svg>
            </div>
          </button>

          {/* Data Management */}
          <div className="mesh-domain mesh-domain-dm">
            <div className="mesh-domain-header">
              <div className="mesh-domain-icon mesh-icon-dm">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M21 12c0 1.66-4.03 3-9 3s-9-1.34-9-3" />
                  <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
                </svg>
              </div>
              <div className="mesh-domain-info">
                <h3>Data Management</h3>
                <span className="mesh-domain-role">ORCHESTRATOR</span>
              </div>
              <span className="mesh-badge mesh-badge-soon">Coming Soon</span>
            </div>
            <div className="mesh-agents">
              <div className="mesh-agent">Reference Data</div>
              <div className="mesh-agent">Master Data</div>
              <div className="mesh-agent">Synchronisation</div>
              <div className="mesh-agent">Entity Matching</div>
              <div className="mesh-agent">Enrichment & Standardisation</div>
            </div>
          </div>

          {/* Data Consumption */}
          <div className="mesh-domain mesh-domain-dc">
            <div className="mesh-domain-header">
              <div className="mesh-domain-icon mesh-icon-dc">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </div>
              <div className="mesh-domain-info">
                <h3>Data Consumption</h3>
                <span className="mesh-domain-role">ORCHESTRATOR</span>
              </div>
              <span className="mesh-badge mesh-badge-soon">Coming Soon</span>
            </div>
            <div className="mesh-agents">
              <div className="mesh-agent">Semantic Routing</div>
              <div className="mesh-agent">Natural Language Query</div>
              <div className="mesh-agent">Business Reporting</div>
              <div className="mesh-agent">Data Product Publishing</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mesh-footer">
          <div className="mesh-footer-systems">
            <span className="mesh-foot-chip">SAP MDG</span>
            <span className="mesh-foot-chip">Informatica</span>
            <span className="mesh-foot-chip">Collibra</span>
            <span className="mesh-foot-chip">Snowflake</span>
            <span className="mesh-foot-chip">Databricks</span>
            <span className="mesh-foot-chip mesh-foot-ai">Powered by Claude on AWS Bedrock</span>
          </div>
        </footer>
      </div>

      {/* Connection overlay */}
      {connectionState !== "idle" && (
        <div className="mesh-overlay">
          <div className={`mesh-modal ${connectionState === "pick-source" || connectionState === "pick-schema" ? "mesh-modal-wide" : ""}`}>
            {/* Step 1: Pick data source */}
            {connectionState === "pick-source" && (
              <div className="mesh-picker">
                <div className="mesh-picker-header">
                  <h3>Connect Data Source</h3>
                  <p>Choose how to load data for the Data Quality Agent</p>
                  <button
                    className="mesh-picker-close"
                    onClick={() => setConnectionState("idle")}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
                <div className="mesh-picker-cards">
                  <button
                    className="mesh-pick-card"
                    onClick={() => setConnectionState("pick-schema")}
                  >
                    <div className="mesh-pick-icon mesh-pick-sf">
                      <svg viewBox="0 0 48 48" fill="none">
                        <line x1="24" y1="8" x2="24" y2="40" stroke="currentColor" strokeWidth="2" />
                        <line x1="10" y1="16" x2="38" y2="32" stroke="currentColor" strokeWidth="2" />
                        <line x1="38" y1="16" x2="10" y2="32" stroke="currentColor" strokeWidth="2" />
                        <circle cx="24" cy="24" r="3.5" stroke="currentColor" strokeWidth="1.5" />
                      </svg>
                    </div>
                    <h4>Snowflake</h4>
                    <p>AZ manufacturing warehouse — MES, LIMS, SAP, Master Data</p>
                    <div className="mesh-pick-meta">
                      <span>14 tables</span>
                      <span>10,630 records</span>
                    </div>
                    <div className="mesh-pick-cta mesh-pick-cta-sf">
                      Connect
                      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="4" y1="10" x2="16" y2="10" />
                        <polyline points="11 5 16 10 11 15" />
                      </svg>
                    </div>
                  </button>

                  <button
                    className="mesh-pick-card"
                    onClick={() => handlePickSource("CSV Upload (AZ Manufacturing)")}
                  >
                    <div className="mesh-pick-icon mesh-pick-csv">
                      <svg viewBox="0 0 48 48" fill="none">
                        <rect x="12" y="16" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" />
                        <line x1="16" y1="22" x2="26" y2="22" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />
                        <line x1="16" y1="26" x2="26" y2="26" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />
                        <line x1="16" y1="30" x2="22" y2="30" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />
                        <polyline points="32 18 37 13 42 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        <line x1="37" y1="13" x2="37" y2="28" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                      </svg>
                    </div>
                    <h4>Upload CSV</h4>
                    <p>Upload your own files or use AZ manufacturing demo dataset</p>
                    <div className="mesh-pick-meta">
                      <span>16 CSV files</span>
                      <span>DuckDB engine</span>
                    </div>
                    <div className="mesh-pick-cta mesh-pick-cta-csv">
                      Upload
                      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="4" y1="10" x2="16" y2="10" />
                        <polyline points="11 5 16 10 11 15" />
                      </svg>
                    </div>
                  </button>
                </div>
              </div>
            )}

            {/* Step 1b: Snowflake schema picker */}
            {connectionState === "pick-schema" && (
              <div className="mesh-picker mesh-schema-picker">
                <div className="mesh-picker-header">
                  <h3>Select Warehouse / Schema</h3>
                  <p>Snowflake — AZ_ENTERPRISE_WH</p>
                  <button
                    className="mesh-picker-close"
                    onClick={() => setConnectionState("pick-source")}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
                <div className="mesh-schema-list">
                  {[
                    { id: "MANUFACTURING", label: "Manufacturing", tables: 14, records: "10,630", desc: "MES, LIMS, SAP, Batch Records" },
                    { id: "CLINICAL", label: "Clinical Trials", tables: 8, records: "24,100", desc: "EDC, CTMS, Safety Data" },
                    { id: "SUPPLY_CHAIN", label: "Supply Chain", tables: 11, records: "18,400", desc: "Logistics, Inventory, Distribution" },
                    { id: "REGULATORY", label: "Regulatory", tables: 6, records: "5,200", desc: "CMC, Submissions, Compliance" },
                    { id: "COMMERCIAL", label: "Commercial", tables: 9, records: "32,800", desc: "Sales, CRM, Market Access" },
                  ].map((schema) => (
                    <button
                      key={schema.id}
                      className={`mesh-schema-row ${selectedSchema === schema.id ? "mesh-schema-selected" : ""}`}
                      onClick={() => setSelectedSchema(schema.id)}
                    >
                      <div className="mesh-schema-radio">
                        {selectedSchema === schema.id && <div className="mesh-schema-radio-dot" />}
                      </div>
                      <div className="mesh-schema-info">
                        <div className="mesh-schema-name">{schema.label}</div>
                        <div className="mesh-schema-desc">{schema.desc}</div>
                      </div>
                      <div className="mesh-schema-stats">
                        <span>{schema.tables} tables</span>
                        <span>{schema.records} rows</span>
                      </div>
                    </button>
                  ))}
                </div>
                <button
                  className="mesh-schema-connect"
                  onClick={() => handlePickSource(`Snowflake — ${selectedSchema}`)}
                >
                  <span>Connect to {selectedSchema.charAt(0) + selectedSchema.slice(1).toLowerCase()}</span>
                  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="4" y1="10" x2="16" y2="10" />
                    <polyline points="11 5 16 10 11 15" />
                  </svg>
                </button>
              </div>
            )}

            {/* Step 2: Connecting */}
            {connectionState === "connecting" && (
              <div className="mesh-status">
                <div className="mesh-loader">
                  <div className="mesh-loader-ring" />
                  <div className="mesh-loader-core" />
                </div>
                <h3>Connecting to {connectingSource}...</h3>
                <p>Loading 14 tables, 15 DQ rules, 10,630 records</p>
              </div>
            )}

            {/* Step 3: Success */}
            {connectionState === "success" && (
              <div className="mesh-status mesh-status-ok">
                <div className="mesh-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <h3>Agent Ready</h3>
                <p>{connectingSource} connected successfully</p>
              </div>
            )}

            {/* Error */}
            {connectionState === "error" && (
              <div className="mesh-status mesh-status-err">
                <div className="mesh-err-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                </div>
                <h3>Connection Failed</h3>
                <p>{errorMessage}</p>
                <button
                  className="mesh-retry"
                  onClick={() => setConnectionState("pick-source")}
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataSourcePanel;
