import { motion } from 'framer-motion';
import {
  ChevronRight,
  Clock,
  MoreHorizontal,
  ArrowUpRight,
} from 'lucide-react';
import type { Project } from '../data/store';

interface ProjectCardsProps {
  projects: Project[];
  onViewProject?: (id: string) => void;
  onViewAll?: () => void;
  getMilestonesForProject?: (id: string) => { status: string; title: string }[];
}

export default function ProjectCards({ projects, onViewProject, onViewAll, getMilestonesForProject }: ProjectCardsProps) {
  return (
    <section>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-lg font-semibold text-az-text">Active Projects</h2>
          <p className="text-sm text-az-text-tertiary mt-0.5">Your current initiatives and their progress</p>
        </div>
        <button
          onClick={onViewAll}
          className="text-sm font-medium text-az-purple hover:text-az-purple-light transition-colors flex items-center gap-1"
        >
          View all
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {projects.map((project, index) => (
          <motion.div
            key={project.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 * index }}
            onClick={() => onViewProject?.(project.id)}
            className="group relative bg-white rounded-xl border border-az-border hover:border-az-purple/20 hover:shadow-lg hover:shadow-az-purple/5 transition-all duration-300 cursor-pointer overflow-hidden"
          >
            {/* Top accent bar */}
            <div
              className="h-1 w-full"
              style={{ background: `linear-gradient(90deg, ${project.color}, ${project.color}88)` }}
            />

            <div className="p-5">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider
                    ${project.status === 'in_progress'
                      ? 'bg-az-purple/8 text-az-purple'
                      : 'bg-az-teal/8 text-az-teal'
                    }`}>
                    {project.status === 'in_progress' ? 'In Progress' : 'Planning'}
                  </span>
                </div>
                <button className="opacity-0 group-hover:opacity-100 transition-opacity text-az-text-tertiary hover:text-az-text-secondary p-1 rounded-md hover:bg-az-surface-warm">
                  <MoreHorizontal className="w-4 h-4" />
                </button>
              </div>

              {/* Title & Description */}
              <h3 className="text-base font-semibold text-az-text group-hover:text-az-plum transition-colors">
                {project.name}
              </h3>
              <p className="mt-1.5 text-sm text-az-text-secondary leading-relaxed line-clamp-2">
                {project.description}
              </p>

              {/* Current Milestone */}
              <div className="mt-4 flex items-center gap-2 text-xs text-az-text-tertiary">
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: project.color }} />
                <span>{getMilestonesForProject?.(project.id)?.find(m => m.status === 'active')?.title || project.currentMilestone}</span>
              </div>

              {/* Progress */}
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-az-text-tertiary">
                    {project.completedTasks} of {project.totalTasks} tasks
                  </span>
                  <span className="text-xs font-medium text-az-text-secondary">{project.progress}%</span>
                </div>
                <div className="h-1.5 bg-az-surface-warm rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${project.progress}%` }}
                    transition={{ duration: 0.8, delay: 0.3 + 0.1 * index, ease: 'easeOut' }}
                    className="h-full rounded-full"
                    style={{ background: `linear-gradient(90deg, ${project.color}, ${project.color}cc)` }}
                  />
                </div>
              </div>

              {/* Footer */}
              <div className="mt-4 pt-3 border-t border-az-border-light flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-az-text-tertiary">
                  <Clock className="w-3 h-3" />
                  <span>{project.lastUpdated}</span>
                </div>
                <div className="flex items-center gap-1 text-xs font-medium text-az-purple opacity-0 group-hover:opacity-100 transition-opacity">
                  Open
                  <ArrowUpRight className="w-3 h-3" />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
