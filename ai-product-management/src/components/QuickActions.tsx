import { motion } from 'framer-motion';
import {
  Upload,
  FolderPlus,
  ArrowRight,
  Sparkles,
  LayoutTemplate,
} from 'lucide-react';

interface QuickActionsProps {
  onNewProject: () => void;
  onBrowseGuidance: () => void;
  onViewProjects: () => void;
  onOpenAiCoach?: () => void;
}

const actions = [
  {
    id: 'new',
    title: 'New Initiative',
    description: 'Start a new product initiative with AI-guided setup.',
    icon: FolderPlus,
    gradient: 'from-[#7c3a5c] to-[#5a2a42]',
    shadowColor: 'shadow-[#7c3a5c]/15',
    action: 'onNewProject',
  },
  {
    id: 'upload',
    title: 'Upload & Capture',
    description: 'Upload an idea, brief, or checklist to get started.',
    icon: Upload,
    gradient: 'from-[#1a1a2e] to-[#16213e]',
    shadowColor: 'shadow-[#1a1a2e]/15',
    action: 'onNewProject',
  },
  {
    id: 'templates',
    title: 'Browse Templates',
    description: 'Use proven templates for briefs, URS, and more.',
    icon: LayoutTemplate,
    gradient: 'from-az-purple to-az-purple-light',
    shadowColor: 'shadow-az-purple/15',
    action: 'onBrowseGuidance',
  },
  {
    id: 'ai',
    title: 'AI Quick Assist',
    description: 'Ask AI to refine, generate, or review your work.',
    icon: Sparkles,
    gradient: 'from-az-teal to-az-teal-light',
    shadowColor: 'shadow-az-teal/15',
    action: 'onOpenAiCoach',
  },
];

export default function QuickActions({ onNewProject, onBrowseGuidance, onOpenAiCoach }: QuickActionsProps) {
  const handlers: Record<string, () => void> = {
    onNewProject,
    onBrowseGuidance,
    onViewProjects: onBrowseGuidance,
    onOpenAiCoach: onOpenAiCoach || onBrowseGuidance,
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-semibold text-az-text">Quick Actions</h2>
          <p className="text-sm text-az-text-tertiary mt-0.5">Start faster, structure better</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {actions.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 * index }}
            whileHover={{ y: -3 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handlers[item.action]?.()}
            className={`group relative bg-white rounded-xl border border-az-border p-5 text-left
              hover:shadow-lg ${item.shadowColor} hover:border-transparent transition-all duration-300 overflow-hidden`}
          >
            {/* Hover gradient background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-[0.03] transition-opacity duration-300`} />

            <div className="relative z-10">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.gradient} flex items-center justify-center mb-3 shadow-sm`}>
                <item.icon className="w-5 h-5 text-white" />
              </div>

              <h3 className="text-sm font-semibold text-az-text">{item.title}</h3>
              <p className="mt-1 text-xs text-az-text-tertiary leading-relaxed">{item.description}</p>

              <div className="mt-3 flex items-center gap-1 text-xs font-medium text-az-purple opacity-0 group-hover:opacity-100 transition-all translate-x-0 group-hover:translate-x-1">
                Get started <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </section>
  );
}
