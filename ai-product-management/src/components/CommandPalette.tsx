import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  FolderPlus,
  FolderKanban,
  BookOpen,
  Sparkles,
  LayoutDashboard,
  FileText,
  Upload,
  ArrowRight,
  BarChart3,
  Users,
  AlertTriangle,
  Lightbulb,
  Target,
  TrendingUp,
  Zap,
  Command,
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (view: string) => void;
  onNewProject: () => void;
}

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'navigation' | 'action' | 'project' | 'ai' | 'playbook';
  action: () => void;
  keywords?: string[];
}

export default function CommandPalette({ isOpen, onClose, onNavigate, onNewProject }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const commands: CommandItem[] = useMemo(() => [
    // Navigation
    { id: 'nav-home', label: 'Go to Home', icon: LayoutDashboard, category: 'navigation', action: () => { onNavigate('home'); onClose(); }, keywords: ['dashboard', 'workspace'] },
    { id: 'nav-projects', label: 'Go to Projects', icon: FolderKanban, category: 'navigation', action: () => { onNavigate('projects'); onClose(); }, keywords: ['initiatives'] },
    { id: 'nav-guidance', label: 'Go to Guidance Library', icon: BookOpen, category: 'navigation', action: () => { onNavigate('guidance'); onClose(); }, keywords: ['templates', 'methods', 'examples'] },
    { id: 'nav-portfolio', label: 'Go to Portfolio Health', icon: BarChart3, category: 'navigation', action: () => { onNavigate('portfolio'); onClose(); }, keywords: ['dashboard', 'health', 'status'] },
    { id: 'nav-playbooks', label: 'Go to AI Playbooks', icon: Zap, category: 'navigation', action: () => { onNavigate('playbooks'); onClose(); }, keywords: ['workflows', 'automation'] },

    // Actions
    { id: 'act-new', label: 'Create New Initiative', description: 'Start a new product initiative', icon: FolderPlus, category: 'action', action: () => { onNewProject(); onClose(); }, keywords: ['project', 'new', 'start'] },
    { id: 'act-upload', label: 'Upload Document', description: 'Upload a brief, transcript, or checklist', icon: Upload, category: 'action', action: () => { onNewProject(); onClose(); }, keywords: ['file', 'document'] },
    { id: 'act-ai', label: 'Open AI Coach', description: 'Get AI assistance', icon: Sparkles, category: 'action', action: () => { onNavigate('ai-assist'); onClose(); }, keywords: ['assistant', 'help', 'copilot'] },

    // Projects
    { id: 'proj-sop', label: 'SOP Assistant', description: 'In Progress · 50% complete', icon: FileText, category: 'project', action: () => { onNavigate('project-workspace'); onClose(); }, keywords: ['sop'] },
    { id: 'proj-clinical', label: 'Clinical Trial Dashboard', description: 'In Progress · 72% complete', icon: BarChart3, category: 'project', action: () => { onNavigate('project-workspace'); onClose(); }, keywords: ['clinical', 'trial'] },
    { id: 'proj-supply', label: 'Supply Chain Predictor', description: 'Planning · 15% complete', icon: TrendingUp, category: 'project', action: () => { onNavigate('project-workspace'); onClose(); }, keywords: ['supply', 'chain'] },

    // AI Commands
    { id: 'ai-brief', label: 'AI: Generate Product Brief', description: 'Auto-generate a brief from your inputs', icon: Sparkles, category: 'ai', action: () => { onClose(); }, keywords: ['generate', 'prd', 'document'] },
    { id: 'ai-risks', label: 'AI: Surface Risks', description: 'Identify risks across active initiatives', icon: AlertTriangle, category: 'ai', action: () => { onClose(); }, keywords: ['risk', 'identify'] },
    { id: 'ai-stakeholders', label: 'AI: Map Stakeholders', description: 'Generate a stakeholder map for your initiative', icon: Users, category: 'ai', action: () => { onClose(); }, keywords: ['stakeholder', 'map'] },
    { id: 'ai-metrics', label: 'AI: Suggest Success Metrics', description: 'Generate KPIs based on initiative context', icon: Target, category: 'ai', action: () => { onClose(); }, keywords: ['kpi', 'metrics', 'success'] },
    { id: 'ai-summarise', label: 'AI: Portfolio Summary', description: 'Generate an executive summary of all initiatives', icon: Lightbulb, category: 'ai', action: () => { onClose(); }, keywords: ['summary', 'executive', 'portfolio'] },

    // Playbooks
    { id: 'pb-quarterly', label: 'Run: Quarterly Planning Playbook', description: '5-step guided planning workflow', icon: Zap, category: 'playbook', action: () => { onNavigate('playbooks'); onClose(); }, keywords: ['quarterly', 'planning'] },
    { id: 'pb-launch', label: 'Run: Initiative Launch Playbook', description: '7-step launch readiness workflow', icon: Zap, category: 'playbook', action: () => { onNavigate('playbooks'); onClose(); }, keywords: ['launch', 'readiness'] },
  ], [onNavigate, onNewProject, onClose]);

  const filtered = useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter(
      (cmd) =>
        cmd.label.toLowerCase().includes(q) ||
        cmd.description?.toLowerCase().includes(q) ||
        cmd.keywords?.some((k) => k.includes(q))
    );
  }, [query, commands]);

  const grouped = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    filtered.forEach((cmd) => {
      if (!groups[cmd.category]) groups[cmd.category] = [];
      groups[cmd.category].push(cmd);
    });
    return groups;
  }, [filtered]);

  const categoryLabels: Record<string, string> = {
    navigation: 'Navigate',
    action: 'Actions',
    project: 'Projects',
    ai: 'AI Commands',
    playbook: 'Playbooks',
  };

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // toggle handled in parent
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      filtered[selectedIndex]?.action();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  let flatIndex = 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm flex items-start justify-center pt-[15vh]"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
          className="w-full max-w-[580px] bg-white rounded-2xl shadow-2xl shadow-black/20 overflow-hidden border border-az-border"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-5 h-14 border-b border-az-border">
            <Search className="w-4.5 h-4.5 text-az-text-tertiary flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search commands, projects, AI actions..."
              className="flex-1 bg-transparent text-sm text-az-text placeholder:text-az-text-tertiary outline-none"
            />
            <kbd className="hidden sm:flex items-center gap-0.5 px-2 py-1 rounded-md bg-az-surface-warm border border-az-border text-[10px] text-az-text-tertiary font-mono">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div ref={listRef} className="max-h-[400px] overflow-y-auto py-2">
            {filtered.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <Search className="w-8 h-8 text-az-text-tertiary mx-auto mb-3 opacity-40" />
                <p className="text-sm text-az-text-secondary">No results for "{query}"</p>
                <p className="text-xs text-az-text-tertiary mt-1">Try a different search term</p>
              </div>
            ) : (
              Object.entries(grouped).map(([category, items]) => (
                <div key={category} className="mb-1">
                  <div className="px-5 py-1.5">
                    <span className="text-[10px] font-semibold text-az-text-tertiary uppercase tracking-wider">
                      {categoryLabels[category] || category}
                    </span>
                  </div>
                  {items.map((cmd) => {
                    const currentIndex = flatIndex++;
                    const isSelected = currentIndex === selectedIndex;
                    return (
                      <button
                        key={cmd.id}
                        onClick={cmd.action}
                        onMouseEnter={() => setSelectedIndex(currentIndex)}
                        className={`w-full flex items-center gap-3 px-5 py-2.5 text-left transition-colors
                          ${isSelected ? 'bg-az-plum/5' : 'hover:bg-az-surface-warm'}`}
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors
                          ${isSelected ? 'bg-az-plum/10 text-az-plum' : 'bg-az-surface-warm text-az-text-secondary'}`}>
                          <cmd.icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${isSelected ? 'text-az-plum' : 'text-az-text'}`}>
                            {cmd.label}
                          </p>
                          {cmd.description && (
                            <p className="text-xs text-az-text-tertiary truncate">{cmd.description}</p>
                          )}
                        </div>
                        {isSelected && (
                          <div className="flex items-center gap-1 text-az-text-tertiary">
                            <ArrowRight className="w-3 h-3" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-5 py-2.5 border-t border-az-border bg-az-surface/50">
            <div className="flex items-center gap-3 text-[10px] text-az-text-tertiary">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-az-surface-warm border border-az-border font-mono">↑↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-az-surface-warm border border-az-border font-mono">↵</kbd>
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 rounded bg-az-surface-warm border border-az-border font-mono">esc</kbd>
                Close
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-az-text-tertiary">
              <Command className="w-3 h-3" />
              <span>Powered by AI</span>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
