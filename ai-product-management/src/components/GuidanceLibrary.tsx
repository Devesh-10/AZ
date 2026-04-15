import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  AlertTriangle,
  Users,
  Compass,
  Layout,
  Calculator,
  ArrowLeft,
  ChevronRight,
  Sparkles,
  Copy,
  Check,
  Search,
} from 'lucide-react';
import { GUIDANCE_ITEMS } from '../data/constants';

const iconMap: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  FileText,
  AlertTriangle,
  Users,
  Compass,
  Layout,
  Calculator,
};

interface GuidanceLibraryProps {
  onBack?: () => void;
  onOpenAiWithPrompt?: (prompt: string) => void;
}

export default function GuidanceLibrary({ onBack, onOpenAiWithPrompt }: GuidanceLibraryProps) {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState('All');

  const selected = GUIDANCE_ITEMS.find((i) => i.id === selectedItem);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const categories = ['All', 'PM Task', 'Template', 'Method'];

  if (selected) {
    const Icon = iconMap[selected.icon] || FileText;

    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="max-w-3xl mx-auto"
      >
        <button
          onClick={() => setSelectedItem(null)}
          className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-6"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Guidance
        </button>

        {/* Header */}
        <div className="flex items-start gap-4 mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: `${selected.color}15` }}
          >
            <Icon className="w-6 h-6" style={{ color: selected.color }} />
          </div>
          <div>
            <span className="text-xs font-semibold text-az-purple uppercase tracking-wider">{selected.category}</span>
            <h1 className="text-2xl font-bold text-az-text mt-1">{selected.title}</h1>
            <p className="text-sm text-az-text-secondary mt-2 leading-relaxed">{selected.description}</p>
          </div>
        </div>

        {/* How to use AI */}
        <div className="mb-8">
          <h2 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider mb-4">How to Use AI</h2>
          <div className="grid grid-cols-2 gap-4">
            {selected.steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 * index }}
                className="bg-white rounded-xl border border-az-border p-5"
              >
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-full bg-az-plum flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-white">{index + 1}</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-az-text">{step.title}</h4>
                    <p className="text-xs text-az-text-secondary mt-1.5 leading-relaxed">{step.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Example prompt */}
        <div className="bg-gradient-to-br from-az-plum/5 to-az-plum/10 rounded-2xl border border-az-plum/15 p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-az-plum" />
              <h3 className="text-xs font-bold text-az-plum uppercase tracking-wider">Example AI Prompt</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onOpenAiWithPrompt?.(selected.examplePrompt)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-az-plum text-white text-xs font-semibold hover:bg-az-plum-light transition-all"
              >
                <Sparkles className="w-3 h-3" />
                Try with AI
              </button>
              <button
                onClick={() => handleCopy(selected.examplePrompt)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/60 border border-az-plum/20 text-xs font-medium text-az-text-secondary hover:bg-white transition-all"
              >
                {copied ? <Check className="w-3 h-3 text-az-teal" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copied!' : 'Copy prompt'}
              </button>
            </div>
          </div>
          <p className="text-sm text-az-text leading-relaxed italic">
            "{selected.examplePrompt}"
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-4"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Home
            </button>
          )}
          <h1 className="text-2xl font-bold text-az-text">Find Information</h1>
          <p className="text-sm text-az-text-secondary mt-1">
            Practical AI guidance for each stage of product management at AstraZeneca. Click on a section to explore step-by-step guides, example prompts, and best practices.
          </p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-az-text-tertiary" />
          <input
            type="text"
            placeholder="Search guidance..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-az-border bg-white text-sm text-az-text placeholder:text-az-text-tertiary focus:border-az-purple/30 focus:ring-2 focus:ring-az-purple/10 outline-none transition-all"
          />
        </div>
        <div className="flex items-center gap-1 bg-az-surface-warm rounded-xl p-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${filter === cat
                  ? 'bg-white text-az-text shadow-sm'
                  : 'text-az-text-tertiary hover:text-az-text-secondary'
                }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {GUIDANCE_ITEMS
          .filter((item) => filter === 'All' || item.category === filter)
          .map((item, index) => {
            const Icon = iconMap[item.icon] || FileText;
            return (
              <motion.button
                key={item.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.05 * index }}
                whileHover={{ y: -3 }}
                onClick={() => setSelectedItem(item.id)}
                className="group bg-white rounded-xl border border-az-border hover:border-transparent hover:shadow-lg text-left p-6 transition-all duration-300 overflow-hidden relative"
              >
                {/* Hover gradient */}
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-[0.04] transition-opacity"
                  style={{ background: `linear-gradient(135deg, ${item.color}, transparent)` }}
                />

                <div className="relative z-10">
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center mb-4"
                    style={{ backgroundColor: `${item.color}12` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: item.color }} />
                  </div>

                  <span className="text-[10px] font-semibold text-az-purple uppercase tracking-wider">{item.category}</span>
                  <h3 className="text-base font-semibold text-az-text mt-1 group-hover:text-az-plum transition-colors">{item.title}</h3>
                  <p className="text-xs text-az-text-tertiary mt-2 leading-relaxed line-clamp-3">{item.description}</p>

                  <div className="mt-4 flex items-center gap-1 text-xs font-medium text-az-purple opacity-0 group-hover:opacity-100 transition-opacity">
                    Explore guide
                    <ChevronRight className="w-3 h-3" />
                  </div>
                </div>
              </motion.button>
            );
          })}
      </div>
    </div>
  );
}
