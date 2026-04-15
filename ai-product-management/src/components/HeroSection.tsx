import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, BookOpen, FolderPlus } from 'lucide-react';

interface HeroSectionProps {
  onNewProject: () => void;
  onBrowseGuidance: () => void;
}

export default function HeroSection({ onNewProject, onBrowseGuidance }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden rounded-2xl mx-0"
      style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%)' }}>
      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
          backgroundSize: '32px 32px',
        }}
      />
      {/* Gradient orbs for depth */}
      <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full blur-[100px]" style={{ background: 'rgba(124, 58, 92, 0.15)' }} />
      <div className="absolute -bottom-10 -left-10 w-60 h-60 rounded-full blur-[80px]" style={{ background: 'rgba(139, 92, 246, 0.1)' }} />

      <div className="relative z-10 px-10 py-12 md:py-14">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          className="max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/10 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-[#d4a5c0]" />
            <span className="text-xs font-medium text-white/70">AI-Powered Product Management</span>
          </div>

          <h1 className="text-3xl md:text-[40px] font-bold text-white leading-[1.15] tracking-tight">
            Move from idea to execution
            <br />
            <span className="text-[#d4a5c0]">with confidence.</span>
          </h1>

          <p className="mt-4 text-base text-white/60 leading-relaxed max-w-lg">
            Your structured companion for every stage of product development —
            from capturing opportunities to launch readiness.
          </p>

          <div className="flex flex-wrap gap-3 mt-8">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onNewProject}
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl text-white font-semibold text-sm shadow-lg hover:shadow-xl transition-shadow"
              style={{ background: 'linear-gradient(135deg, #7c3a5c 0%, #5a2a42 100%)', boxShadow: '0 4px 12px rgba(124, 58, 92, 0.3)' }}
            >
              <FolderPlus className="w-4 h-4" />
              Start a New Initiative
              <ArrowRight className="w-4 h-4" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onBrowseGuidance}
              className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-white/10 border border-white/15 text-white font-medium text-sm hover:bg-white/15 transition-all"
            >
              <BookOpen className="w-4 h-4" />
              Explore Guidance
            </motion.button>
          </div>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex gap-10 mt-10 pt-8 border-t border-white/10"
        >
          {[
            { value: '3', label: 'Active projects' },
            { value: '7', label: 'Milestones tracked' },
            { value: '12', label: 'Tasks in progress' },
            { value: '24', label: 'AI assists this week' },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-white/40 mt-0.5">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
