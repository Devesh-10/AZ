import { useState } from 'react';
import { motion } from 'framer-motion';
import HeroSection from '../components/HeroSection';
import MilestoneJourney from '../components/MilestoneJourney';
import ProjectCards from '../components/ProjectCards';
import QuickActions from '../components/QuickActions';
import AiNudges from '../components/AiNudges';
import type { AppStore } from '../data/store';

interface HomePageProps {
  store: AppStore;
  onNewProject: () => void;
  onBrowseGuidance: () => void;
  onViewProjects: () => void;
  onViewProject: (id: string) => void;
  onOpenAiWithPrompt: (prompt: string) => void;
  onNavigate: (view: string) => void;
}

export default function HomePage({
  store,
  onNewProject,
  onBrowseGuidance,
  onViewProjects,
  onViewProject,
  onOpenAiWithPrompt,
  onNavigate,
}: HomePageProps) {
  const [selectedProjectId, setSelectedProjectId] = useState(store.projects[0]?.id || '1');
  const selectedMilestones = store.getMilestonesForProject(selectedProjectId);

  return (
    <div className="space-y-8 pb-12">
      <HeroSection onNewProject={onNewProject} onBrowseGuidance={onBrowseGuidance} />

      <AiNudges
        onViewProject={onViewProject}
        onOpenAiWithPrompt={onOpenAiWithPrompt}
        onNavigate={onNavigate}
      />

      <QuickActions
        onNewProject={onNewProject}
        onBrowseGuidance={onBrowseGuidance}
        onViewProjects={onViewProjects}
        onOpenAiCoach={() => onOpenAiWithPrompt('How can I accelerate my current initiatives?')}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="bg-white rounded-2xl border border-az-border p-6"
      >
        {/* Project selector for journey */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider">Showing journey for:</span>
          <div className="flex gap-1.5">
            {store.projects.map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedProjectId(p.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                  ${selectedProjectId === p.id
                    ? 'text-white shadow-sm'
                    : 'bg-az-surface-warm text-az-text-secondary hover:bg-az-surface border border-az-border'
                  }`}
                style={selectedProjectId === p.id ? { background: `linear-gradient(135deg, ${p.color}, ${p.color}cc)` } : undefined}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        <MilestoneJourney
          milestones={selectedMilestones}
          onToggleTask={(milestoneId, taskIndex) => store.toggleMilestoneTask(milestoneId, taskIndex, selectedProjectId)}
          onOpenAiWithPrompt={onOpenAiWithPrompt}
        />
      </motion.div>

      <ProjectCards
        projects={store.projects}
        onViewProject={onViewProject}
        onViewAll={onViewProjects}
        getMilestonesForProject={store.getMilestonesForProject}
      />

      <div className="pt-4 pb-2 text-center">
        <p className="text-xs text-az-text-tertiary">
          AstraZeneca — AI for Product Management — Internal Use Only
        </p>
      </div>
    </div>
  );
}
