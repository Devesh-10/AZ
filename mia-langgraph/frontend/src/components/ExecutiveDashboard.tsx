import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import "./ExecutiveDashboard.css";

interface DashboardProps {
  onStartChat: () => void;
}

interface ManufacturingKpiData {
  batchYield: { current: number; target: number; trend: { week: string; value: number }[] };
  rft: { current: number; target: number; trend: { week: string; value: number }[] };
  oee: { current: number; target: number; availability: number; performance: number; quality: number };
  cycleTime: { current: number; target: number; trend: { week: string; value: number }[] };
  production: { batches: number; volume: number; trend: { week: string; batches: number; volume: number }[] };
  deviations: { current: number; target: number; bySite: { site: string; count: number }[] };
  sitePerformance: { site: string; yield: number; rft: number; oee: number }[];
}

const COLORS = {
  primary: "#0f766e",
  secondary: "#115e59",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  purple: "#8b5cf6",
  teal: "#14b8a6",
  cyan: "#06b6d4",
};

const ExecutiveDashboard: React.FC<DashboardProps> = ({ onStartChat }) => {
  const [data, setData] = useState<ManufacturingKpiData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    // Load manufacturing KPI data
    setTimeout(() => {
      setData({
        batchYield: {
          current: 97.32,
          target: 98.0,
          trend: [
            { week: "W1", value: 96.8 },
            { week: "W2", value: 97.1 },
            { week: "W3", value: 96.9 },
            { week: "W4", value: 97.5 },
            { week: "W5", value: 97.2 },
            { week: "W6", value: 97.32 },
          ],
        },
        rft: {
          current: 94.5,
          target: 95.0,
          trend: [
            { week: "W1", value: 93.2 },
            { week: "W2", value: 94.1 },
            { week: "W3", value: 93.8 },
            { week: "W4", value: 94.6 },
            { week: "W5", value: 94.3 },
            { week: "W6", value: 94.5 },
          ],
        },
        oee: {
          current: 85.2,
          target: 90.0,
          availability: 92.1,
          performance: 94.3,
          quality: 98.2,
        },
        cycleTime: {
          current: 4.2,
          target: 4.0,
          trend: [
            { week: "W1", value: 4.5 },
            { week: "W2", value: 4.4 },
            { week: "W3", value: 4.3 },
            { week: "W4", value: 4.25 },
            { week: "W5", value: 4.22 },
            { week: "W6", value: 4.2 },
          ],
        },
        production: {
          batches: 1247,
          volume: 2456000,
          trend: [
            { week: "W1", batches: 195, volume: 385000 },
            { week: "W2", batches: 210, volume: 412000 },
            { week: "W3", batches: 198, volume: 390000 },
            { week: "W4", batches: 225, volume: 445000 },
            { week: "W5", batches: 208, volume: 410000 },
            { week: "W6", batches: 211, volume: 414000 },
          ],
        },
        deviations: {
          current: 2.3,
          target: 2.0,
          bySite: [
            { site: "Baar", count: 12 },
            { site: "Sodertalje", count: 18 },
            { site: "Macclesfield", count: 15 },
            { site: "Frederick", count: 8 },
          ],
        },
        sitePerformance: [
          { site: "Baar", yield: 98.1, rft: 95.2, oee: 87.5 },
          { site: "Sodertalje", yield: 96.8, rft: 93.8, oee: 84.2 },
          { site: "Macclesfield", yield: 97.5, rft: 94.1, oee: 85.8 },
          { site: "Frederick", yield: 97.9, rft: 95.0, oee: 86.3 },
        ],
      });
      setLoading(false);
    }, 800);

    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading Manufacturing Dashboard...</p>
      </div>
    );
  }

  const oeeBreakdownData = [
    { name: "Availability", value: data!.oee.availability, color: COLORS.success },
    { name: "Performance", value: data!.oee.performance, color: COLORS.info },
    { name: "Quality", value: data!.oee.quality, color: COLORS.purple },
  ];

  const getStatusColor = (current: number, target: number, lowerIsBetter = false) => {
    if (lowerIsBetter) {
      return current <= target ? COLORS.success : current <= target * 1.1 ? COLORS.warning : COLORS.danger;
    }
    return current >= target ? COLORS.success : current >= target * 0.95 ? COLORS.warning : COLORS.danger;
  };

  const getStatusText = (current: number, target: number, lowerIsBetter = false) => {
    if (lowerIsBetter) {
      return current <= target ? "On Target" : current <= target * 1.1 ? "Near Target" : "Below Target";
    }
    return current >= target ? "On Target" : current >= target * 0.95 ? "Near Target" : "Below Target";
  };

  // Calculate overall manufacturing score
  const manufacturingScore = Math.round(
    (data!.batchYield.current / data!.batchYield.target * 25) +
    (data!.rft.current / data!.rft.target * 25) +
    (data!.oee.current / data!.oee.target * 25) +
    (data!.cycleTime.target / data!.cycleTime.current * 25)
  );

  return (
    <div className="executive-dashboard manufacturing">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon manufacturing">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 20h20" />
                <path d="M5 20V10l4-4 4 4v10" />
                <path d="M13 20V4l6 4v12" />
                <path d="M8 14h1" />
                <path d="M8 17h1" />
                <path d="M16 10h1" />
                <path d="M16 14h1" />
                <path d="M16 17h1" />
              </svg>
            </div>
            <div>
              <h1>AstraZeneca</h1>
              <span className="subtitle">Manufacturing Intelligence Platform</span>
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
            Ask MIA
          </button>
        </div>
      </header>

      {/* Manufacturing Score Hero */}
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
                stroke="url(#mfgScoreGradient)"
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${manufacturingScore * 5.65} 565`}
                transform="rotate(-90 100 100)"
              />
              <defs>
                <linearGradient id="mfgScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={COLORS.teal} />
                  <stop offset="100%" stopColor={COLORS.cyan} />
                </linearGradient>
              </defs>
            </svg>
            <div className="score-value">
              <span className="score-number">{manufacturingScore}</span>
              <span className="score-label">Manufacturing Excellence</span>
            </div>
          </div>
          <div className="score-breakdown">
            <h3>Performance Components</h3>
            <div className="score-item">
              <span>Batch Yield</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${(data!.batchYield.current / data!.batchYield.target) * 100}%`, background: getStatusColor(data!.batchYield.current, data!.batchYield.target) }}></div>
              </div>
              <span>{data!.batchYield.current}%</span>
            </div>
            <div className="score-item">
              <span>Right First Time</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${(data!.rft.current / data!.rft.target) * 100}%`, background: getStatusColor(data!.rft.current, data!.rft.target) }}></div>
              </div>
              <span>{data!.rft.current}%</span>
            </div>
            <div className="score-item">
              <span>OEE</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${(data!.oee.current / data!.oee.target) * 100}%`, background: getStatusColor(data!.oee.current, data!.oee.target) }}></div>
              </div>
              <span>{data!.oee.current}%</span>
            </div>
            <div className="score-item">
              <span>Cycle Time</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${(data!.cycleTime.target / data!.cycleTime.current) * 100}%`, background: getStatusColor(data!.cycleTime.current, data!.cycleTime.target, true) }}></div>
              </div>
              <span>{data!.cycleTime.current} hr</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="kpi-cards-row">
        <div className="kpi-card yield">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Batch Yield</span>
            <span className="kpi-value">{data!.batchYield.current}%</span>
            <span className="kpi-unit">Target: {data!.batchYield.target}%</span>
          </div>
          <div className={`kpi-trend ${data!.batchYield.current >= data!.batchYield.target ? 'positive' : 'warning'}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            {getStatusText(data!.batchYield.current, data!.batchYield.target)}
          </div>
        </div>

        <div className="kpi-card rft">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M8 12l2 2 4-4" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Right First Time</span>
            <span className="kpi-value">{data!.rft.current}%</span>
            <span className="kpi-unit">Target: {data!.rft.target}%</span>
          </div>
          <div className={`kpi-trend ${data!.rft.current >= data!.rft.target ? 'positive' : 'warning'}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            {getStatusText(data!.rft.current, data!.rft.target)}
          </div>
        </div>

        <div className="kpi-card oee">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 3v4M8 3v4" />
              <path d="M2 11h20" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">OEE</span>
            <span className="kpi-value">{data!.oee.current}%</span>
            <span className="kpi-unit">Target: {data!.oee.target}%</span>
          </div>
          <div className={`kpi-trend ${data!.oee.current >= data!.oee.target ? 'positive' : 'warning'}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            {getStatusText(data!.oee.current, data!.oee.target)}
          </div>
        </div>

        <div className="kpi-card cycletime">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Avg Cycle Time</span>
            <span className="kpi-value">{data!.cycleTime.current} hr</span>
            <span className="kpi-unit">Target: {data!.cycleTime.target} hr</span>
          </div>
          <div className={`kpi-trend ${data!.cycleTime.current <= data!.cycleTime.target ? 'positive' : 'warning'}`}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
              <polyline points="17 18 23 18 23 12" />
            </svg>
            {getStatusText(data!.cycleTime.current, data!.cycleTime.target, true)}
          </div>
        </div>

        <div className="kpi-card production">
          <div className="kpi-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Production Volume</span>
            <span className="kpi-value">{(data!.production.volume / 1000000).toFixed(2)}M</span>
            <span className="kpi-unit">{data!.production.batches} batches</span>
          </div>
          <div className="kpi-trend positive">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            +8% vs Plan
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Yield Trend */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Batch Yield Trend</h3>
            <span className={`chart-badge ${data!.batchYield.current >= data!.batchYield.target ? 'success' : 'warning'}`}>
              {data!.batchYield.current >= data!.batchYield.target ? 'On Target' : 'Near Target'}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data!.batchYield.trend}>
              <defs>
                <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.teal} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.teal} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="week" tick={{ fontSize: 12 }} stroke="#9ca3af" />
              <YAxis domain={[95, 100]} tick={{ fontSize: 12 }} stroke="#9ca3af" unit="%" />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value: number) => [`${value}%`, 'Yield']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={COLORS.teal}
                strokeWidth={3}
                fill="url(#yieldGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* OEE Breakdown */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>OEE Breakdown</h3>
            <span className="chart-badge info">{data!.oee.current}% Overall</span>
          </div>
          <div className="pie-chart-container">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={oeeBreakdownData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#9ca3af" unit="%" />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} stroke="#9ca3af" width={90} />
                <Tooltip
                  contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value: number) => [`${value}%`, '']}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {oeeBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Production Trend */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Weekly Production</h3>
            <span className="chart-badge success">Above Plan</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data!.production.trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="week" tick={{ fontSize: 11 }} stroke="#9ca3af" />
              <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Bar dataKey="batches" fill={COLORS.info} radius={[4, 4, 0, 0]} name="Batches" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="bottom-row">
        {/* Site Performance */}
        <div className="chart-card wide">
          <div className="chart-header">
            <h3>Site Performance Comparison</h3>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data!.sitePerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="site" tick={{ fontSize: 11 }} stroke="#9ca3af" />
              <YAxis domain={[80, 100]} tick={{ fontSize: 11 }} stroke="#9ca3af" unit="%" />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Legend />
              <Bar dataKey="yield" name="Yield" fill={COLORS.success} radius={[4, 4, 0, 0]} />
              <Bar dataKey="rft" name="RFT" fill={COLORS.info} radius={[4, 4, 0, 0]} />
              <Bar dataKey="oee" name="OEE" fill={COLORS.purple} radius={[4, 4, 0, 0]} />
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
            <h3>Manufacturing Insights</h3>
          </div>
          <div className="insights-list">
            <div className="insight-item success">
              <span className="insight-icon">✓</span>
              <p>Batch yield at 97.32% - strong performance across all sites</p>
            </div>
            <div className="insight-item warning">
              <span className="insight-icon">!</span>
              <p>OEE at 85.2% - below 90% target. Focus on availability improvements</p>
            </div>
            <div className="insight-item info">
              <span className="insight-icon">i</span>
              <p>Sodertalje showing lower RFT - investigate recent deviations</p>
            </div>
            <div className="insight-item success">
              <span className="insight-icon">✓</span>
              <p>Cycle time improving - down 0.3 hr over 6 weeks</p>
            </div>
          </div>
          <button className="ask-more-btn" onClick={onStartChat}>
            Ask MIA for Analysis
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
        <span>Data Source: Manufacturing Execution System</span>
        <span>Powered by MIA (Manufacturing Insight Agent)</span>
      </footer>
    </div>
  );
};

export default ExecutiveDashboard;
