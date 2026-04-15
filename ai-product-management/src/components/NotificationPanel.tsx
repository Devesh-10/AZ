import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Bell,
  Check,
  AlertTriangle,
  Sparkles,
  Users,
  Clock,
  FileText,
  TrendingUp,
  CheckCircle2,
} from 'lucide-react';

interface Notification {
  id: string;
  type: 'alert' | 'ai' | 'task' | 'stakeholder' | 'milestone' | 'document';
  title: string;
  description: string;
  time: string;
  read: boolean;
  projectName?: string;
}

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onViewProject?: (id: string) => void;
}

const INITIAL_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    type: 'alert',
    title: 'Supply Chain Predictor at risk',
    description: 'No activity for 3 days. Alignment score dropped to 52%. Recommend stakeholder check-in.',
    time: '10 min ago',
    read: false,
    projectName: 'Supply Chain Predictor',
  },
  {
    id: '2',
    type: 'ai',
    title: 'AI Coach generated risk analysis',
    description: 'Risk assessment completed for SOP Assistant. 3 high-priority risks identified with mitigations.',
    time: '25 min ago',
    read: false,
    projectName: 'SOP Assistant',
  },
  {
    id: '3',
    type: 'stakeholder',
    title: 'Stakeholder review overdue',
    description: 'Stakeholder interview for SOP Assistant was due last week. Recommend rescheduling.',
    time: '1 hour ago',
    read: false,
    projectName: 'SOP Assistant',
  },
  {
    id: '4',
    type: 'milestone',
    title: 'Clinical Trial Dashboard advanced',
    description: 'Phase 3 "Define Value & Outcomes" completed. Now in Phase 4: Create Product Brief.',
    time: '2 hours ago',
    read: true,
    projectName: 'Clinical Trial Dashboard',
  },
  {
    id: '5',
    type: 'task',
    title: 'Task completed: Risk Assessment',
    description: 'Risk Assessment task marked complete for SOP Assistant initiative.',
    time: '3 hours ago',
    read: true,
    projectName: 'SOP Assistant',
  },
  {
    id: '6',
    type: 'document',
    title: 'New document uploaded',
    description: 'SOP-Assistant-Brief-v2.docx uploaded by Lea M. Ready for review.',
    time: '5 hours ago',
    read: true,
    projectName: 'SOP Assistant',
  },
  {
    id: '7',
    type: 'ai',
    title: 'Portfolio health updated',
    description: 'AI recalculated health scores. SOP Assistant: 72%, Clinical Trial Dashboard: 88%.',
    time: 'Yesterday',
    read: true,
  },
  {
    id: '8',
    type: 'milestone',
    title: 'Q2 planning window opens next week',
    description: 'Run the AI Quarterly Planning Playbook to prepare initiative prioritisation.',
    time: 'Yesterday',
    read: true,
  },
];

const iconMap: Record<string, { icon: React.ComponentType<{ className?: string }>, bg: string, color: string }> = {
  alert: { icon: AlertTriangle, bg: 'bg-amber-50', color: 'text-amber-600' },
  ai: { icon: Sparkles, bg: 'bg-purple-50', color: 'text-purple-600' },
  task: { icon: CheckCircle2, bg: 'bg-emerald-50', color: 'text-emerald-600' },
  stakeholder: { icon: Users, bg: 'bg-rose-50', color: 'text-rose-600' },
  milestone: { icon: TrendingUp, bg: 'bg-blue-50', color: 'text-blue-600' },
  document: { icon: FileText, bg: 'bg-gray-50', color: 'text-gray-600' },
};

export default function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const unreadCount = notifications.filter((n) => !n.read).length;
  const filtered = filter === 'unread' ? notifications.filter((n) => !n.read) : notifications;

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const dismissNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40"
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.98 }}
        transition={{ duration: 0.2 }}
        className="fixed top-14 right-24 z-50 w-[420px] max-h-[600px] bg-white rounded-2xl border border-az-border shadow-2xl shadow-black/15 flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-az-border">
          <div className="flex items-center gap-2.5">
            <Bell className="w-4 h-4 text-az-plum" />
            <h3 className="text-sm font-semibold text-az-text">Notifications</h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-az-plum/10 text-az-plum text-[10px] font-bold">
                {unreadCount} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button onClick={markAllRead}
                className="text-[11px] font-medium text-az-plum hover:text-az-plum-light transition-colors">
                Mark all read
              </button>
            )}
            <button onClick={onClose}
              className="w-7 h-7 rounded-lg flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm transition-all">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 px-5 py-2 border-b border-az-border-light">
          {(['all', 'unread'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                ${filter === f ? 'bg-az-plum/8 text-az-plum' : 'text-az-text-tertiary hover:text-az-text-secondary hover:bg-az-surface-warm'}`}
            >
              {f === 'all' ? 'All' : `Unread (${unreadCount})`}
            </button>
          ))}
        </div>

        {/* Notification list */}
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="py-12 text-center">
              <Check className="w-8 h-8 text-az-text-tertiary mx-auto mb-2 opacity-30" />
              <p className="text-sm text-az-text-tertiary">All caught up!</p>
            </div>
          ) : (
            <AnimatePresence>
              {filtered.map((notif) => {
                const { icon: Icon, bg, color } = iconMap[notif.type] || iconMap.ai;
                return (
                  <motion.div
                    key={notif.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                    onClick={() => { markAsRead(notif.id); }}
                    className={`group flex items-start gap-3 px-5 py-3.5 border-b border-az-border-light hover:bg-az-surface-warm/50 cursor-pointer transition-all
                      ${!notif.read ? 'bg-az-plum/[0.02]' : ''}`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${bg}`}>
                      <Icon className={`w-4 h-4 ${color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className={`text-xs font-medium leading-snug ${!notif.read ? 'text-az-text' : 'text-az-text-secondary'}`}>
                          {!notif.read && <span className="inline-block w-1.5 h-1.5 rounded-full bg-az-plum mr-1.5 mb-0.5" />}
                          {notif.title}
                        </h4>
                        <button
                          onClick={(e) => { e.stopPropagation(); dismissNotification(notif.id); }}
                          className="opacity-0 group-hover:opacity-100 w-5 h-5 rounded flex items-center justify-center text-az-text-tertiary hover:text-red-400 transition-all flex-shrink-0"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                      <p className="text-[11px] text-az-text-tertiary mt-0.5 leading-relaxed line-clamp-2">{notif.description}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] text-az-text-tertiary flex items-center gap-1">
                          <Clock className="w-2.5 h-2.5" />{notif.time}
                        </span>
                        {notif.projectName && (
                          <span className="text-[10px] text-az-plum font-medium">{notif.projectName}</span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          )}
        </div>
      </motion.div>
    </>
  );
}
