import { useState, useCallback } from 'react';
import { MILESTONES as INITIAL_MILESTONES, PROJECTS as INITIAL_PROJECTS, PROJECT_MILESTONES } from './constants';

// ─── Types ───────────────────────────────────────────────────────

export interface Task {
  title: string;
  completed: boolean;
}

export interface Milestone {
  id: string;
  phase: number;
  title: string;
  description: string;
  status: 'completed' | 'active' | 'upcoming';
  tasks: Task[];
  aiHint: string;
  icon: string;
  color: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: 'in_progress' | 'planning';
  progress: number;
  completedTasks: number;
  totalTasks: number;
  currentMilestone: string;
  lastUpdated: string;
  color: string;
}

export interface AiMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: string[];
}

export interface AppState {
  milestones: Milestone[];
  projects: Project[];
  aiMessages: AiMessage[];
  activeProjectId: string | null;
  aiCoachContext: string;
}

// ─── Hook ────────────────────────────────────────────────────────

export function useAppState() {
  const [milestones, setMilestones] = useState<Milestone[]>(
    JSON.parse(JSON.stringify(INITIAL_MILESTONES))
  );
  const [projects, setProjects] = useState<Project[]>(
    JSON.parse(JSON.stringify(INITIAL_PROJECTS))
  );
  const [projectMilestones, setProjectMilestones] = useState<Record<string, Milestone[]>>(
    JSON.parse(JSON.stringify(PROJECT_MILESTONES))
  );
  const [aiMessages, setAiMessages] = useState<AiMessage[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [aiCoachContext, setAiCoachContext] = useState('');
  const [notification, setNotification] = useState<string | null>(null);

  // ─── Get milestones for a project ────────
  const getMilestonesForProject = useCallback((projectId: string): Milestone[] => {
    return projectMilestones[projectId] || milestones;
  }, [projectMilestones, milestones]);

  // ─── Milestone Actions ────────────────────

  const toggleMilestoneTask = useCallback((milestoneId: string, taskIndex: number, projectId?: string) => {
    const updateMilestones = (prev: Milestone[]) => {
      const updated = prev.map((m) => {
        if (m.id !== milestoneId) return m;
        const newTasks = m.tasks.map((t, i) =>
          i === taskIndex ? { ...t, completed: !t.completed } : t
        );
        const completedCount = newTasks.filter((t) => t.completed).length;
        const allDone = completedCount === newTasks.length;

        let newStatus = m.status;
        if (allDone && m.status === 'active') {
          newStatus = 'completed';
        } else if (completedCount > 0 && m.status === 'upcoming') {
          newStatus = 'active';
        }

        return { ...m, tasks: newTasks, status: newStatus };
      });

      // Auto-activate next milestone
      for (let i = 0; i < updated.length; i++) {
        if (updated[i].status === 'completed' && i + 1 < updated.length && updated[i + 1].status === 'upcoming') {
          if (updated[i].tasks.every((t) => t.completed)) {
            updated[i + 1] = { ...updated[i + 1], status: 'active' };
          }
        }
      }

      return updated;
    };

    if (projectId && projectMilestones[projectId]) {
      setProjectMilestones((prev) => {
        const updated = updateMilestones(prev[projectId] || []);
        // Also update the project's progress
        const allTasks = updated.flatMap((m) => m.tasks);
        const completed = allTasks.filter((t) => t.completed).length;
        const activeMilestone = updated.find((m) => m.status === 'active');

        setProjects((prevProjects) =>
          prevProjects.map((p) => {
            if (p.id !== projectId) return p;
            return {
              ...p,
              completedTasks: completed,
              totalTasks: allTasks.length,
              progress: Math.round((completed / allTasks.length) * 100),
              currentMilestone: activeMilestone?.title || p.currentMilestone,
              lastUpdated: 'Just now',
            };
          })
        );

        return { ...prev, [projectId]: updated };
      });
    } else {
      setMilestones(updateMilestones);
    }
  }, [projectMilestones]);

  // ─── Project Actions ──────────────────────

  const createProject = useCallback((name: string, description: string, _category: string) => {
    const id = String(Date.now());
    const newProject: Project = {
      id,
      name,
      description,
      status: 'planning',
      progress: 0,
      completedTasks: 0,
      totalTasks: 21,
      currentMilestone: 'Capture Opportunity',
      lastUpdated: 'Just now',
      color: ['#6C3483', '#8B1A3A', '#148F77', '#C4972F', '#2E86C1'][Math.floor(Math.random() * 5)],
    };
    setProjects((prev) => [newProject, ...prev]);

    // Create fresh milestones for this project
    const freshMilestones: Milestone[] = JSON.parse(JSON.stringify(INITIAL_MILESTONES)).map(
      (m: Milestone, i: number) => ({
        ...m,
        status: i === 0 ? 'active' as const : 'upcoming' as const,
        tasks: m.tasks.map((t: Task) => ({ ...t, completed: false })),
      })
    );
    setProjectMilestones((prev) => ({ ...prev, [id]: freshMilestones }));

    showNotification(`Project "${name}" created successfully`);
    return id;
  }, []);

  // ─── AI Coach Actions ─────────────────────

  const sendAiMessage = useCallback((content: string) => {
    const userMsg: AiMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setAiMessages((prev) => [...prev, userMsg]);

    // Call Claude API via backend
    (async () => {
      try {
        const allMessages = [...aiMessages, userMsg];
        const apiMessages = allMessages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: apiMessages }),
        });

        if (!res.ok) {
          throw new Error(`API error: ${res.status}`);
        }

        const data = await res.json();

        const aiMsg: AiMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: data.content,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setAiMessages((prev) => [...prev, aiMsg]);
      } catch (error) {
        const errorMsg: AiMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error connecting to the AI service. Please check that the backend server is running and the API key is configured.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setAiMessages((prev) => [...prev, errorMsg]);
      }
    })();
  }, [aiMessages]);

  const openAiCoachWithPrompt = useCallback((prompt: string) => {
    setAiCoachContext(prompt);
  }, []);

  // ─── Notifications ────────────────────────

  const showNotification = useCallback((message: string) => {
    setNotification(message);
    setTimeout(() => setNotification(null), 3000);
  }, []);

  // ─── Project workspace task toggle ────────

  const toggleProjectTask = useCallback((projectId: string, _taskIndex: number, tasks: { title: string; completed: boolean }[]) => {
    setProjects((prev) =>
      prev.map((p) => {
        if (p.id !== projectId) return p;
        const newCompleted = tasks.filter((t) => t.completed).length;
        const newTotal = tasks.length;
        return {
          ...p,
          completedTasks: newCompleted,
          totalTasks: newTotal,
          progress: Math.round((newCompleted / newTotal) * 100),
          lastUpdated: 'Just now',
        };
      })
    );
  }, []);

  return {
    milestones,
    projects,
    projectMilestones,
    aiMessages,
    activeProjectId,
    aiCoachContext,
    notification,
    setActiveProjectId,
    toggleMilestoneTask,
    getMilestonesForProject,
    createProject,
    sendAiMessage,
    openAiCoachWithPrompt,
    showNotification,
    toggleProjectTask,
    setAiCoachContext,
  };
}

export type AppStore = ReturnType<typeof useAppState>;
