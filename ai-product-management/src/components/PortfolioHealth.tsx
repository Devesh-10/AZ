import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Clock,
  ChevronRight,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Info,
  ExternalLink,
} from 'lucide-react';

interface PortfolioHealthProps {
  onBack: () => void;
  viewMode: 'pm' | 'executive';
  onViewProject?: (id: string) => void;
}

const portfolioMetrics = [
  { label: 'Active Initiatives', value: '3', change: '+1', trend: 'up', color: '#6C3483' },
  { label: 'On Track', value: '2', change: '0', trend: 'neutral', color: '#148F77' },
  { label: 'At Risk', value: '1', change: '+1', trend: 'down', color: '#C4972F' },
  { label: 'Avg. Completion', value: '46%', change: '+8%', trend: 'up', color: '#2E86C1' },
];

const initiatives = [
  {
    name: 'SOP Assistant',
    health: 'on-track' as const,
    healthScore: 82,
    milestone: 'Define Value & Outcomes',
    milestonePhase: 3,
    totalPhases: 7,
    risks: 1,
    blockers: 0,
    stakeholderAlignment: 85,
    lastUpdate: '2 hours ago',
    aiSummary: 'Progressing well through value definition. URS and Risk Assessment complete. Stakeholder interview pending — recommend scheduling within this week to maintain timeline.',
    aiCitations: ['URS-v2.docx (reviewed Mar 28)', 'Risk Register (updated Mar 30)', 'Sprint velocity: 3 tasks/week'],
    owner: 'Lea M.',
    team: 'Clinical Ops',
  },
  {
    name: 'Clinical Trial Dashboard',
    health: 'on-track' as const,
    healthScore: 91,
    milestone: 'Create Product Brief',
    milestonePhase: 4,
    totalPhases: 7,
    risks: 0,
    blockers: 0,
    stakeholderAlignment: 92,
    lastUpdate: '1 day ago',
    aiSummary: 'Strong progress. Product brief is 80% complete with clear requirements. All stakeholders aligned on scope. Recommend finalising brief by end of week for steering committee review.',
    aiCitations: ['Product Brief v3 (drafted Mar 28)', 'Stakeholder alignment score: 92%', '5/7 tasks completed'],
    owner: 'James T.',
    team: 'R&D Technology',
  },
  {
    name: 'Supply Chain Predictor',
    health: 'at-risk' as const,
    healthScore: 45,
    milestone: 'Capture Opportunity',
    milestonePhase: 1,
    totalPhases: 7,
    risks: 3,
    blockers: 1,
    stakeholderAlignment: 52,
    lastUpdate: '3 days ago',
    aiSummary: 'Flagged at-risk due to: (1) no stakeholder interviews conducted yet, (2) unclear data availability from supply chain systems, (3) competing priority with Q2 compliance deadline. Recommend re-scoping or deferring to Q3.',
    aiCitations: ['No stakeholder inputs recorded', 'Data catalogue: 2/5 required sources unconfirmed', 'Last activity: Mar 27'],
    owner: 'Priya K.',
    team: 'Supply & Manufacturing',
  },
];

const weeklyTrends = [
  { week: 'W9', onTrack: 2, atRisk: 0, blocked: 0 },
  { week: 'W10', onTrack: 2, atRisk: 0, blocked: 0 },
  { week: 'W11', onTrack: 2, atRisk: 1, blocked: 0 },
  { week: 'W12', onTrack: 2, atRisk: 1, blocked: 0 },
  { week: 'W13', onTrack: 2, atRisk: 1, blocked: 0 },
];

