import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
import ChatInterface from "./components/ChatInterface";

const App: React.FC = () => {
  const [chatOpen, setChatOpen] = useState(true);

  return (
    <>
      <style>{`
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; }
        @keyframes blink { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
      `}</style>

      <div style={styles.layout}>
        <nav style={styles.nav}>
          <div style={styles.navLeft}>
            <span style={styles.logo}>🌍</span>
            <span style={styles.navTitle}>ESG Sustainability Hub</span>
          </div>
          <button onClick={() => setChatOpen(!chatOpen)} style={styles.chatToggle}>
            {chatOpen ? "Hide Chat" : "💬 Open Chat"}
          </button>
        </nav>

        <div style={styles.main}>
          <div style={{ ...styles.dashArea, flex: chatOpen ? "1 1 70%" : "1 1 100%" }}>
            <Dashboard />
          </div>
          {chatOpen && (
            <div style={styles.chatArea}>
              <ChatInterface />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  layout: { minHeight: "100vh", display: "flex", flexDirection: "column" },
  nav: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 24px", background: "#fff", borderBottom: "1px solid #e2e8f0",
    position: "sticky", top: 0, zIndex: 100,
  },
  navLeft: { display: "flex", alignItems: "center", gap: 10 },
  logo: { fontSize: 24 },
  navTitle: { fontSize: 17, fontWeight: 700, color: "#0f172a" },
  chatToggle: {
    padding: "8px 16px", borderRadius: 8, border: "1px solid #d1fae5",
    background: "#f0fdf4", color: "#059669", fontWeight: 600, fontSize: 13,
    cursor: "pointer", fontFamily: "Inter, sans-serif",
  },
  main: {
    display: "flex", flex: 1, gap: 0, overflow: "hidden",
  },
  dashArea: {
    padding: 24, overflowY: "auto", height: "calc(100vh - 57px)",
  },
  chatArea: {
    flex: "0 0 380px", height: "calc(100vh - 57px)",
    borderLeft: "1px solid #e2e8f0",
  },
};

export default App;
