import { useState, useEffect } from "react";
import {
  FlaskConical, Brain, Shield, Microscope,
  Table2, FileText, Database, Lock, Cpu,
  LogOut, Activity, CheckCircle2, Clock, Zap
} from "lucide-react";
import type { Platform } from "../types";
import "./PlatformSelector.css";

const ICON_MAP: Record<string, any> = {
  flask: FlaskConical, brain: Brain, shield: Shield, microscope: Microscope,
  table: Table2, "file-text": FileText, database: Database, lock: Lock, cpu: Cpu,
};

const STATIC_PLATFORMS: Platform[] = [
  {
    id: "3dp", name: "3DP - Drug Development Data Platform",
    description: "Regulatory validation testing for Module 2/3 CTD submissions, FDA/EMA compliance",
    depth: "deep", icon: "flask", color: "#3b82f6",
    testDomains: ["CTD Module 2/3", "eCTD Validation", "Regulatory Filing"],
    sampleQueries: ["Test Module 3 submission validation", "Validate CDISC format compliance", "Test eCTD gateway submission"],
    metrics: { totalTests: 847, passRate: 94.2, avgExecutionTime: "2.3 min", manualEquivalent: "18 days" },
  },
  {
    id: "bikg", name: "BIKG - Biological Intelligence Knowledge Graph",
    description: "Knowledge graph query testing, ontology validation, entity relationship integrity",
    depth: "deep", icon: "brain", color: "#8b5cf6",
    testDomains: ["KG Query Validation", "Ontology Integrity", "Data Ingestion"],
    sampleQueries: ["Validate gene-disease relationship queries", "Test ontology boundary cases", "Verify KG ingestion pipeline"],
    metrics: { totalTests: 623, passRate: 91.7, avgExecutionTime: "1.8 min", manualEquivalent: "14 days" },
  },
  {
    id: "patient_safety", name: "Patient Safety - Pharmacovigilance",
    description: "ICSR processing, MedDRA coding, adverse event reporting, E2B(R3) compliance",
    depth: "deep", icon: "shield", color: "#ef4444",
    testDomains: ["ICSR Validation", "MedDRA Coding", "Signal Detection", "E2B Compliance"],
    sampleQueries: ["Test adverse event reporting for Patient Safety", "Validate ICSR mandatory fields", "Test E2B(R3) XML compliance"],
    metrics: { totalTests: 1203, passRate: 96.8, avgExecutionTime: "3.1 min", manualEquivalent: "22 days" },
  },
  {
    id: "clinical_trials", name: "Clinical Trials - CDISC/SDTM",
    description: "Protocol validation, CDISC SDTM/ADaM conformance, Define-XML, P21 checks",
    depth: "deep", icon: "microscope", color: "#10b981",
    testDomains: ["SDTM Compliance", "ADaM Derivations", "Define-XML", "P21 Validation"],
    sampleQueries: ["Validate SDTM domain conformance for DM", "Test ADaM derivation rules", "Run Pinnacle 21 validation"],
    metrics: { totalTests: 956, passRate: 93.5, avgExecutionTime: "2.7 min", manualEquivalent: "20 days" },
  },
  {
    id: "cdisc_adam", name: "CDISC/ADaM - Analysis Dataset Model",
    description: "Clinical data format validation and transformation testing",
    depth: "visual", icon: "table", color: "#f59e0b",
    metrics: { totalTests: 412, passRate: 92.1, avgExecutionTime: "1.5 min", manualEquivalent: "12 days" },
  },
  {
    id: "regulatory_docs", name: "Regulatory Docs - eCTD Gateway",
    description: "Module 2/3 submission document validation and cross-reference integrity",
    depth: "visual", icon: "file-text", color: "#6366f1",
    metrics: { totalTests: 328, passRate: 95.3, avgExecutionTime: "2.0 min", manualEquivalent: "15 days" },
  },
  {
    id: "study_pldb", name: "Study PLDB - Protocol Library",
    description: "Patient-level database quality validation and PII protection testing",
    depth: "visual", icon: "database", color: "#ec4899",
    metrics: { totalTests: 567, passRate: 89.6, avgExecutionTime: "2.4 min", manualEquivalent: "16 days" },
  },
  {
    id: "gxp_systems", name: "GxP Systems - Validated Infra",
    description: "21 CFR Part 11 compliance, audit trail testing, electronic signatures",
    depth: "visual", icon: "lock", color: "#14b8a6",
    metrics: { totalTests: 734, passRate: 97.1, avgExecutionTime: "3.5 min", manualEquivalent: "25 days" },
  },
  {
    id: "hpc_environment", name: "HPC - High Performance Compute",
    description: "ReFrame environment tests, job scheduling validation, metadata-scenario consistency, computational reproducibility",
    depth: "deep", icon: "cpu", color: "#f97316",
    testDomains: ["ReFrame Tests", "Job Scheduling", "Metadata-Scenario", "Reproducibility"],
    sampleQueries: ["Validate HPC job scheduling fairness across genomics workloads", "Test computational reproducibility for PKPD pipelines", "Check metadata-scenario consistency for batch runs"],
    metrics: { totalTests: 423, passRate: 97.5, avgExecutionTime: "1.5 min", manualEquivalent: "10 days" },
  },
];

