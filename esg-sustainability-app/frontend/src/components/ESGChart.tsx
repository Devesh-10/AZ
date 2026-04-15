import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import type { SectorData, RatingData, Company } from "../types";

const COLORS = ["#10b981", "#059669", "#34d399", "#6ee7b7", "#a7f3d0", "#d1fae5", "#f0fdf4"];
const RATING_COLORS: Record<string, string> = {
  AAA: "#059669",
  AA: "#10b981",
  A: "#34d399",
  BBB: "#fbbf24",
  BB: "#f97316",
  B: "#ef4444",
  CCC: "#dc2626",
};

export const SectorBarChart: React.FC<{ data: SectorData[] }> = ({ data }) => (
  <div style={{ width: "100%", height: 320 }}>
    <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600, color: "#1e293b" }}>
      ESG Scores by Sector
    </h3>
    <ResponsiveContainer>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="Sector" angle={-35} textAnchor="end" fontSize={11} tick={{ fill: "#64748b" }} />
        <YAxis domain={[0, 100]} fontSize={11} tick={{ fill: "#64748b" }} />
        <Tooltip
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Environmental_Score" name="Environmental" fill="#10b981" radius={[2, 2, 0, 0]} />
        <Bar dataKey="Social_Score" name="Social" fill="#3b82f6" radius={[2, 2, 0, 0]} />
        <Bar dataKey="Governance_Score" name="Governance" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);

export const RatingPieChart: React.FC<{ data: RatingData[] }> = ({ data }) => (
  <div style={{ width: "100%", height: 320 }}>
    <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600, color: "#1e293b" }}>
      ESG Rating Distribution
    </h3>
    <ResponsiveContainer>
      <PieChart>
        <Pie
          data={data.filter((d) => d.count > 0)}
          cx="50%"
          cy="50%"
          outerRadius={100}
          dataKey="count"
          nameKey="rating"
          label={({ rating, count }) => `${rating}: ${count}`}
          labelLine={true}
          fontSize={12}
        >
          {data
            .filter((d) => d.count > 0)
            .map((entry, i) => (
              <Cell key={entry.rating} fill={RATING_COLORS[entry.rating] || COLORS[i % COLORS.length]} />
            ))}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  </div>
);

export const TopCompaniesRadar: React.FC<{ data: Company[] }> = ({ data }) => {
  const radarData = data.slice(0, 6).map((c) => ({
    company: c.Company.length > 12 ? c.Company.slice(0, 12) + "..." : c.Company,
    Environmental: c.Environmental_Score,
    Social: c.Social_Score,
    Governance: c.Governance_Score,
  }));

  return (
    <div style={{ width: "100%", height: 320 }}>
      <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600, color: "#1e293b" }}>
        Top Companies ESG Breakdown
      </h3>
      <ResponsiveContainer>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis dataKey="company" fontSize={10} tick={{ fill: "#64748b" }} />
          <PolarRadiusAxis domain={[0, 100]} fontSize={10} />
          <Radar name="Environmental" dataKey="Environmental" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
          <Radar name="Social" dataKey="Social" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
          <Radar name="Governance" dataKey="Governance" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.15} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
