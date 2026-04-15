import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import LoginPage from './components/LoginPage';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import HomePage from './pages/HomePage';
import GuidanceLibrary from './components/GuidanceLibrary';
import ProjectWorkspace from './components/ProjectWorkspace';
import AiCoachPanel from './components/AiCoachPanel';
import NewProjectModal from './components/NewProjectModal';
import CommandPalette from './components/CommandPalette';
import PortfolioHealth from './components/PortfolioHealth';
import AiPlaybooks from './components/AiPlaybooks';
import NotificationPanel from './components/NotificationPanel';
import Toast from './components/Toast';
import { useAppState } from './data/store';

type View = 'home' | 'projects' | 'guidance' | 'ai-assist' | 'project-workspace' | 'portfolio' | 'playbooks';

const viewTitles: Record<View, { title: string; subtitle?: string }> = {
  home: { title: 'Welcome back, Lea', subtitle: 'Here\'s your product management workspace' },
  projects: { title: 'Projects', subtitle: 'Manage your active initiatives' },
  guidance: { title: 'Guidance Library', subtitle: 'AI methods, templates, and best practices' },
  'ai-assist': { title: 'AI Assistant', subtitle: 'Get AI help across your projects' },
  'project-workspace': { title: '', subtitle: '' },
  portfolio: { title: 'Portfolio Health', subtitle: 'AI-calculated health scores across your initiatives' },
  playbooks: { title: 'AI Playbooks', subtitle: 'Multi-step guided workflows for product management' },
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userName, setUserName] = useState('');
  const [activeView, setActiveView] = useState<View>('home');
  const [showNewProject, setShowNewProject] = useState(false);
  const [showAiCoach, setShowAiCoach] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [viewMode, setViewMode] = useState<'pm' | 'executive'>('pm');

  const store = useAppState();

  // Global Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // When AI coach context changes, open the panel
  useEffect(() => {
    if (store.aiCoachContext) {
      setShowAiCoach(true);
    }
  }, [store.aiCoachContext]);

  const handleNavigate = useCallback((view: string) => {
    if (view === 'ai-assist') {
      setShowAiCoach(true);
      return;
    }
    setActiveView(view as View);
  }, []);

  const handleViewProject = (id: string) => {
    store.setActiveProjectId(id);
    setActiveView('project-workspace');
  };

  const handleOpenAiWithPrompt = (prompt: string) => {
    store.openAiCoachWithPrompt(prompt);
    setShowAiCoach(true);
    setTimeout(() => store.sendAiMessage(prompt), 300);
  };

  const handleCreateProject = (name: string, description: string, category: string) => {
    const newId = store.createProject(name, description, category);
    store.setActiveProjectId(newId);
    setActiveView('project-workspace');
  };

  const handleLogin = (username: string) => {
    setUserName(username);
    setIsAuthenticated(true);
  };

  const handleToggleNotifications = useCallback(() => {
    setShowNotifications((prev) => !prev);
  }, []);

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const viewConfig = viewTitles[activeView];
  const showSidebar = activeView !== 'project-workspace';

  return (
    <div className="flex min-h-screen bg-az-surface">
      {/* Sidebar */}
      {showSidebar && (
        <Sidebar
          activeView={activeView}
          onNavigate={handleNavigate}
          onNewProject={() => setShowNewProject(true)}
        />
      )}

      {/* Main content area */}
      <main className={`flex-1 transition-all duration-300 ${showSidebar ? 'ml-[260px]' : ''}`}>
        {showSidebar && (
          <TopBar
            title={viewConfig.title}
            subtitle={viewConfig.subtitle}
            viewMode={viewMode}
            onToggleViewMode={() => setViewMode(viewMode === 'pm' ? 'executive' : 'pm')}
            onOpenCommandPalette={() => setShowCommandPalette(true)}
            onToggleNotifications={handleToggleNotifications}
            userName={userName}
          />
        )}

        <div className={showSidebar ? 'p-8' : ''}>
          {activeView === 'home' && (
            <HomePage
              store={store}
              onNewProject={() => setShowNewProject(true)}
              onBrowseGuidance={() => setActiveView('guidance')}
              onViewProjects={() => setActiveView('projects')}
              onViewProject={handleViewProject}
              onOpenAiWithPrompt={handleOpenAiWithPrompt}
              onNavigate={handleNavigate}
            />
          )}

          {activeView === 'projects' && (
            <HomePage
              store={store}
              onNewProject={() => setShowNewProject(true)}
              onBrowseGuidance={() => setActiveView('guidance')}
              onViewProjects={() => setActiveView('projects')}
              onViewProject={handleViewProject}
              onOpenAiWithPrompt={handleOpenAiWithPrompt}
              onNavigate={handleNavigate}
            />
          )}

          {activeView === 'guidance' && (
            <GuidanceLibrary
              onBack={() => setActiveView('home')}
              onOpenAiWithPrompt={handleOpenAiWithPrompt}
            />
          )}

          {activeView === 'project-workspace' && (
            <ProjectWorkspace
              store={store}
              onBack={() => setActiveView('home')}
              onOpenAiWithPrompt={handleOpenAiWithPrompt}
            />
          )}

          {activeView === 'portfolio' && (
            <PortfolioHealth
              onBack={() => setActiveView('home')}
              viewMode={viewMode}
              onViewProject={handleViewProject}
            />
          )}

          {activeView === 'playbooks' && (
            <AiPlaybooks
              onBack={() => setActiveView('home')}
              onOpenAiWithPrompt={handleOpenAiWithPrompt}
            />
          )}
        </div>
      </main>

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onNavigate={handleNavigate}
        onNewProject={() => setShowNewProject(true)}
      />

      {/* Notification Panel */}
      <AnimatePresence>
        {showNotifications && (
          <NotificationPanel
            isOpen={showNotifications}
            onClose={() => setShowNotifications(false)}
            onViewProject={(id) => { setShowNotifications(false); handleViewProject(id); }}
          />
        )}
      </AnimatePresence>

      {/* AI Coach floating panel */}
      <AnimatePresence>
        {showAiCoach && (
          <AiCoachPanel
            isOpen={showAiCoach}
            onClose={() => { setShowAiCoach(false); store.setAiCoachContext(''); }}
            store={store}
          />
        )}
      </AnimatePresence>

      {/* New Project Modal */}
      <NewProjectModal
        isOpen={showNewProject}
        onClose={() => setShowNewProject(false)}
        onCreateProject={handleCreateProject}
      />

      {/* Toast Notifications */}
      <Toast message={store.notification} />
    </div>
  );
}

export default App;
