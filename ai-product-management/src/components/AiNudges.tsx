import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  X,
  AlertTriangle,
  Target,
  Users,
  ArrowRight,
  Lightbulb,
  TrendingUp,
} from 'lucide-react';

interface Nudge {
  id: string;
  type: 'warning' | 'suggestion' | 'insight' | 'action';
  title: string;
  description: string;
  actionLabel: string;
  actionType: 'viewProject' | 'aiPrompt' | 'navigate';
  actionPayload: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  citation?: string;
  priority: 'high' | 'medium' | 'low';
}

interface AiNudgesProps {
  onViewProject: (id: string) => void;
  onOpenAiWithPrompt: (prompt: string) => void;
  onNavigate: (view: string) => void;
}

const nudges: Nudge[] = [
  {
    id: '1',
    type: 'warning',
    title: 'Supply Chain Predictor needs attention',
    description: 'No stakeholder interviews conducted. Alignment score dropped to 52%. At risk of stalling.',
    actionLabel: 'View initiative',
    actionType: 'viewProject',
    actionPayload: '3',
    icon: AlertTriangle,
    color: '#C4972F',
    citation: 'Based on: 0 stakeholder inputs, 3-day inactivity, alignment trend',
    priority: 'high',
  },
  {
    id: '2',
    type: 'suggestion',
    title: '3 initiatives missing success metrics',
    description: 'Define KPIs before progressing past the "Define Value" milestone. AI can suggest metrics.',
    actionLabel: 'Generate metrics',
    actionType: 'aiPrompt',
    actionPayload: 'Suggest success metrics and KPIs for my active initiatives. Include adoption metrics, efficiency metrics, and quality metrics for each.',
    icon: Target,
    color: '#6C3483',
    citation: 'Based on: milestone requirements check across active projects',
    priority: 'high',
  },
  {
    id: '3',
    type: 'insight',
    title: 'Clinical Trial Dashboard is your fastest initiative',
    description: 'Averaging 1.2 tasks/day — 40% faster than your portfolio average. Consider applying its patterns.',
    actionLabel: 'View details',
    actionType: 'viewProject',
    actionPayload: '2',
    icon: TrendingUp,
    color: '#148F77',
    citation: 'Based on: task completion velocity over 14 days',
    priority: 'medium',
  },
  {
    id: '4',
    type: 'action',
    title: 'Stakeholder review overdue for SOP Assistant',
    description: 'Stakeholder interview was scheduled for last week. Recommend rescheduling.',
    actionLabel: 'Schedule now',
    actionType: 'aiPrompt',
    actionPayload: 'Generate 15 structured interview questions for a stakeholder interview about the SOP Assistant initiative. Cover: current processes, pain points, desired outcomes, success criteria, and integration constraints.',
    icon: Users,
    color: '#8B1A3A',
    citation: 'Based on: project timeline, task due dates',
    priority: 'medium',
  },
  {
    id: '5',
    type: 'suggestion',
    title: 'Quarterly planning playbook available',
    description: 'Q2 planning window opens next week. Run the AI Quarterly Planning Playbook to prepare.',
    actionLabel: 'Open playbook',
    actionType: 'navigate',
    actionPayload: 'playbooks',
    icon: Lightbulb,
    color: '#2E86C1',
    priority: 'low',
  },
];

const priorityBorder = {
  high: 'border-l-amber-500',
  medium: 'border-l-az-purple',
  low: 'border-l-az-border',
};

export default function AiNudges({ onViewProject, onOpenAiWithPrompt, onNavigate }: AiNudgesProps) {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [isExpanded, setIsExpanded] = useState(true);

  const visibleNudges = nudges.filter((n) => !dismissedIds.has(n.id));
  const highPriority = visibleNudges.filter((n) => n.priority === 'high');
  const otherNudges = visibleNudges.filter((n) => n.priority !== 'high');

  const handleDismiss = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDismissedIds((prev) => new Set([...prev, id]));
  };

  const handleAction = (nudge: Nudge) => {
    switch (nudge.actionType) {
      case 'viewProject':
        onViewProject(nudge.actionPayload);
        break;
      case 'aiPrompt':
        onOpenAiWithPrompt(nudge.actionPayload);
        break;
      case 'navigate':
        onNavigate(nudge.actionPayload);
        break;
    }
  };

  if (visibleNudges.length === 0) return null;

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-az-text">AI Insights</h2>
            <p className="text-xs text-az-text-tertiary">{visibleNudges.length} recommendations based on your portfolio data</p>
          </div>
        </div>
        <button onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs font-medium text-az-text-tertiary hover:text-az-text-secondary transition-colors">
          {isExpanded ? 'Collapse' : `Show ${visibleNudges.length} insights`}
        </button>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }} className="space-y-2.5 overflow-hidden">

            {highPriority.map((nudge, index) => (
              <motion.div
                key={nudge.id}
                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10, height: 0 }}
                transition={{ duration: 0.3, delay: 0.05 * index }}
                onClick={() => handleAction(nudge)}
                className={`group relative bg-white rounded-xl border border-az-border border-l-[3px] ${priorityBorder[nudge.priority]} overflow-hidden hover:shadow-md transition-all cursor-pointer`}
              >
                <div className="flex items-start gap-3.5 p-4">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                    style={{ backgroundColor: `${nudge.color}10` }}>
                    <nudge.icon className="w-4 h-4" style={{ color: nudge.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium text-az-text">{nudge.title}</h4>
                      <button onClick={(e) => handleDismiss(nudge.id, e)}
                        className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-md flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm hover:text-az-text-secondary transition-all flex-shrink-0">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                    <p className="text-xs text-az-text-secondary mt-0.5 leading-relaxed">{nudge.description}</p>
                    <div className="flex items-center justify-between mt-2.5">
                      <span className="flex items-center gap-1 text-xs font-medium text-az-purple group-hover:text-az-purple-light transition-colors">
                        {nudge.actionLabel}
                        <ArrowRight className="w-3 h-3" />
                      </span>
                      {nudge.citation && (
                        <span className="text-[10px] text-az-text-tertiary italic">{nudge.citation}</span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}

            {otherNudges.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {otherNudges.map((nudge, index) => (
                  <motion.div
                    key={nudge.id}
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.3, delay: 0.05 * index }}
                    onClick={() => handleAction(nudge)}
                    className={`group relative bg-white rounded-xl border border-az-border border-l-[3px] ${priorityBorder[nudge.priority]} p-3.5 hover:shadow-md transition-all cursor-pointer`}
                  >
                    <button onClick={(e) => handleDismiss(nudge.id, e)}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 w-5 h-5 rounded flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm transition-all">
                      <X className="w-2.5 h-2.5" />
                    </button>
                    <div className="flex items-start gap-2.5">
                      <nudge.icon className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: nudge.color }} />
                      <div>
                        <h4 className="text-xs font-medium text-az-text leading-snug">{nudge.title}</h4>
                        <p className="text-[11px] text-az-text-tertiary mt-1 leading-relaxed line-clamp-2">{nudge.description}</p>
                        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-az-purple mt-1.5">
                          {nudge.actionLabel} <ArrowRight className="w-2.5 h-2.5" />
                        </span>
                        {nudge.citation && (
                          <p className="text-[9px] text-az-text-tertiary mt-1 italic">{nudge.citation}</p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
