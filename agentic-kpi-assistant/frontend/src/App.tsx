import { useState } from "react";
import LoginPage from "./components/LoginPage";
import ChatInterface from "./components/ChatInterface";
import AgentFlowPanel from "./components/AgentFlowPanel";
import SqlPanel from "./components/SqlPanel";
import ExecutiveDashboard from "./components/ExecutiveDashboard";
import "./App.css";

type ViewType = "dashboard" | "chat";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState<ViewType>("chat");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [generatedSql, setGeneratedSql] = useState<string | null>(null);
  const [isAgentPanelCollapsed, setIsAgentPanelCollapsed] = useState(false);
  const [isSqlPanelCollapsed, setIsSqlPanelCollapsed] = useState(false);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleStartChat = () => {
    setCurrentView("chat");
  };

  const handleBackToDashboard = () => {
    setCurrentView("dashboard");
  };

  const handleSqlGenerated = (sql: string | null) => {
    setGeneratedSql(sql);
  };

  const handleSessionIdChange = (id: string | null) => {
    setSessionId(id);
  };

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Show executive dashboard
  if (currentView === "dashboard") {
    return <ExecutiveDashboard onStartChat={handleStartChat} />;
  }

  // Show chat interface with three-panel layout
  return (
    <div className="app">
      <main className={`app-main three-panel ${isAgentPanelCollapsed ? 'agent-collapsed' : ''} ${isSqlPanelCollapsed ? 'sql-collapsed' : ''}`}>
        {/* Left Panel - Chat */}
        <div className="chat-panel">
          <ChatInterface
            sessionId={sessionId}
            onSessionIdChange={handleSessionIdChange}
            onNewMessage={() => {}}
            onBackToDashboard={handleBackToDashboard}
            onSqlGenerated={handleSqlGenerated}
          />
        </div>

        {/* Middle Panel - Agent Flow */}
        <aside className={`agent-panel ${isAgentPanelCollapsed ? 'collapsed' : ''}`}>
          <div className="panel-header">
            <span className="panel-title">Agent Flow</span>
            <button
              className="panel-toggle-btn"
              onClick={() => setIsAgentPanelCollapsed(!isAgentPanelCollapsed)}
              title={isAgentPanelCollapsed ? "Expand" : "Minimize"}
            >
              {isAgentPanelCollapsed ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="15 3 21 3 21 9" />
                  <polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              )}
            </button>
          </div>
          {!isAgentPanelCollapsed && (
            <AgentFlowPanel sessionId={sessionId} isCollapsed={false} />
          )}
        </aside>

        {/* Right Panel - SQL */}
        <aside className={`sql-panel ${isSqlPanelCollapsed ? 'collapsed' : ''}`}>
          <div className="panel-header">
            <span className="panel-title">Generated SQL</span>
            <button
              className="panel-toggle-btn"
              onClick={() => setIsSqlPanelCollapsed(!isSqlPanelCollapsed)}
              title={isSqlPanelCollapsed ? "Expand" : "Minimize"}
            >
              {isSqlPanelCollapsed ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="15 3 21 3 21 9" />
                  <polyline points="9 21 3 21 3 15" />
                  <line x1="21" y1="3" x2="14" y2="10" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
              )}
            </button>
          </div>
          {!isSqlPanelCollapsed && (
            <SqlPanel sql={generatedSql} />
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;
