import { useState } from "react";
import {
  ClipboardCheck, ChevronDown, ChevronRight, Download,
  CheckCircle2, XCircle, AlertTriangle
} from "lucide-react";
import type { ComplianceReport } from "../types";
import "./EvidenceReportPanel.css";

interface Props {
  report: ComplianceReport | null;
}

export default function EvidenceReportPanel({ report }: Props) {
  const [expandedSection, setExpandedSection] = useState<number | null>(0);

  if (!report) {
    return (
      <div className="erp-panel">
        <div className="erp-header">
          <ClipboardCheck size={14} />
          <span>Compliance Report</span>
        </div>
        <div className="erp-empty">
          <ClipboardCheck size={28} />
          <p>GxP evidence report will appear here</p>
        </div>
      </div>
    );
  }

  const StatusIcon = () => {
    switch (report.complianceStatus) {
      case "Compliant": return <CheckCircle2 size={16} />;
      case "Non-Compliant": return <XCircle size={16} />;
      default: return <AlertTriangle size={16} />;
    }
  };

  const statusClass = report.complianceStatus.toLowerCase().replace(/[- ]/g, "");

  return (
    <div className="erp-panel">
      <div className="erp-header">
        <ClipboardCheck size={14} />
        <span>Compliance Report</span>
      </div>

      <div className="erp-body">
        <div className={`erp-status-card ${statusClass}`}>
          <StatusIcon />
          <div className="esc-info">
            <span className="esc-label">{report.complianceStatus}</span>
            <span className="esc-detail">
              {report.passed}/{report.totalTests} tests passed &middot; {report.passRate.toFixed(1)}%
            </span>
          </div>
          <span className="esc-id">{report.reportId}</span>
        </div>

        <div className="erp-meta">
          <span>Platform: {report.platform}</span>
          <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
        </div>

        <div className="erp-sections">
          {report.sections.map((section, i) => (
            <div key={i} className="erp-section">
              <div
                className="erp-section-header"
                onClick={() => setExpandedSection(expandedSection === i ? null : i)}
              >
                {expandedSection === i ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span>{section.title}</span>
              </div>
              {expandedSection === i && (
                <div
                  className="erp-section-content"
                  dangerouslySetInnerHTML={{ __html: formatSectionContent(section.content) }}
                />
              )}
            </div>
          ))}
        </div>

        <button className="erp-download" disabled>
          <Download size={14} />
          <span>Download PDF Report</span>
        </button>
      </div>
    </div>
  );
}

function formatSectionContent(content: string): string {
  let html = content;
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^- (.*$)/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="section-list">$&</ul>');
  html = html.replace(/\n/g, "<br />");
  return html;
}