interface Props {
  onPlatformSelect: (platformId: string) => void;
  onLogout: () => void;
}

export default function PlatformSelector({ onPlatformSelect, onLogout }: Props) {
  const [visible, setVisible] = useState(false);
  const platforms = STATIC_PLATFORMS;

  useEffect(() => { setVisible(true); }, []);

  const totalTests = platforms.reduce((s, p) => s + p.metrics.totalTests, 0);
  const avgPass = (platforms.reduce((s, p) => s + p.metrics.passRate, 0) / platforms.length).toFixed(1);
  const deepCount = platforms.filter((p) => p.depth === "deep").length;

  const handleClick = (p: Platform) => {
    if (p.depth === "deep") {
      onPlatformSelect(p.id);
    }
  };

  return (
    <div className={`platform-page ${visible ? "visible" : ""}`}>
      <header className="platform-header">
        <div className="header-left">
          <div className="header-icon">
            <Shield size={22} />
          </div>
          <div>
            <h1>Test Intelligence Agent</h1>
            <span className="header-sub">AstraZeneca R&D IT</span>
          </div>
        </div>
        <button className="logout-btn" onClick={onLogout}>
          <LogOut size={16} /> Sign Out
        </button>
      </header>

      <div className="platform-content">
        <div className="platform-intro">
          <h2>Select a Platform to Test</h2>
          <p>AI-powered 7-step testing pipeline across 9 R&D platforms</p>
        </div>

        <div className="metrics-bar">
          <div className="metric-item">
            <Activity size={16} />
            <span className="metric-value">{totalTests.toLocaleString()}</span>
            <span className="metric-label">Total Tests</span>
          </div>
          <div className="metric-item">
            <CheckCircle2 size={16} />
            <span className="metric-value">{avgPass}%</span>
            <span className="metric-label">Avg Pass Rate</span>
          </div>
          <div className="metric-item">
            <Zap size={16} />
            <span className="metric-value">{deepCount}</span>
            <span className="metric-label">AI-Ready</span>
          </div>
          <div className="metric-item">
            <Clock size={16} />
            <span className="metric-value">~5 min</span>
            <span className="metric-label">Avg Pipeline</span>
          </div>
        </div>

        <div className="platform-grid">
          {platforms.map((p, i) => {
            const Icon = ICON_MAP[p.icon] || FlaskConical;
            return (
              <div
                key={p.id}
                className={`platform-card ${p.depth}`}
                style={{ "--card-color": p.color, animationDelay: `${i * 60}ms` } as any}
                onClick={() => handleClick(p)}
              >
                <div className="card-top">
                  <div className="card-icon" style={{ background: p.color }}>
                    <Icon size={22} />
                  </div>
                  <span className={`card-badge ${p.depth}`}>
                    {p.depth === "deep" ? "AI-Ready" : "Coming Soon"}
                  </span>
                </div>

                <h3 className="card-name">{p.name}</h3>
                <p className="card-desc">{p.description}</p>

                <div className="card-metrics">
                  <div className="cm">
                    <span className="cm-value">{p.metrics.totalTests.toLocaleString()}</span>
                    <span className="cm-label">Tests</span>
                  </div>
                  <div className="cm">
                    <span className="cm-value">{p.metrics.passRate}%</span>
                    <span className="cm-label">Pass Rate</span>
                  </div>
                  <div className="cm">
                    <span className="cm-value">{p.metrics.avgExecutionTime}</span>
                    <span className="cm-label">Avg Time</span>
                  </div>
                </div>

                {p.depth === "deep" && (
                  <div className="card-cta">Start Testing &rarr;</div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
