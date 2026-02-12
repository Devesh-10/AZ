import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./ExecutiveDashboard.css";

interface DashboardProps {
  onStartChat: () => void;
}

interface KpiData {
  energy: { total: number; renewable: number; imported: number; trend: number[] };
  emissions: { scope1: number; scope2: number; total: number; trend: number[] };
  water: { total: number; groundwater: number; municipal: number };
  waste: { total: number; siteWaste: number; productWaste: number };
  fleet: { total: number; ev: number; evPercent: number; trend: number[] };
}

const COLORS = {
  primary: "#7c3a5c",
  secondary: "#5a2a42",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  purple: "#8b5cf6",
  teal: "#14b8a6",
};

const ExecutiveDashboard: React.FC<DashboardProps> = ({ onStartChat }) => {
  const [data, setData] = useState<KpiData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    // Simulate loading KPI data
    setTimeout(() => {
      setData({
        energy: {
          total: 1611.84,
          renewable: 1622.43,
          imported: 1634.3,
          trend: [1450, 1520, 1580, 1611, 1590, 1620],
        },
        emissions: {
          scope1: 245.8,
          scope2: 189.3,
          total: 435.1,
          trend: [520, 490, 465, 450, 440, 435],
        },
        water: {
          total: 2.85,
          groundwater: 1.12,
          municipal: 1.73,
        },
        waste: {
          total: 1245.6,
          siteWaste: 856.2,
          productWaste: 389.4,
        },
        fleet: {
          total: 4771,
          ev: 101,
          evPercent: 2.1,
          trend: [0.5, 0.8, 1.2, 1.5, 1.8, 2.1],
        },
      });
      setLoading(false);
    }, 1000);

    // Update time every second
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading Executive Dashboard...</p>
      </div>
    );
  }

  const energyMixData = [
    { name: "Renewable", value: data!.energy.renewable, color: COLORS.success },
    { name: "Imported", value: data!.energy.imported - data!.energy.renewable, color: COLORS.info },
  ];

  const emissionsTrendData = data!.emissions.trend.map((val, idx) => ({
    month: ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][idx],
    emissions: val,
  }));

  const evTrendData = data!.fleet.trend.map((val, idx) => ({
    quarter: ["Q1'24", "Q2'24", "Q3'24", "Q4'24", "Q1'25", "Q2'25"][idx],
    evPercent: val,
  }));

  const wasteBreakdownData = [
    { name: "Site Waste", value: data!.waste.siteWaste, color: COLORS.warning },
    { name: "Product Waste", value: data!.waste.productWaste, color: COLORS.purple },
  ];

  const waterSourceData = [
    { name: "Groundwater", value: data!.water.groundwater, color: COLORS.info },
    { name: "Municipal", value: data!.water.municipal, color: COLORS.teal },
  ];

  const sustainabilityScore = Math.round(
    ((data!.energy.renewable / data!.energy.total) * 40) +
    ((500 - data!.emissions.total) / 500 * 30) +
    (data!.fleet.evPercent * 3)
  );

  return (
    <div className="executive-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <h1>AstraZeneca</h1>
              <span className="subtitle">Sustainability Command Center</span>
            </div>
          </div>
        </div>
        <div className="header-center">
          <div className="live-indicator">
            <span className="pulse"></span>
            LIVE DATA
          </div>
          <div className="current-time">
            {currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            <span className="time">{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>
        <div className="header-right">
          <button className="ai-assistant-btn" onClick={onStartChat}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Ask AI Assistant
          </button>
        </div>
      </header>

      {/* Sustainability Score Hero */}
      <div className="score-hero">
        <div className="score-card">
          <div className="score-visual">
            <svg viewBox="0 0 200 200" className="score-ring">
              <circle cx="100" cy="100" r="90" fill="none" stroke="#e5e7eb" strokeWidth="12" />
              <circle
                cx="100"
                cy="100"
                r="90"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${sustainabilityScore * 5.65} 565`}
                transform="rotate(-90 100 100)"
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={COLORS.success} />
                  <stop offset="100%" stopColor={COLORS.teal} />
                </linearGradient>
              </defs>
            </svg>
            <div className="score-value">
              <span className="score-number">{sustainabilityScore}</span>
              <span className="score-label">Sustainability Score</span>
            </div>
          </div>
          <div className="score-breakdown">
            <h3>Score Components</h3>
            <div className="score-item">
              <span>Renewable Energy</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: '100%', background: COLORS.success }}></div>
              </div>
              <span>100%</span>
            </div>
            <div className="score-item">
              <span>Emissions Reduction</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: '87%', background: COLORS.info }}></div>
              </div>
              <span>-13% YoY</span>
            </div>
            <div className="score-item">
              <span>Fleet Electrification</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: '21%', background: COLORS.purple }}></div>
              </div>
              <span>2.1%</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="kpi-cards-row">
        <div className="kpi-card energy">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Total Energy</span>
            <span className="kpi-value">{data!.energy.total.toLocaleString()}</span>
            <span className="kpi-unit">MWh</span>
          </div>
          <div className="kpi-trend positive">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            100% Renewable
          </div>
        </div>

        <div className="kpi-card emissions">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">GHG Emissions</span>
            <span className="kpi-value">{data!.emissions.total.toLocaleString()}</span>
            <span className="kpi-unit">tCO2e</span>
          </div>
          <div className="kpi-trend positive">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
              <polyline points="17 18 23 18 23 12" />
            </svg>
            -16% YoY
          </div>
        </div>

        <div className="kpi-card water">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Water Usage</span>
            <span className="kpi-value">{data!.water.total.toFixed(2)}</span>
            <span className="kpi-unit">Million m³</span>
          </div>
          <div className="kpi-trend neutral">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            On Target
          </div>
        </div>

        <div className="kpi-card waste">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Total Waste</span>
            <span className="kpi-value">{data!.waste.total.toLocaleString()}</span>
            <span className="kpi-unit">Tonnes</span>
          </div>
          <div className="kpi-trend positive">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
              <polyline points="17 18 23 18 23 12" />
            </svg>
            -8% YoY
          </div>
        </div>

        <div className="kpi-card fleet">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="1" y="3" width="15" height="13" rx="2" ry="2" />
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
              <circle cx="5.5" cy="18.5" r="2.5" />
              <circle cx="18.5" cy="18.5" r="2.5" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">EV Fleet</span>
            <span className="kpi-value">{data!.fleet.evPercent}%</span>
            <span className="kpi-unit">{data!.fleet.ev} of {data!.fleet.total}</span>
          </div>
          <div className="kpi-trend positive">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            +40% YoY
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Emissions Trend */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>GHG Emissions Trend</h3>
            <span className="chart-badge success">On Track to Net Zero</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={emissionsTrendData}>
              <defs>
                <linearGradient id="emissionsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#9ca3af" />
              <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Area
                type="monotone"
                dataKey="emissions"
                stroke={COLORS.primary}
                strokeWidth={3}
                fill="url(#emissionsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Energy Mix */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Energy Mix</h3>
            <span className="chart-badge success">100% Renewable</span>
          </div>
          <div className="pie-chart-container">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={energyMixData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {energyMixData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="pie-legend">
              {energyMixData.map((entry, index) => (
                <div key={index} className="legend-item">
                  <span className="legend-color" style={{ background: entry.color }}></span>
                  <span>{entry.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* EV Transition */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Fleet Electrification</h3>
            <span className="chart-badge info">Growing 40% YoY</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={evTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="quarter" tick={{ fontSize: 11 }} stroke="#9ca3af" />
              <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" unit="%" />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Bar dataKey="evPercent" fill={COLORS.purple} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="bottom-row">
        {/* Waste Breakdown */}
        <div className="chart-card small">
          <div className="chart-header">
            <h3>Waste Breakdown</h3>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={wasteBreakdownData}
                cx="50%"
                cy="50%"
                outerRadius={60}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {wasteBreakdownData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Water Sources */}
        <div className="chart-card small">
          <div className="chart-header">
            <h3>Water Sources</h3>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={waterSourceData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" tick={{ fontSize: 11 }} stroke="#9ca3af" />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} stroke="#9ca3af" width={80} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {waterSourceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* AI Insights */}
        <div className="insights-card">
          <div className="insights-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <h3>AI-Powered Insights</h3>
          </div>
          <div className="insights-list">
            <div className="insight-item success">
              <span className="insight-icon">✓</span>
              <p>Renewable energy exceeds consumption - potential for carbon credits</p>
            </div>
            <div className="insight-item warning">
              <span className="insight-icon">!</span>
              <p>Fleet electrification at 2.1% - accelerate EV adoption to meet 2030 targets</p>
            </div>
            <div className="insight-item info">
              <span className="insight-icon">i</span>
              <p>Scope 2 emissions down 16% - market-based approach showing results</p>
            </div>
          </div>
          <button className="ask-more-btn" onClick={onStartChat}>
            Ask AI for More Insights
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="dashboard-footer">
        <span>Last updated: {currentTime.toLocaleString()}</span>
        <span>Data Source: Enablon Sustainability Platform</span>
        <span>Powered by Claude AI</span>
      </footer>
    </div>
  );
};

export default ExecutiveDashboard;
