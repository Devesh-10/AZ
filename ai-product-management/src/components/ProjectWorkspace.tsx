import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Check,
  Circle,
  Clock,
  FileText,
  MoreHorizontal,
  Paperclip,
  Plus,
  Sparkles,
  Users,
  AlertTriangle,
  ChevronRight,
  BarChart3,
  Send,
  HelpCircle,
  Pencil,
  Trash2,
  X,
} from 'lucide-react';
import type { AppStore } from '../data/store';

interface ProjectWorkspaceProps {
  store: AppStore;
  onBack: () => void;
  onOpenAiWithPrompt: (prompt: string) => void;
}

interface WorkspaceTask {
  id: string;
  title: string;
  description: string;
  completed: boolean;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
}

interface Stage {
  id: string;
  title: string;
  status: 'completed' | 'active' | 'upcoming';
}

const documents = [
  { name: 'SOP-Assistant-Brief-v2.docx', type: 'Word', updated: '2 hours ago', size: '245 KB' },
  { name: 'Stakeholder-Interview-Notes.pdf', type: 'PDF', updated: '1 day ago', size: '1.2 MB' },
  { name: 'Requirements-Draft.xlsx', type: 'Excel', updated: '3 days ago', size: '89 KB' },
];

const timeline = [
  { date: 'Today', items: [
    { text: 'Risk Assessment marked as complete', time: '2:30 PM', type: 'completed' },
    { text: 'AI generated 3 risk mitigation suggestions', time: '2:15 PM', type: 'ai' },
  ]},
  { date: 'Yesterday', items: [
    { text: 'URS document uploaded and reviewed', time: '4:45 PM', type: 'document' },
    { text: 'Stakeholder interview scheduled with Clinical Ops', time: '11:00 AM', type: 'action' },
  ]},
  { date: 'Mar 27', items: [
    { text: 'Project created from template', time: '9:30 AM', type: 'created' },
    { text: 'AI generated initial milestone plan', time: '9:31 AM', type: 'ai' },
  ]},
];

const TASK_ICONS = [FileText, AlertTriangle, Users, Sparkles, BarChart3, Clock];
const TASK_COLORS = ['#8B1A3A', '#C4972F', '#6C3483', '#2E86C1', '#148F77', '#E74C3C'];

