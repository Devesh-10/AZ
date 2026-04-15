import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendQuery, fetchDocTypes, Source } from '../api/chatApi';
import './ChatInterface.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

const SUGGESTED_QUERIES = [
  'What are the gowning requirements for aseptic manufacturing?',
  'How are deviations classified at AZ?',
  'What is the data retention policy for clinical trial data?',
  'Describe the CAPA effectiveness check process.',
  'What security controls are required on AZ endpoints?',
  'What are the media fill acceptance criteria?',
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [docTypes, setDocTypes] = useState<string[]>([]);
  const [selectedType, setSelectedType] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchDocTypes().then(setDocTypes);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const question = text || input.trim();
    if (!question || loading) return;

    const userMsg: Message = { role: 'user', content: question, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const resp = await sendQuery(question, sessionId, selectedType || undefined);
      setSessionId(resp.session_id);
      const assistantMsg: Message = {
        role: 'assistant',
        content: resp.answer,
        sources: resp.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.', timestamp: new Date() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  return (
    <div className="chat-interface">
      {/* Messages area */}
      <div className="messages-area">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--az-purple)" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <h2>Query AZ Internal Documents</h2>
            <p>Ask questions about SOPs, policies, training materials, clinical protocols, compliance guidelines, and more.</p>
            <div className="suggested-queries">
              {SUGGESTED_QUERIES.map((q, i) => (
                <button key={i} className="suggestion-chip" onClick={() => handleSend(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" fill="none" stroke="white" strokeWidth="2" />
                    </svg>
                  )}
                </div>
                <div className="message-content">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources-list">
                      <span className="sources-label">Sources:</span>
                      {msg.sources.map((s, j) => (
                        <span key={j} className="source-tag" title={`${s.doc_title} — ${s.section} (${Math.round(s.relevance * 100)}% match)`}>
                          <span className="source-type">{s.doc_type}</span>
                          {s.doc_title} — {s.section}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-avatar">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  </svg>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input bar */}
      <div className="input-bar">
        <div className="input-controls">
          {docTypes.length > 0 && (
            <select
              className="type-filter"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
              <option value="">All Document Types</option>
              {docTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          )}
          {sessionId && (
            <button className="new-chat-btn" onClick={handleNewChat} title="New conversation">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Chat
            </button>
          )}
        </div>
        <div className="input-row">
          <input
            type="text"
            placeholder="Ask about AZ internal documents..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button className="send-btn" onClick={() => handleSend()} disabled={loading || !input.trim()}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
