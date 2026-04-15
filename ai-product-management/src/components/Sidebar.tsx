import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  FolderKanban,
  BookOpen,
  Sparkles,
  Plus,
  ChevronLeft,
  ChevronRight,
  Settings,
  HelpCircle,
  Search,
  BarChart3,
  Zap,
} from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
  onNewProject: () => void;
}

const navItems = [
  { id: 'home', label: 'Home', icon: LayoutDashboard },
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'portfolio', label: 'Portfolio Health', icon: BarChart3 },
  { id: 'playbooks', label: 'AI Playbooks', icon: Zap },
  { id: 'guidance', label: 'Guidance', icon: BookOpen },
  { id: 'ai-assist', label: 'AI Assistant', icon: Sparkles },
];

const bottomItems = [
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'help', label: 'Help & Support', icon: HelpCircle },
];

export default function Sidebar({ activeView, onNavigate, onNewProject }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col border-r border-white/5"
      style={{ background: 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-white/8">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #7c3a5c 0%, #5a2a42 100%)' }}>
          <span className="text-white font-bold text-sm">AZ</span>
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="text-xs font-medium text-white/50 uppercase tracking-wider leading-none">AstraZeneca</div>
              <div className="text-sm font-semibold text-white whitespace-nowrap leading-tight mt-0.5">AI for Product Mgmt</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Search */}
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pt-4"
          >
            <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/6 border border-white/8 text-white/40 text-sm hover:bg-white/10 hover:text-white/60 transition-all">
              <Search className="w-3.5 h-3.5" />
              <span>Search...</span>
              <span className="ml-auto text-xs bg-white/8 px-1.5 py-0.5 rounded font-mono">⌘K</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* New Project Button */}
      <div className="px-4 pt-4 pb-2">
        <button
          onClick={onNewProject}
          style={{ background: 'linear-gradient(135deg, #7c3a5c 0%, #5a2a42 100%)' }}
          className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-sm transition-all
            text-white hover:shadow-lg hover:shadow-[#7c3a5c]/30 active:scale-[0.98]
            ${collapsed ? 'px-2' : 'px-4'}`}
        >
          <Plus className="w-4 h-4" />
          {!collapsed && <span>New Project</span>}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 pt-2">
        <div className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative group
                  ${isActive
                    ? 'bg-white/12 text-white'
                    : 'text-white/50 hover:bg-white/6 hover:text-white/80'
                  }
                  ${collapsed ? 'justify-center' : ''}
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#d4a5c0] rounded-r-full"
                  />
                )}
                <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
                {collapsed && (
                  <div className="absolute left-full ml-2 px-2.5 py-1.5 rounded-md bg-az-plum text-white text-xs font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity shadow-xl z-50">
                    {item.label}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-3 space-y-0.5">
        {bottomItems.map((item) => (
          <button
            key={item.id}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/40 hover:bg-white/6 hover:text-white/60 transition-all ${collapsed ? 'justify-center' : ''}`}
          >
            <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/6 transition-all mt-2"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          {!collapsed && <span className="text-xs">Collapse</span>}
        </button>
      </div>
    </motion.aside>
  );
}
