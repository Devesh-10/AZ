import React, { useState } from 'react';
import { chatSummary, suggestedQuestions } from '../data/mapData';
import '../styles/ChatAssist.css';

interface Message {
  type: 'question' | 'answer';
  text: string;
}

const ChatAssist: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');

  const handleQuestionClick = (questionId: string) => {
    const question = suggestedQuestions.find((q) => q.id === questionId);
    if (question) {
      setMessages((prev) => [
        ...prev,
        { type: 'question', text: question.question },
        { type: 'answer', text: question.answer },
      ]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      setMessages((prev) => [
        ...prev,
        { type: 'question', text: inputText },
        { type: 'answer', text: 'This is a placeholder response. In a real implementation, this would be connected to an AI service.' },
      ]);
      setInputText('');
    }
  };

  return (
    <>
      <button className="chat-fab" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? '✕' : '💬'}
      </button>

      {isOpen && (
        <div className="chat-panel">
          <div className="chat-header">
            <h3>DSCM Assist</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>✕</button>
          </div>

          <div className="chat-content">
            <div className="summary-section">
              <h4>Summary:</h4>
              <ul>
                {chatSummary.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>

            {messages.length === 0 && (
              <div className="suggested-questions">
                <h4>Suggested questions:</h4>
                <div className="question-chips">
                  {suggestedQuestions.map((q) => (
                    <button
                      key={q.id}
                      className="question-chip"
                      onClick={() => handleQuestionClick(q.id)}
                    >
                      {q.question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="messages-list">
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.type}`}>
                  {msg.type === 'question' && <strong>You: </strong>}
                  {msg.type === 'answer' && <strong>DSCM Assist: </strong>}
                  <span style={{ whiteSpace: 'pre-line' }}>{msg.text}</span>
                </div>
              ))}
            </div>

            {messages.length > 0 && (
              <div className="suggested-questions compact">
                <div className="question-chips">
                  {suggestedQuestions
                    .filter((q) => !messages.some((m) => m.text === q.question))
                    .map((q) => (
                      <button
                        key={q.id}
                        className="question-chip small"
                        onClick={() => handleQuestionClick(q.id)}
                      >
                        {q.question}
                      </button>
                    ))}
                </div>
              </div>
            )}
          </div>

          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Ask a question..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatAssist;
