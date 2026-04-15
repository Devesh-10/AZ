import { useState } from 'react';
import LoginPage from './components/LoginPage';
import ChatInterface from './components/ChatInterface';
import DocumentSidebar from './components/DocumentSidebar';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <div className="az-logo">AZ</div>
          <div className="header-title">
            <h1>Document Query</h1>
            <span className="header-subtitle">RAG-Powered Internal Document Search</span>
          </div>
        </div>
        <button className="logout-btn" onClick={() => setIsAuthenticated(false)}>
          Sign Out
        </button>
      </header>
      <main className="app-main">
        <div className="chat-panel">
          <ChatInterface />
        </div>
        <aside className="sidebar-panel">
          <DocumentSidebar />
        </aside>
      </main>
    </div>
  );
}

export default App;