const healthColorMap = {
  'on-track': { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-200' },
  'at-risk': { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', border: 'border-amber-200' },
  'blocked': { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500', border: 'border-red-200' },
};

export default function PortfolioHealth({ onBack, viewMode, onViewProject: _onViewProject }: PortfolioHealthProps) {
  const [expandedInitiative, setExpandedInitiative] = useState<string | null>('SOP Assistant');

  return (
    <div className="max-w-6xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-6"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Home
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-az-text">Portfolio Health</h1>
          <p className="text-sm text-az-text-secondary mt-1">
            {viewMode === 'executive'
              ? 'Executive overview of all active initiatives with AI-calculated health scores'
              : 'Detailed health analysis across your product initiatives'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-az-purple/5 border border-az-purple/10">
            <Sparkles className="w-3.5 h-3.5 text-az-purple" />
            <span className="text-xs font-medium text-az-purple">AI-Calculated</span>
          </div>
          <span className="text-xs text-az-text-tertiary">Updated 5 min ago</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {portfolioMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 * index }}
            className="bg-white rounded-xl border border-az-border p-5"
          >
            <div className="flex items-start justify-between">
              <p className="text-xs text-az-text-tertiary font-medium">{metric.label}</p>
              <div className={`flex items-center gap-0.5 text-xs font-medium ${
                metric.trend === 'up' ? 'text-emerald-600' : metric.trend === 'down' ? 'text-amber-600' : 'text-az-text-tertiary'
              }`}>
                {metric.trend === 'up' && <ArrowUpRight className="w-3 h-3" />}
                {metric.trend === 'down' && <ArrowDownRight className="w-3 h-3" />}
                {metric.trend === 'neutral' && <Minus className="w-3 h-3" />}
                {metric.change}
              </div>
            </div>
            <p className="text-3xl font-bold mt-2" style={{ color: metric.color }}>{metric.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Executive AI Summary */}
      {viewMode === 'executive' && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="bg-gradient-to-br from-az-plum/[0.04] to-az-purple/[0.03] rounded-2xl border border-az-plum/10 p-6 mb-8"
        >
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-az-purple" />
            <h3 className="text-sm font-semibold text-az-text">AI Executive Summary</h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-az-purple/8 text-az-purple font-medium">Auto-generated</span>
          </div>
          <p className="text-sm text-az-text-secondary leading-relaxed mb-4">
            Portfolio health is <span className="font-semibold text-emerald-700">stable</span> with 2 of 3 initiatives on track.
            <span className="font-semibold text-amber-700"> Supply Chain Predictor requires attention</span> — stakeholder alignment is low (52%) and no interviews have been conducted.
            Clinical Trial Dashboard is the strongest performer at 91% health. Recommend focusing team capacity on unblocking the Supply Chain initiative or deferring to Q3.
          </p>
          <div className="flex items-start gap-4 pt-3 border-t border-az-plum/8">
            <div className="flex-1">
              <p className="text-[10px] font-semibold text-az-text-tertiary uppercase tracking-wider mb-2">Sources</p>
              <div className="space-y-1">
                {['Project status data (3 initiatives)', 'Milestone completion rates', 'Stakeholder alignment scores', 'Task velocity — last 14 days'].map((src) => (
                  <div key={src} className="flex items-center gap-1.5 text-xs text-az-text-tertiary">
                    <div className="w-1 h-1 rounded-full bg-az-purple/40" />
                    {src}
                  </div>
                ))}
              </div>
            </div>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-az-border text-xs font-medium text-az-text-secondary hover:border-az-purple/20 transition-all">
              <ExternalLink className="w-3 h-3" />
              Share summary
            </button>
          </div>
        </motion.div>
      )}

      {/* Trend Chart (simplified visual) */}
      <div className="bg-white rounded-xl border border-az-border p-6 mb-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-sm font-semibold text-az-text">Health Trend — Last 5 Weeks</h3>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> On Track</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> At Risk</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Blocked</span>
          </div>
        </div>
        <div className="flex items-end gap-3 h-32">
          {weeklyTrends.map((week, i) => {
            const total = week.onTrack + week.atRisk + week.blocked;
            return (
              <motion.div
                key={week.week}
                initial={{ opacity: 0, scaleY: 0 }}
                animate={{ opacity: 1, scaleY: 1 }}
                transition={{ duration: 0.5, delay: 0.1 * i }}
                style={{ transformOrigin: 'bottom' }}
                className="flex-1 flex flex-col items-center gap-1"
              >
                <div className="w-full flex flex-col gap-0.5 h-24">
                  <div className="bg-emerald-400 rounded-t-md flex-1" style={{ flex: week.onTrack / total }} />
                  {week.atRisk > 0 && <div className="bg-amber-400 flex-1" style={{ flex: week.atRisk / total }} />}
                  {week.blocked > 0 && <div className="bg-red-400 rounded-b-md flex-1" style={{ flex: week.blocked / total }} />}
                </div>
                <span className="text-[10px] text-az-text-tertiary font-medium">{week.week}</span>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Initiative Health Cards */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-az-text">Initiative Details</h3>
        {initiatives.map((initiative, index) => {
          const colors = healthColorMap[initiative.health];
          const isExpanded = expandedInitiative === initiative.name;

          return (
            <motion.div
              key={initiative.name}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.05 * index }}
              className="bg-white rounded-xl border border-az-border overflow-hidden"
            >
              {/* Header */}
              <button
                onClick={() => setExpandedInitiative(isExpanded ? null : initiative.name)}
                className="w-full flex items-center gap-4 p-5 text-left hover:bg-az-surface/50 transition-colors"
              >
                {/* Health Score */}
                <div className="relative w-12 h-12 flex-shrink-0">
                  <svg className="w-12 h-12 -rotate-90" viewBox="0 0 48 48">
                    <circle cx="24" cy="24" r="20" fill="none" stroke="#f0ede9" strokeWidth="4" />
                    <circle
                      cx="24" cy="24" r="20" fill="none"
                      stroke={initiative.health === 'on-track' ? '#10b981' : initiative.health === 'at-risk' ? '#f59e0b' : '#ef4444'}
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray={`${(initiative.healthScore / 100) * 125.6} 125.6`}
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-az-text">
                    {initiative.healthScore}
                  </span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-az-text">{initiative.name}</h4>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${colors.bg} ${colors.text}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
                      {initiative.health.replace('-', ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-az-text-tertiary mt-1">
                    Phase {initiative.milestonePhase}/{initiative.totalPhases} · {initiative.milestone} · {initiative.owner}, {initiative.team}
                  </p>
                </div>

                {/* Quick stats */}
                <div className="flex items-center gap-5 text-xs">
                  <div className="text-center">
                    <p className="font-semibold text-az-text">{initiative.risks}</p>
                    <p className="text-az-text-tertiary">Risks</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-az-text">{initiative.blockers}</p>
                    <p className="text-az-text-tertiary">Blockers</p>
                  </div>
                  <div className="text-center">
                    <p className="font-semibold text-az-text">{initiative.stakeholderAlignment}%</p>
                    <p className="text-az-text-tertiary">Alignment</p>
                  </div>
                </div>

                <ChevronRight className={`w-4 h-4 text-az-text-tertiary transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </button>

              {/* Expanded AI Analysis */}
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className="border-t border-az-border"
                >
                  <div className="p-5 bg-az-surface/30">
                    {/* AI Summary */}
                    <div className="flex items-start gap-3 mb-4">
                      <div className="w-7 h-7 rounded-lg bg-az-purple/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Sparkles className="w-3.5 h-3.5 text-az-purple" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="text-xs font-semibold text-az-text">AI Health Analysis</h5>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-az-purple/8 text-az-purple font-medium">Auto-generated</span>
                        </div>
                        <p className="text-sm text-az-text-secondary leading-relaxed">{initiative.aiSummary}</p>
                      </div>
                    </div>

                    {/* Citations */}
                    <div className="ml-10 bg-white rounded-lg border border-az-border p-3">
                      <div className="flex items-center gap-1.5 mb-2">
                        <Info className="w-3 h-3 text-az-text-tertiary" />
                        <span className="text-[10px] font-semibold text-az-text-tertiary uppercase tracking-wider">Evidence Sources</span>
                      </div>
                      <div className="space-y-1">
                        {initiative.aiCitations.map((citation, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-az-text-secondary">
                            <span className="w-4 h-4 rounded bg-az-surface-warm flex items-center justify-center text-[10px] font-mono text-az-text-tertiary flex-shrink-0">
                              {i + 1}
                            </span>
                            {citation}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Updated timestamp */}
                    <div className="flex items-center gap-1.5 mt-3 ml-10 text-[10px] text-az-text-tertiary">
                      <Clock className="w-3 h-3" />
                      Last updated {initiative.lastUpdate}
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
