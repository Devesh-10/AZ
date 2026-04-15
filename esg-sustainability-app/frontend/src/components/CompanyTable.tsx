import React, { useState, useEffect } from "react";
import type { Company, FilterOptions } from "../types";
import { fetchCompanies, fetchFilters } from "../api/api";

const ratingColor: Record<string, string> = {
  AAA: "#059669",
  AA: "#10b981",
  A: "#34d399",
  BBB: "#ca8a04",
  BB: "#ea580c",
  B: "#dc2626",
  CCC: "#991b1b",
};

const CompanyTable: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [sector, setSector] = useState("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("Total_ESG_Score");
  const [order, setOrder] = useState("desc");

  useEffect(() => {
    fetchFilters().then(setFilters);
  }, []);

  useEffect(() => {
    fetchCompanies({
      sector: sector || undefined,
      search: search || undefined,
      sort_by: sortBy,
      order,
    }).then(setCompanies);
  }, [sector, search, sortBy, order]);

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setOrder(order === "desc" ? "asc" : "desc");
    } else {
      setSortBy(col);
      setOrder("desc");
    }
  };

  const SortIcon = ({ col }: { col: string }) =>
    sortBy === col ? <span>{order === "desc" ? " \u25BC" : " \u25B2"}</span> : null;

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Company ESG Scores</h3>
      <div style={styles.filterRow}>
        <input
          type="text"
          placeholder="Search companies..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={styles.searchInput}
        />
        <select value={sector} onChange={(e) => setSector(e.target.value)} style={styles.select}>
          <option value="">All Sectors</option>
          {filters?.sectors.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              {[
                { key: "Company", label: "Company" },
                { key: "Sector", label: "Sector" },
                { key: "Environmental_Score", label: "Env" },
                { key: "Social_Score", label: "Social" },
                { key: "Governance_Score", label: "Gov" },
                { key: "Total_ESG_Score", label: "Total" },
                { key: "ESG_Rating", label: "Rating" },
              ].map(({ key, label }) => (
                <th key={key} onClick={() => handleSort(key)} style={styles.th}>
                  {label}
                  <SortIcon col={key} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {companies.map((c) => (
              <tr key={c.Company} style={styles.tr}>
                <td style={styles.td}>{c.Company}</td>
                <td style={styles.td}>{c.Sector}</td>
                <td style={styles.tdNum}>{c.Environmental_Score}</td>
                <td style={styles.tdNum}>{c.Social_Score}</td>
                <td style={styles.tdNum}>{c.Governance_Score}</td>
                <td style={{ ...styles.tdNum, fontWeight: 600 }}>{c.Total_ESG_Score}</td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.ratingBadge,
                      background: `${ratingColor[c.ESG_Rating] || "#94a3b8"}18`,
                      color: ratingColor[c.ESG_Rating] || "#94a3b8",
                      borderColor: ratingColor[c.ESG_Rating] || "#94a3b8",
                    }}
                  >
                    {c.ESG_Rating}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: { background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" },
  title: { margin: "0 0 16px", fontSize: 15, fontWeight: 600, color: "#1e293b" },
  filterRow: { display: "flex", gap: 12, marginBottom: 16 },
  searchInput: {
    flex: 1, padding: "8px 14px", borderRadius: 8, border: "1px solid #e2e8f0",
    fontSize: 13, outline: "none", fontFamily: "Inter, sans-serif",
  },
  select: {
    padding: "8px 14px", borderRadius: 8, border: "1px solid #e2e8f0",
    fontSize: 13, background: "#fff", fontFamily: "Inter, sans-serif",
  },
  tableWrapper: { overflowX: "auto", maxHeight: 400 },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: {
    textAlign: "left", padding: "10px 12px", borderBottom: "2px solid #e2e8f0",
    color: "#64748b", fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", fontSize: 12,
    position: "sticky" as const, top: 0, background: "#fff",
  },
  tr: { borderBottom: "1px solid #f1f5f9" },
  td: { padding: "10px 12px", color: "#334155" },
  tdNum: { padding: "10px 12px", color: "#334155", textAlign: "center" },
  ratingBadge: {
    display: "inline-block", padding: "2px 10px", borderRadius: 12,
    fontWeight: 600, fontSize: 12, border: "1px solid",
  },
};

export default CompanyTable;
