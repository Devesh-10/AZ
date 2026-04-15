import React, { useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { VisualizationConfig } from "../types";
import "./VisualizationPanel.css";

interface VisualizationPanelProps {
  config: VisualizationConfig | undefined;
}

type ChartViewType = "bar" | "pie";

const COLORS = [
  "#7c3a5c", "#5a2a42", "#a855f7", "#3b82f6",
  "#10b981", "#f59e0b", "#ef4444", "#6366f1",
];

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({ config }) => {
  const [chartView, setChartView] = useState<ChartViewType>("bar");

  if (!config) {
    return (
      <div className="visualization-panel empty">
        <div className="empty-state">
          <span className="empty-icon">📊</span>
          <p>Charts will appear here after you ask a question</p>
        </div>
      </div>
    );
  }

  const transformData = () => {
    if (config.series.length === 0) return [];
    const allXValues = new Set<string>();
    config.series.forEach((s) => { s.data.forEach((d) => allXValues.add(String(d.x))); });
    const xValues = Array.from(allXValues).sort();
    return xValues.map((x) => {
      const point: Record<string, unknown> = { name: x };
      config.series.forEach((s) => {
        const dataPoint = s.data.find((d) => String(d.x) === x);
        point[s.name] = dataPoint?.y || 0;
      });
      return point;
    });
  };

  const data = transformData();

  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color: string }>; label?: string }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="tooltip-value" style={{ color: entry.color }}>
              <span className="tooltip-dot" style={{ backgroundColor: entry.color }}></span>
              {entry.name}: <strong>{entry.value.toLocaleString()}</strong>
              {config.yLabel && <span className="tooltip-unit"> {config.yLabel}</span>}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const getPieData = () => {
    if (config.series.length === 0) return [];
    if (config.series.length === 1) {
      return config.series[0].data.map((d, i) => ({ name: String(d.x), value: d.y, fill: COLORS[i % COLORS.length] }));
    }
    return config.series.map((s, i) => ({ name: s.name, value: s.data.reduce((sum, d) => sum + d.y, 0), fill: COLORS[i % COLORS.length] }));
  };

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
        <defs>
          {config.series.map((_, i) => (
            <linearGradient key={`gradient-${i}`} id={`colorBar${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={1}/>
              <stop offset="95%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.6}/>
            </linearGradient>
          ))}
          <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15"/>
          </filter>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4b5563', fontWeight: 500 }} axisLine={{ stroke: '#e5e7eb', strokeWidth: 1 }} tickLine={false} dy={10} />
        <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} tickFormatter={(value) => { if (value >= 1000000) return `${(value/1000000).toFixed(1)}M`; if (value >= 1000) return `${(value/1000).toFixed(0)}k`; return value; }} label={config.yLabel ? { value: config.yLabel, angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280', fontWeight: 500 } } : undefined} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(124, 58, 92, 0.05)' }} />
        <Legend wrapperStyle={{ paddingTop: 15 }} iconType="circle" iconSize={10} formatter={(value) => <span style={{ color: '#374151', fontWeight: 500, fontSize: 13 }}>{value}</span>} />
        {config.series.map((s, i) => (
          <Bar key={s.name} dataKey={s.name} fill={`url(#colorBar${i})`} radius={[8, 8, 0, 0]} maxBarSize={65} style={{ filter: 'url(#shadow)' }} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => {
    const pieData = getPieData();
    const total = pieData.reduce((sum, d) => sum + d.value, 0);

    const renderCustomLabel = (props: any) => {
      const { cx, cy, midAngle, outerRadius, percent, name } = props;
      if (!midAngle || !outerRadius || !percent) return null;
      const RADIAN = Math.PI / 180;
      const radius = outerRadius + 30;
      const x = cx + radius * Math.cos(-midAngle * RADIAN);
      const y = cy + radius * Math.sin(-midAngle * RADIAN);
      if (percent < 0.05) return null;
      return (
        <text x={x} y={y} fill="#374151" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" style={{ fontSize: 12, fontWeight: 500 }}>
          {name} ({(percent * 100).toFixed(0)}%)
        </text>
      );
    };

    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <defs>
            {pieData.map((entry, i) => (
              <linearGradient key={`pieGradient-${i}`} id={`pieColor${i}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={entry.fill} stopOpacity={1}/>
                <stop offset="100%" stopColor={entry.fill} stopOpacity={0.75}/>
              </linearGradient>
            ))}
            <filter id="pieShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodOpacity="0.2"/>
            </filter>
          </defs>
          <Pie data={pieData} cx="50%" cy="50%" labelLine={{ stroke: '#9ca3af', strokeWidth: 1 }} label={renderCustomLabel} innerRadius={60} outerRadius={110} paddingAngle={3} dataKey="value" style={{ filter: 'url(#pieShadow)' }} animationBegin={0} animationDuration={800}>
            {pieData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={`url(#pieColor${index})`} stroke="white" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ backgroundColor: "white", border: "none", borderRadius: "12px", boxShadow: "0 8px 30px rgba(0,0,0,0.12)", padding: "12px 16px" }} formatter={(value: number, name: string) => [
            <span key={name}><strong>{value.toLocaleString()}</strong>{config.yLabel && <span style={{ color: '#6b7280', marginLeft: 4 }}>{config.yLabel}</span>}<span style={{ color: '#9ca3af', marginLeft: 8 }}>({((value / total) * 100).toFixed(1)}%)</span></span>, name
          ]} />
          <text x="50%" y="47%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 24, fontWeight: 700, fill: '#1a1a2e' }}>
            {total >= 1000000 ? `${(total/1000000).toFixed(1)}M` : total >= 1000 ? `${(total/1000).toFixed(0)}k` : total.toLocaleString()}
          </text>
          <text x="50%" y="57%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 11, fill: '#6b7280', fontWeight: 500 }}>
            {config.yLabel || 'Total'}
          </text>
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderChart = () => {
    if (config.chartType === "line") {
      return (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <defs>
              {config.series.map((_, i) => (
                <linearGradient key={`lineGradient-${i}`} id={`lineColor${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.3}/>
                  <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0}/>
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4b5563' }} axisLine={{ stroke: '#e5e7eb' }} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} label={config.yLabel ? { value: config.yLabel, angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280', fontWeight: 500 } } : undefined} />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="circle" />
            {config.series.map((s, i) => (
              <Line key={s.name} type="monotone" dataKey={s.name} stroke={COLORS[i % COLORS.length]} strokeWidth={3} dot={{ fill: COLORS[i % COLORS.length], strokeWidth: 2, r: 4 }} activeDot={{ r: 7, stroke: 'white', strokeWidth: 2 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
    }
    return chartView === "bar" ? renderBarChart() : renderPieChart();
  };

  const showToggle = config.chartType === "bar" || config.chartType === "pie";

  return (
    <div className="visualization-panel">
      <div className="viz-header">
        <h3>{config.title}</h3>
        <div className="viz-controls">
          {showToggle && (
            <div className="chart-toggle">
              <button className={`toggle-btn ${chartView === 'bar' ? 'active' : ''}`} onClick={() => setChartView('bar')} title="Bar Chart">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="8" width="4" height="13" rx="1"/><rect x="17" y="4" width="4" height="17" rx="1"/></svg>
              </button>
              <button className={`toggle-btn ${chartView === 'pie' ? 'active' : ''}`} onClick={() => setChartView('pie')} title="Pie Chart">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v9l6.5 6.5"/></svg>
              </button>
            </div>
          )}
          <span className="chart-type-badge">{chartView === 'pie' ? 'pie' : config.chartType}</span>
        </div>
      </div>
      <div className="viz-content">{renderChart()}</div>
    </div>
  );
};

export default VisualizationPanel;