export default function ProjectWorkspace({ store, onBack, onOpenAiWithPrompt }: ProjectWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<'tasks' | 'documents' | 'timeline'>('tasks');
  const [coachMessage, setCoachMessage] = useState('');
  const [tasks, setTasks] = useState<WorkspaceTask[]>([
    { id: '1', title: 'User Requirements Specification', description: 'A URS formally documents what users need from a system before development begins.', completed: true, icon: FileText, color: '#8B1A3A' },
    { id: '2', title: 'Risk Assessment', description: 'A Risk Assessment identifies potential threats to project success, evaluates their likelihood and impact.', completed: true, icon: AlertTriangle, color: '#C4972F' },
    { id: '3', title: 'Stakeholder Interview', description: 'Stakeholder interviews are structured conversations to understand user needs, pain points, and expectations.', completed: false, icon: Users, color: '#6C3483' },
    { id: '4', title: 'Vision for a New Initiative', description: 'A Vision statement describes the desired future state — what success looks like and why it matters.', completed: false, icon: Sparkles, color: '#2E86C1' },
  ]);

  const projectMilestones = store.getMilestonesForProject(store.activeProjectId || '1');

  const [stages, setStages] = useState<Stage[]>(() =>
    projectMilestones.map((m) => ({
      id: m.id,
      title: m.title,
      status: m.status,
    }))
  );

  // Re-sync when project changes
  useEffect(() => {
    const pm = store.getMilestonesForProject(store.activeProjectId || '1');
    setStages(pm.map((m) => ({
      id: m.id,
      title: m.title,
      status: m.status,
    })));

    // Set tasks from the active milestone
    const activeMilestone = pm.find((m) => m.status === 'active');
    if (activeMilestone) {
      setTasks(activeMilestone.tasks.map((t, i) => ({
        id: `${store.activeProjectId}-task-${i}`,
        title: t.title,
        description: `Task for ${activeMilestone.title} phase.`,
        completed: t.completed,
        icon: TASK_ICONS[i % TASK_ICONS.length],
        color: TASK_COLORS[i % TASK_COLORS.length],
      })));
    }
  }, [store.activeProjectId]);

  // Editing states
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [editingStageId, setEditingStageId] = useState<string | null>(null);
  const [editStageName, setEditStageName] = useState('');
  const [showAddStage, setShowAddStage] = useState(false);
  const [newStageName, setNewStageName] = useState('');
  const [, setTaskMenuId] = useState<string | null>(null);

  const addTaskInputRef = useRef<HTMLInputElement>(null);

  const project = store.projects.find((p) => p.id === store.activeProjectId) || store.projects[0];
  const completedTaskCount = tasks.filter((t) => t.completed).length;
  const progress = Math.round((completedTaskCount / tasks.length) * 100);

  const toggleTask = (taskId: string) => {
    setTasks((prev) =>
      prev.map((t) => t.id === taskId ? { ...t, completed: !t.completed } : t)
    );
    store.showNotification(
      tasks.find((t) => t.id === taskId)?.completed
        ? 'Task unmarked'
        : 'Task completed!'
    );
  };

  const startEditTask = (task: WorkspaceTask) => {
    setEditingTaskId(task.id);
    setEditTitle(task.title);
    setEditDesc(task.description);
    setTaskMenuId(null);
  };

  const saveEditTask = () => {
    if (!editTitle.trim()) return;
    setTasks((prev) =>
      prev.map((t) => t.id === editingTaskId ? { ...t, title: editTitle.trim(), description: editDesc.trim() } : t)
    );
    setEditingTaskId(null);
    store.showNotification('Task updated');
  };

  const deleteTask = (taskId: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    setTaskMenuId(null);
    store.showNotification('Task removed');
  };

  const addTask = () => {
    if (!newTaskTitle.trim()) return;
    const iconIndex = tasks.length % TASK_ICONS.length;
    const newTask: WorkspaceTask = {
      id: String(Date.now()),
      title: newTaskTitle.trim(),
      description: newTaskDesc.trim() || 'Custom task added to the project.',
      completed: false,
      icon: TASK_ICONS[iconIndex],
      color: TASK_COLORS[iconIndex],
    };
    setTasks((prev) => [...prev, newTask]);
    setNewTaskTitle('');
    setNewTaskDesc('');
    setShowAddTask(false);
    store.showNotification(`Task "${newTask.title}" added`);
  };

  const startEditStage = (stage: Stage) => {
    setEditingStageId(stage.id);
    setEditStageName(stage.title);
  };

  const saveEditStage = () => {
    if (!editStageName.trim()) return;
    setStages((prev) =>
      prev.map((s) => s.id === editingStageId ? { ...s, title: editStageName.trim() } : s)
    );
    setEditingStageId(null);
    store.showNotification('Stage renamed');
  };

  const addStage = () => {
    if (!newStageName.trim()) return;
    const newStage: Stage = {
      id: `stage-${Date.now()}`,
      title: newStageName.trim(),
      status: 'upcoming',
    };
    setStages((prev) => [...prev, newStage]);
    setNewStageName('');
    setShowAddStage(false);
    store.showNotification(`Stage "${newStage.title}" added`);
  };

  const deleteStage = (stageId: string) => {
    setStages((prev) => prev.filter((s) => s.id !== stageId));
    store.showNotification('Stage removed');
  };

  const cycleStageStatus = (stageId: string) => {
    setStages((prev) =>
      prev.map((s) => {
        if (s.id !== stageId) return s;
        const next = s.status === 'upcoming' ? 'active' : s.status === 'active' ? 'completed' : 'upcoming';
        return { ...s, status: next };
      })
    );
  };

  const handleAiHelp = (taskTitle: string) => {
    onOpenAiWithPrompt(`Help me with the "${taskTitle}" task for my ${project?.name || 'SOP Assistant'} initiative. Provide step-by-step guidance, example prompts, and best practices.`);
  };

  const handleCoachSend = () => {
    if (!coachMessage.trim()) return;
    onOpenAiWithPrompt(coachMessage);
    setCoachMessage('');
  };

  return (
    <div className="min-h-screen bg-az-surface">
      {/* Project Header */}
      <div className="bg-white border-b border-az-border">
        <div className="px-8 py-5">
          <button onClick={onBack}
            className="flex items-center gap-2 text-sm text-az-text-secondary hover:text-az-plum transition-colors mb-4">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Projects
          </button>

          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl font-bold text-az-text">{project?.name || 'SOP Assistant'}</h1>
                <span className="px-2.5 py-1 rounded-lg bg-az-plum/8 text-az-plum text-xs font-semibold uppercase tracking-wider">
                  {project?.status === 'in_progress' ? 'In Progress' : 'Planning'}
                </span>
              </div>
              <p className="text-sm text-az-text-secondary max-w-2xl">{project?.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-4 py-2 rounded-lg border border-az-border text-sm font-medium text-az-text-secondary hover:bg-az-surface-warm transition-all">
                <Users className="w-4 h-4 inline mr-2" />Share
              </button>
              <button className="w-9 h-9 rounded-lg border border-az-border flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm transition-all">
                <MoreHorizontal className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-5 flex items-center gap-4">
            <span className="text-xs text-az-text-tertiary whitespace-nowrap">Overall progress</span>
            <div className="flex-1 h-2 bg-az-surface-warm rounded-full overflow-hidden">
              <motion.div
                key={completedTaskCount}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="h-full rounded-full"
                style={{ background: 'linear-gradient(90deg, #7c3a5c, #9b4d73)' }}
              />
            </div>
            <span className="text-sm font-semibold text-az-text">{completedTaskCount} / {tasks.length} tasks</span>
          </div>
        </div>

        {/* Editable milestone rail */}
        <div className="px-8 pb-4">
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {stages.map((s, i) => (
              <div key={s.id} className="flex items-center group/stage">
                {editingStageId === s.id ? (
                  <div className="flex items-center gap-1">
                    <input
                      autoFocus
                      value={editStageName}
                      onChange={(e) => setEditStageName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') saveEditStage(); if (e.key === 'Escape') setEditingStageId(null); }}
                      className="px-2 py-1 rounded-full text-xs border border-az-plum/30 bg-white outline-none w-36"
                    />
                    <button onClick={saveEditStage} className="w-5 h-5 rounded-full bg-az-plum/10 flex items-center justify-center text-az-plum hover:bg-az-plum/20">
                      <Check className="w-3 h-3" />
                    </button>
                    <button onClick={() => setEditingStageId(null)} className="w-5 h-5 rounded-full bg-red-50 flex items-center justify-center text-red-400 hover:bg-red-100">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <div
                    className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs whitespace-nowrap cursor-pointer
                      ${s.status === 'completed' ? 'bg-az-plum/8 text-az-plum font-medium' : s.status === 'active' ? 'bg-az-plum/10 text-az-plum-light font-semibold ring-1 ring-az-plum/20' : 'bg-az-surface-warm text-az-text-tertiary'}`}
                    onClick={() => cycleStageStatus(s.id)}
                  >
                    {s.status === 'completed' && <Check className="w-3 h-3" />}
                    {s.status === 'active' && <Circle className="w-2.5 h-2.5 fill-current" />}
                    {s.title}
                    <div className="hidden group-hover/stage:flex items-center gap-0.5 ml-1">
                      <button onClick={(e) => { e.stopPropagation(); startEditStage(s); }}
                        className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-black/5">
                        <Pencil className="w-2.5 h-2.5" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); deleteStage(s.id); }}
                        className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-red-50 text-red-400">
                        <X className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                )}
                {i < stages.length - 1 && <ChevronRight className="w-3 h-3 text-az-text-tertiary mx-1 flex-shrink-0" />}
              </div>
            ))}
            {showAddStage ? (
              <div className="flex items-center gap-1 ml-1">
                <input
                  autoFocus
                  value={newStageName}
                  onChange={(e) => setNewStageName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') addStage(); if (e.key === 'Escape') setShowAddStage(false); }}
                  placeholder="Stage name..."
                  className="px-2 py-1 rounded-full text-xs border border-az-plum/30 bg-white outline-none w-32"
                />
                <button onClick={addStage} className="w-5 h-5 rounded-full bg-az-plum/10 flex items-center justify-center text-az-plum hover:bg-az-plum/20">
                  <Check className="w-3 h-3" />
                </button>
                <button onClick={() => setShowAddStage(false)} className="w-5 h-5 rounded-full bg-red-50 flex items-center justify-center text-red-400 hover:bg-red-100">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <button onClick={() => setShowAddStage(true)}
                className="flex items-center gap-1 ml-1 px-2 py-1 rounded-full text-xs text-az-text-tertiary hover:text-az-plum hover:bg-az-plum/5 transition-all">
                <Plus className="w-3 h-3" /> Add Stage
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-[1fr_340px] gap-0 min-h-[calc(100vh-220px)]">
        {/* Left: Workspace */}
        <div className="p-8">
          <div className="flex items-center gap-1 mb-6 bg-az-surface-warm rounded-xl p-1 w-fit">
            {([
              { id: 'tasks' as const, label: 'AI Task Checklist', icon: Check },
              { id: 'documents' as const, label: 'Documents', icon: FileText },
              { id: 'timeline' as const, label: 'Activity', icon: Clock },
            ]).map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${activeTab === tab.id ? 'bg-white text-az-text shadow-sm' : 'text-az-text-tertiary hover:text-az-text-secondary'}`}>
                <tab.icon className="w-3.5 h-3.5" />{tab.label}
              </button>
            ))}
          </div>

          {/* Tasks */}
          {activeTab === 'tasks' && (
            <div className="space-y-3">
              <p className="text-xs text-az-text-tertiary mb-2">Click a task to toggle completion. Hover for edit/delete. Use <HelpCircle className="w-3 h-3 inline" /> for AI guidance.</p>

              <AnimatePresence>
                {tasks.map((task, index) => (
                  <motion.div key={task.id}
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20, height: 0 }}
                    transition={{ duration: 0.3, delay: 0.05 * index }}
                    className="group bg-white rounded-xl border border-az-border hover:border-az-purple/15 hover:shadow-md transition-all p-5">

                    {editingTaskId === task.id ? (
                      /* Edit mode */
                      <div className="space-y-3">
                        <input
                          autoFocus
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter') saveEditTask(); if (e.key === 'Escape') setEditingTaskId(null); }}
                          className="w-full px-3 py-2 rounded-lg border border-az-border text-sm font-semibold text-az-text outline-none focus:border-az-plum/30"
                          placeholder="Task title"
                        />
                        <textarea
                          value={editDesc}
                          onChange={(e) => setEditDesc(e.target.value)}
                          rows={2}
                          className="w-full px-3 py-2 rounded-lg border border-az-border text-xs text-az-text-secondary outline-none focus:border-az-plum/30 resize-none"
                          placeholder="Task description"
                        />
                        <div className="flex items-center gap-2">
                          <button onClick={saveEditTask}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium text-white"
                            style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
                            Save
                          </button>
                          <button onClick={() => setEditingTaskId(null)}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium text-az-text-secondary border border-az-border hover:bg-az-surface-warm">
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* View mode */
                      <div className="flex items-start gap-4">
                        <button onClick={() => toggleTask(task.id)}
                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-all cursor-pointer
                            ${task.completed ? 'border-az-plum bg-az-plum/10 hover:border-az-plum-light' : 'border-az-border hover:border-az-purple/30'}`}>
                          {task.completed && <Check className="w-3.5 h-3.5 text-az-plum" />}
                        </button>
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: `${task.color}12` }}>
                          <task.icon className="w-4 h-4" style={{ color: task.color }} />
                        </div>
                        <div className="flex-1 min-w-0 cursor-pointer" onClick={() => toggleTask(task.id)}>
                          <h4 className={`text-sm font-semibold ${task.completed ? 'text-az-text-secondary line-through' : 'text-az-text'}`}>{task.title}</h4>
                          <p className="text-xs text-az-text-tertiary mt-1 leading-relaxed line-clamp-2">{task.description}</p>
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => startEditTask(task)}
                            className="w-7 h-7 rounded-full flex items-center justify-center text-az-text-tertiary hover:text-az-plum hover:bg-az-plum/5 transition-all"
                            title="Edit task">
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => deleteTask(task.id)}
                            className="w-7 h-7 rounded-full flex items-center justify-center text-az-text-tertiary hover:text-red-500 hover:bg-red-50 transition-all"
                            title="Delete task">
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => handleAiHelp(task.title)}
                            className="w-7 h-7 rounded-full flex items-center justify-center text-az-text-tertiary hover:text-az-purple hover:bg-az-purple/5 transition-all"
                            title="AI guidance">
                            <HelpCircle className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Add task */}
              <AnimatePresence>
                {showAddTask ? (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                    className="bg-white rounded-xl border border-az-plum/20 shadow-md p-5 space-y-3">
                    <input
                      ref={addTaskInputRef}
                      autoFocus
                      value={newTaskTitle}
                      onChange={(e) => setNewTaskTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter' && newTaskTitle.trim()) addTask(); if (e.key === 'Escape') setShowAddTask(false); }}
                      className="w-full px-3 py-2 rounded-lg border border-az-border text-sm font-semibold text-az-text outline-none focus:border-az-plum/30"
                      placeholder="Task title (e.g., Compliance Review)"
                    />
                    <textarea
                      value={newTaskDesc}
                      onChange={(e) => setNewTaskDesc(e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 rounded-lg border border-az-border text-xs text-az-text-secondary outline-none focus:border-az-plum/30 resize-none"
                      placeholder="Brief description (optional)"
                    />
                    <div className="flex items-center gap-2">
                      <button onClick={addTask} disabled={!newTaskTitle.trim()}
                        className="px-4 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-40"
                        style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
                        Add Task
                      </button>
                      <button onClick={() => { setShowAddTask(false); setNewTaskTitle(''); setNewTaskDesc(''); }}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-az-text-secondary border border-az-border hover:bg-az-surface-warm">
                        Cancel
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.button
                    onClick={() => setShowAddTask(true)}
                    className="flex items-center gap-2 px-4 py-3 rounded-xl border border-dashed border-az-border text-sm text-az-text-tertiary hover:border-az-purple/20 hover:text-az-purple transition-all w-full">
                    <Plus className="w-4 h-4" />Add custom task
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Documents */}
          {activeTab === 'documents' && (
            <div className="space-y-3">
              {documents.map((doc, index) => (
                <motion.div key={doc.name}
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.05 * index }}
                  className="group flex items-center gap-4 bg-white rounded-xl border border-az-border hover:border-az-purple/15 hover:shadow-md p-4 cursor-pointer transition-all">
                  <div className="w-10 h-10 rounded-lg bg-az-surface-warm flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-az-text-secondary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-az-text truncate">{doc.name}</p>
                    <p className="text-xs text-az-text-tertiary mt-0.5">{doc.type} &middot; {doc.size} &middot; Updated {doc.updated}</p>
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 text-az-text-tertiary hover:text-az-text-secondary p-1.5 rounded-lg hover:bg-az-surface-warm transition-all">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
              <div className="border-2 border-dashed border-az-border rounded-xl p-8 text-center hover:border-az-purple/20 transition-colors cursor-pointer">
                <Paperclip className="w-6 h-6 text-az-text-tertiary mx-auto mb-2" />
                <p className="text-sm text-az-text-secondary">Drop files here or click to upload</p>
                <p className="text-xs text-az-text-tertiary mt-1">PDF, DOCX, PPTX, XLSX</p>
              </div>
            </div>
          )}

          {/* Timeline */}
          {activeTab === 'timeline' && (
            <div className="space-y-6">
              {timeline.map((group) => (
                <div key={group.date}>
                  <h4 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider mb-3">{group.date}</h4>
                  <div className="space-y-2">
                    {group.items.map((item, i) => (
                      <motion.div key={i}
                        initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: 0.05 * i }}
                        className="flex items-start gap-3 bg-white rounded-xl border border-az-border p-4">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5
                          ${item.type === 'ai' ? 'bg-az-purple/10' : item.type === 'completed' ? 'bg-az-teal/10' : 'bg-az-surface-warm'}`}>
                          {item.type === 'ai' ? <Sparkles className="w-3 h-3 text-az-purple" /> : item.type === 'completed' ? <Check className="w-3 h-3 text-az-teal" /> : <Circle className="w-3 h-3 text-az-text-tertiary" />}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-az-text">{item.text}</p>
                          <p className="text-xs text-az-text-tertiary mt-0.5">{item.time}</p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: AI Coach Panel */}
        <div className="border-l border-az-border bg-white flex flex-col">
          <div className="flex items-center gap-2.5 px-5 h-16 border-b border-az-border flex-shrink-0">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-az-text">AI Coach</h3>
              <span className="text-[10px] text-az-plum font-medium">Active on this project</span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            <div className="bg-az-surface-warm rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-az-plum" />
                <span className="text-xs font-semibold text-az-text">Current Focus</span>
              </div>
              <p className="text-xs text-az-text-secondary leading-relaxed">
                You're in <span className="font-medium text-az-text">{stages.find(s => s.status === 'active')?.title || 'Define Value & Outcomes'}</span>.
                {' '}{completedTaskCount}/{tasks.length} tasks done.
                {completedTaskCount < tasks.length
                  ? ` Next: complete ${tasks.find((t) => !t.completed)?.title}.`
                  : ' All tasks complete!'}
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider">Recommendations</h4>
              {[
                { title: 'Draft interview questions', desc: 'Generate structured questions for the Stakeholder Interview task.', prompt: 'Generate 15 structured interview questions for a stakeholder on the SOP Assistant project. Cover: current processes, pain points, desired outcomes, success criteria, and integration constraints.' },
                { title: 'Review similar SOPs', desc: 'AI found 3 similar SOP initiatives with learnings to apply.', prompt: 'Review similar SOP initiatives at AstraZeneca and summarise key learnings, common pitfalls, and success factors I should apply to my SOP Assistant project.' },
                { title: 'Risk: no success metrics', desc: 'Define KPIs before moving to the Product Brief phase.', prompt: 'Suggest success metrics and KPIs for the SOP Assistant initiative. Include adoption metrics, efficiency metrics, and quality metrics.' },
              ].map((item, i) => (
                <button key={i} onClick={() => onOpenAiWithPrompt(item.prompt)}
                  className="w-full bg-white rounded-xl border border-az-border hover:border-az-purple/15 p-3.5 cursor-pointer hover:shadow-sm transition-all group text-left">
                  <h5 className="text-xs font-medium text-az-text group-hover:text-az-plum transition-colors">{item.title}</h5>
                  <p className="text-[11px] text-az-text-tertiary mt-1 leading-relaxed">{item.desc}</p>
                </button>
              ))}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {['Generate URS', 'Draft vision', 'List risks', 'Suggest KPIs'].map((p) => (
                <button key={p}
                  onClick={() => onOpenAiWithPrompt(`${p} for my ${project?.name || 'SOP Assistant'} initiative. Provide detailed, actionable output.`)}
                  className="px-2.5 py-1 rounded-full bg-az-surface-warm border border-az-border-light text-[11px] text-az-text-secondary hover:border-az-purple/20 hover:text-az-purple transition-all">
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 border-t border-az-border">
            <div className="flex items-center gap-2 bg-az-surface-warm rounded-xl border border-az-border-light p-1 focus-within:border-az-purple/30 transition-all">
              <input type="text" value={coachMessage} onChange={(e) => setCoachMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCoachSend()}
                placeholder="Ask about this project..."
                className="flex-1 bg-transparent px-3 py-2 text-xs text-az-text placeholder:text-az-text-tertiary outline-none" />
              <button onClick={handleCoachSend}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-white transition-colors flex-shrink-0 disabled:opacity-40"
                style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}
                disabled={!coachMessage.trim()}>
                <Send className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
