import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb,
  Target,
  TrendingUp,
  FileText,
  BarChart3,
  Calendar,
  Rocket,
  Check,
  Circle,
  ChevronRight,
  X,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Clock,
  Copy,
} from 'lucide-react';
import type { Milestone } from '../data/store';

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Lightbulb, Target, TrendingUp, FileText, BarChart3, Calendar, Rocket,
};

interface MilestoneJourneyProps {
  milestones: Milestone[];
  onToggleTask: (milestoneId: string, taskIndex: number) => void;
  onOpenAiWithPrompt: (prompt: string) => void;
}

export default function MilestoneJourney({ milestones, onToggleTask, onOpenAiWithPrompt }: MilestoneJourneyProps) {
  const [selectedMilestone, setSelectedMilestone] = useState<string | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  const selected = milestones.find((m) => m.id === selectedMilestone);

  // Calculate progress percentage for the rail
  const completedCount = milestones.filter((m) => m.status === 'completed').length;
  const activeIndex = milestones.findIndex((m) => m.status === 'active');
  const progressPercent = activeIndex >= 0
    ? ((activeIndex + 0.5) / milestones.length) * 100
    : (completedCount / milestones.length) * 100;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-az-text">Your Journey</h2>
          <p className="text-sm text-az-text-tertiary mt-0.5">From opportunity to launch — 7 guided milestones. Click any phase to explore.</p>
        </div>
        <button
          onClick={() => setSelectedMilestone(selectedMilestone ? null : milestones[0]?.id)}
          className="text-sm font-medium text-az-purple hover:text-az-purple-light transition-colors flex items-center gap-1"
        >
          {selectedMilestone ? 'Collapse' : 'View all milestones'}
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Journey Rail */}
      <div className="relative">
        <div className="absolute top-[30px] left-[30px] right-[30px] h-[3px] bg-az-border rounded-full">
          <motion.div
            initial={{ width: '0%' }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 1.2, delay: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #7c3a5c, #9b4d73)' }}
          />
        </div>

        <div className="grid grid-cols-7 gap-2 relative">
          {milestones.map((milestone, index) => {
            const Icon = iconMap[milestone.icon] || Circle;
            const isCompleted = milestone.status === 'completed';
            const isActive = milestone.status === 'active';
            const isSelected = selectedMilestone === milestone.id;
            const completedTasks = milestone.tasks.filter(t => t.completed).length;

            return (
              <motion.button
                key={milestone.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 * index }}
                onClick={() => setSelectedMilestone(isSelected ? null : milestone.id)}
                className={`group flex flex-col items-center text-center rounded-xl py-2 transition-all duration-200 cursor-pointer
                  ${isSelected ? 'bg-az-plum/[0.04] ring-1 ring-az-plum/10' : 'hover:bg-az-surface-warm'}`}
              >
                <div className={`relative z-10 w-[60px] h-[60px] rounded-2xl flex items-center justify-center transition-all duration-300
                  ${isCompleted
                    ? 'bg-az-plum text-white shadow-md'
                    : isActive
                      ? 'bg-white border-2 border-az-plum text-az-plum shadow-lg shadow-az-plum/10'
                      : 'bg-white border border-az-border text-az-text-tertiary group-hover:border-az-purple/30 group-hover:shadow-md'
                  }
                  ${isSelected && !isCompleted && !isActive ? 'border-az-purple/40 shadow-md' : ''}`}
                >
                  {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  {isActive && (
                    <motion.div
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="absolute -top-1 -right-1 w-3 h-3 bg-az-plum rounded-full border-2 border-white"
                    />
                  )}
                </div>

                <div className={`mt-3 text-[10px] font-semibold uppercase tracking-wider
                  ${isCompleted ? 'text-az-plum' : isActive ? 'text-az-plum-light' : 'text-az-text-tertiary'}`}>
                  Phase {milestone.phase}
                </div>

                <div className={`mt-1 text-xs font-medium leading-snug px-1 line-clamp-2
                  ${isCompleted || isActive ? 'text-az-text' : 'text-az-text-secondary'}`}>
                  {milestone.title}
                </div>

                <div className="mt-2 flex items-center gap-1">
                  {milestone.tasks.map((_, i) => (
                    <div
                      key={i}
                      className={`w-1.5 h-1.5 rounded-full transition-colors
                        ${i < completedTasks ? (isCompleted ? 'bg-az-plum' : 'bg-az-plum-light') : 'bg-az-border'}`}
                    />
                  ))}
                  <span className="text-[10px] text-az-text-tertiary ml-1">{completedTasks}/{milestone.tasks.length}</span>
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Expanded Milestone Detail Panel */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-6 bg-white rounded-2xl border border-az-border shadow-sm overflow-hidden">
              {/* Top accent */}
              <div className="relative">
                <div className="absolute top-0 left-0 right-0 h-1" style={{ background: `linear-gradient(90deg, ${selected.color}, ${selected.color}88)` }} />
                <div className="px-6 pt-5 pb-4 flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: `${selected.color}12` }}>
                      {(() => { const MIcon = iconMap[selected.icon] || Circle; return <MIcon className="w-5 h-5" />; })()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: selected.color }}>Phase {selected.phase}</span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase
                          ${selected.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : selected.status === 'active' ? 'bg-amber-50 text-amber-700' : 'bg-gray-50 text-gray-500'}`}>
                          {selected.status === 'completed' && <Check className="w-2.5 h-2.5" />}
                          {selected.status === 'active' && <Clock className="w-2.5 h-2.5" />}
                          {selected.status === 'completed' ? 'Completed' : selected.status === 'active' ? 'In Progress' : 'Upcoming'}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-az-text mt-1">{selected.title}</h3>
                      <p className="text-sm text-az-text-secondary mt-1">{selected.description}</p>
                    </div>
                  </div>
                  <button onClick={() => setSelectedMilestone(null)}
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm hover:text-az-text-secondary transition-all">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Content grid */}
              <div className="grid grid-cols-[1fr_1fr] gap-0 border-t border-az-border">
                {/* Tasks — fully interactive */}
                <div className="p-6 border-r border-az-border">
                  <h4 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider mb-4">Tasks</h4>
                  <div className="space-y-2.5">
                    {selected.tasks.map((task, i) => (
                      <motion.button
                        key={i}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.25, delay: 0.05 * i }}
                        onClick={() => onToggleTask(selected.id, i)}
                        className="group w-full flex items-start gap-3 p-3 rounded-xl border border-az-border hover:border-az-purple/15 hover:shadow-sm transition-all cursor-pointer text-left"
                      >
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all
                          ${task.completed ? 'border-emerald-500 bg-emerald-50' : 'border-az-border group-hover:border-az-purple/30'}`}>
                          {task.completed && <Check className="w-3 h-3 text-emerald-600" />}
                        </div>
                        <div className="flex-1">
                          <p className={`text-sm font-medium ${task.completed ? 'text-az-text-secondary line-through' : 'text-az-text'}`}>
                            {task.title}
                          </p>
                          <p className="text-[10px] text-az-text-tertiary mt-0.5">
                            {task.completed ? 'Click to unmark' : 'Click to mark complete'}
                          </p>
                        </div>
                        {!task.completed && (
                          <span className="opacity-0 group-hover:opacity-100 text-xs font-medium text-az-purple flex items-center gap-0.5 transition-opacity mt-0.5">
                            Done <Check className="w-3 h-3" />
                          </span>
                        )}
                      </motion.button>
                    ))}
                  </div>

                  {/* Progress bar */}
                  <div className="mt-4 flex items-center gap-3">
                    <div className="flex-1 h-2 bg-az-surface-warm rounded-full overflow-hidden">
                      <motion.div
                        key={selected.tasks.filter(t => t.completed).length}
                        initial={{ width: 0 }}
                        animate={{ width: `${(selected.tasks.filter(t => t.completed).length / selected.tasks.length) * 100}%` }}
                        transition={{ duration: 0.4, ease: 'easeOut' }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: selected.color }}
                      />
                    </div>
                    <span className="text-xs font-medium text-az-text-secondary">
                      {selected.tasks.filter(t => t.completed).length}/{selected.tasks.length} done
                    </span>
                  </div>
                </div>

                {/* AI Guidance — all buttons functional */}
                <div className="p-6">
                  <h4 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider mb-4">AI Guidance</h4>

                  <div className="bg-gradient-to-br from-az-plum/[0.04] to-az-purple/[0.04] rounded-xl border border-az-plum/10 p-4 mb-4">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg bg-az-purple/10 flex items-center justify-center flex-shrink-0">
                        <Sparkles className="w-3.5 h-3.5 text-az-purple" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-az-text">How AI can help</p>
                        <p className="text-xs text-az-text-secondary mt-1 leading-relaxed">{selected.aiHint}</p>
                      </div>
                    </div>
                  </div>

                  {/* Quick AI Actions — all clickable */}
                  <div className="space-y-2">
                    <h5 className="text-[10px] font-semibold text-az-text-tertiary uppercase tracking-wider">Quick Actions</h5>
                    {[
                      { label: `Draft ${selected.title.toLowerCase()} summary`, prompt: `Please draft a summary for the "${selected.title}" phase of my SOP Assistant initiative. ${selected.aiHint}`, icon: FileText },
                      { label: `Suggest next steps for Phase ${selected.phase}`, prompt: `What are the recommended next steps for Phase ${selected.phase} (${selected.title})? Consider the current task completion and suggest priorities.`, icon: ArrowRight },
                      { label: 'Identify risks at this stage', prompt: `Identify the key risks at the "${selected.title}" phase for my SOP Assistant initiative. Include likelihood, impact, and mitigation suggestions.`, icon: Target },
                    ].map((action, i) => (
                      <button
                        key={i}
                        onClick={() => onOpenAiWithPrompt(action.prompt)}
                        className="w-full flex items-center gap-2.5 p-3 rounded-xl border border-az-border text-left hover:border-az-purple/20 hover:bg-az-purple/[0.02] transition-all group"
                      >
                        <action.icon className="w-4 h-4 text-az-text-tertiary group-hover:text-az-purple transition-colors" />
                        <span className="text-xs font-medium text-az-text-secondary group-hover:text-az-text transition-colors">{action.label}</span>
                        <Sparkles className="w-3 h-3 text-az-text-tertiary opacity-0 group-hover:opacity-100 ml-auto transition-opacity" />
                      </button>
                    ))}
                  </div>

                  {/* Example prompt — copyable */}
                  <div className="mt-4 bg-az-surface-warm rounded-xl border border-az-border-light p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold text-az-crimson uppercase tracking-wider">Example Prompt</span>
                      <button
                        onClick={() => handleCopy(`Help me with the "${selected.title}" phase. ${selected.aiHint}`)}
                        className="flex items-center gap-1 px-2 py-1 rounded-md bg-white border border-az-border text-[10px] font-medium text-az-text-secondary hover:border-az-purple/20 transition-all"
                      >
                        {copiedPrompt ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                        {copiedPrompt ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <p className="text-xs text-az-text-secondary leading-relaxed italic">
                      "Help me with the "{selected.title}" phase. {selected.aiHint}"
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-az-border bg-az-surface/30 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-az-text-tertiary">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {selected.status === 'completed'
                    ? 'This phase is complete. Review outputs anytime.'
                    : selected.status === 'active'
                      ? 'This phase is active. Complete all tasks to advance.'
                      : 'Complete the previous phase to unlock this one.'}
                </div>
                <button
                  onClick={() => onOpenAiWithPrompt(`Help me with the "${selected.title}" phase. ${selected.aiHint}`)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-az-plum text-white text-xs font-semibold hover:bg-az-plum-light transition-colors"
                >
                  <Sparkles className="w-3 h-3" />
                  Get AI Help
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
