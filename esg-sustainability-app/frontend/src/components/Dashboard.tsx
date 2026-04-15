import React, { useState, useEffect } from "react";
import type { Summary, SectorData, RatingData, Company } from "../types";
import { fetchSummary, fetchSectors, fetchRatings, fetchTopCompanies } from "../api/api";
import { SectorBarChart, RatingPieChart, TopCompaniesRadar } from "./ESGChart";
import CompanyTable from "./CompanyTable";

const KPICard: React.FC<{ label: string; value: string | number; sub?: string; color: string }> = ({
  label, value, sub, color,
}) => (
  <div style={{ ...styles.kpiCard, borderTop: `3px solid ${color}` }}>
    <div style={styles.kpiLabel}>{label}</div>
    <div style={{ ...styles.kpiValue, color }}>{value}</div>
    {sub && <div style={styles.kpiSub}>{sub}</div>}
  </div>
);

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [sectors, setSectors] = useState<SectorData[]>([]);
  const [ratings, setRatings] = useState<RatingData[]>([]);
  const [topCompanies, setTopCompanies] = useState<Company[]>([]);

  useEffect(() => {
    fetchSummary().then(setSummary);
    fetchSectors().then(setSectors);
    fetchRatings().then(setRatings);
    fetchTopCompanies(10).then(setTopCompanies);
  }, []);

  if (!summary) {
    return <div style={styles.loading}>Loading dashboard...</div>;
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.pageTitle}>ESG Sustainability Dashboard</h2>
      <p style={styles.pageSubtitle}>
        Environmental, Social & Governance scores for {summary.total_companies} companies across{" "}
        {summary.sectors} sectors
      </p>

      <div style={styles.kpiRow}>
        <KPICard label="Avg Environmental" value={summary.avg_environmental} sub="out of 100" color="#10b981" />
        <KPICard label="Avg Social" value={summary.avg_social} sub="out of 100" color="#3b82f6" />
        <KPICard label="Avg Governance" value={summary.avg_governance} sub="out of 100" color="#8b5cf6" />
        <KPICard label="Total ESG Avg" value={summary.avg_total_esg} sub="out of 100" color="#059669" />
        <KPICard label="Top Rated (AA+)" value={summary.top_rated_count} sub={`of ${summary.total_companies}`} color="#f59e0b" />
        <KPICard label="Countries" value={summary.countries} sub="represented" color="#6366f1" />
      </div>

      <div style={styles.chartRow}>
        <div style={styles.chartCard}>
          <SectorBarChart data={sectors} />
        </div>
        <div style={styles.chartCard}>
          <RatingPieChart data={ratings} />
        </div>
      </div>

      <div style={styles.chartRow}>
        <div style={styles.chartCard}>
          <TopCompaniesRadar data={topCompanies} />
        </div>
      </div>

      <CompanyTable />
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: { display: "flex", flexDirection: "column", gap: 20 },
  loading: { padding: 40, textAlign: "center", color: "#64748b", fontSize: 14 },
  pageTitle: { margin: 0, fontSize: 22, fontWeight: 700, color: "#0f172a" },
  pageSubtitle: { margin: "4px 0 0", fontSize: 14, color: "#64748b" },
  kpiRow: {
    display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 14,
  },
  kpiCard: {
    background: "#fff", borderRadius: 12, padding: "16px 20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
  kpiLabel: { fontSize: 12, color: "#64748b", fontWeight: 500, marginBottom: 6 },
  kpiValue: { fontSize: 28, fontWeight: 700 },
  kpiSub: { fontSize: 11, color: "#94a3b8", marginTop: 2 },
  chartRow: {
    display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 16,
  },
  chartCard: {
    background: "#fff", borderRadius: 12, padding: 20,
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
};

export default Dashboard;
