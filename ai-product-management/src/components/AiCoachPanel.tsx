import { motion } from 'framer-motion';
import {
  Sparkles,
  ArrowRight,
  X,
  Send,
  MessageSquare,
  Info,
  User,
  Loader2,
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { AppStore } from '../data/store';

interface AiCoachPanelProps {
  isOpen: boolean;
  onClose: () => void;
  store: AppStore;
}

export default function AiCoachPanel({ isOpen, onClose, store }: AiCoachPanelProps) {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isWaiting = store.aiMessages.length > 0 && store.aiMessages[store.aiMessages.length - 1].role === 'user';

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [store.aiMessages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 200);
  }, [isOpen]);

  // Auto-fill from context
  useEffect(() => {
    if (store.aiCoachContext && isOpen) {
      setMessage('');
    }
  }, [store.aiCoachContext, isOpen]);

  const handleSend = () => {
    const text = message.trim();
    if (!text || isWaiting) return;
    store.sendAiMessage(text);
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    store.sendAiMessage(prompt);
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ x: 360, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 360, opacity: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
      className="fixed right-0 top-0 bottom-0 w-[400px] bg-white border-l border-az-border z-50 flex flex-col shadow-2xl shadow-black/10"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 h-16 border-b border-az-border flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-az-text">AI Coach</h3>
            <span className="text-[10px] text-az-teal font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-az-teal inline-block" />
              Ready to assist
            </span>
          </div>
        </div>
        <button onClick={onClose}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-az-text-tertiary hover:bg-az-surface-warm hover:text-az-text-secondary transition-all">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {store.aiMessages.length === 0 ? (
          <>
            {/* Welcome state */}
            <div className="bg-az-surface-warm rounded-xl p-4 border border-az-border-light">
              <div className="flex items-start gap-3">
                <MessageSquare className="w-4 h-4 text-az-purple mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-medium text-az-text">Welcome to AI Coach</p>
                  <p className="text-xs text-az-text-tertiary mt-1 leading-relaxed">
                    I can help you draft documents, suggest metrics, identify risks, and guide you through each milestone. Ask me anything about your initiatives.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick prompts */}
            <div>
              <h4 className="text-xs font-semibold text-az-text-tertiary uppercase tracking-wider mb-3">Try asking</h4>
              <div className="space-y-2">
                {[
                  'Draft a value proposition for SOP Assistant',
                  'Suggest success metrics for my initiative',
                  'Identify key risks at this stage',
                  'Generate interview questions for stakeholders',
                  'Review my current progress and recommend next steps',
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleQuickPrompt(prompt)}
                    className="w-full flex items-center gap-2.5 p-3 rounded-xl border border-az-border text-left hover:border-az-purple/20 hover:bg-az-purple/[0.02] transition-all group"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-az-text-tertiary group-hover:text-az-purple transition-colors flex-shrink-0" />
                    <span className="text-xs text-az-text-secondary group-hover:text-az-text transition-colors">{prompt}</span>
                    <ArrowRight className="w-3 h-3 text-az-text-tertiary opacity-0 group-hover:opacity-100 ml-auto transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Message history */}
            {store.aiMessages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
                <div className={`max-w-[85%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
                    ${msg.role === 'user'
                      ? 'bg-az-plum text-white rounded-br-md'
                      : 'bg-az-surface-warm text-az-text border border-az-border-light rounded-bl-md'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <p className="text-sm">{msg.content}</p>
                    ) : (
                      <div className="ai-markdown text-xs leading-relaxed">
                        <ReactMarkdown
                          components={{
                            h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1.5 first:mt-0 text-az-plum">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-sm font-bold mt-3 mb-1 first:mt-0 text-az-plum">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-xs font-semibold mt-2.5 mb-1 first:mt-0 text-az-text">{children}</h3>,
                            p: ({ children }) => <p className="mt-1.5 first:mt-0">{children}</p>,
                            strong: ({ children }) => <strong className="font-semibold text-az-text">{children}</strong>,
                            ul: ({ children }) => <ul className="mt-1 ml-3 space-y-0.5 list-disc list-outside">{children}</ul>,
                            ol: ({ children }) => <ol className="mt-1 ml-3 space-y-0.5 list-decimal list-outside">{children}</ol>,
                            li: ({ children }) => <li className="pl-1">{children}</li>,
                            hr: () => <hr className="my-2 border-az-border-light" />,
                            code: ({ children }) => <code className="bg-az-surface px-1 py-0.5 rounded text-[10px] font-mono">{children}</code>,
                            blockquote: ({ children }) => <blockquote className="border-l-2 border-az-plum/30 pl-2 ml-1 mt-1 italic text-az-text-secondary">{children}</blockquote>,
                            table: ({ children }) => <div className="overflow-x-auto mt-2"><table className="w-full text-[10px] border-collapse">{children}</table></div>,
                            th: ({ children }) => <th className="bg-az-surface-warm px-2 py-1 text-left font-semibold border border-az-border-light">{children}</th>,
                            td: ({ children }) => <td className="px-2 py-1 border border-az-border-light">{children}</td>,
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 bg-white rounded-lg border border-az-border p-2.5">
                      <div className="flex items-center gap-1 mb-1.5">
                        <Info className="w-3 h-3 text-az-text-tertiary" />
                        <span className="text-[9px] font-semibold text-az-text-tertiary uppercase tracking-wider">Sources</span>
                      </div>
                      {msg.citations.map((cite, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-[10px] text-az-text-tertiary mt-0.5">
                          <span className="w-3.5 h-3.5 rounded bg-az-surface-warm flex items-center justify-center text-[8px] font-mono flex-shrink-0">{i + 1}</span>
                          {cite}
                        </div>
                      ))}
                    </div>
                  )}

                  <p className="text-[10px] text-az-text-tertiary mt-1 px-1">{msg.timestamp}</p>
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}>
                    <User className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
              </motion.div>
            ))}

            {/* Loading indicator */}
            {isWaiting && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3"
              >
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-az-purple to-az-purple-light flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="bg-az-surface-warm rounded-2xl rounded-bl-md px-4 py-3 border border-az-border-light">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 text-az-purple animate-spin" />
                    <span className="text-xs text-az-text-tertiary">Thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-az-border flex-shrink-0">
        <div className="flex items-center gap-2 bg-az-surface-warm rounded-xl border border-az-border-light p-1.5 focus-within:border-az-purple/30 focus-within:ring-2 focus-within:ring-az-purple/10 transition-all">
          <input
            ref={inputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask AI anything..."
            className="flex-1 bg-transparent px-3 py-2 text-sm text-az-text placeholder:text-az-text-tertiary outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!message.trim() || isWaiting}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white transition-colors flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: 'linear-gradient(135deg, #7c3a5c, #5a2a42)' }}
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="mt-2 text-[10px] text-az-text-tertiary text-center">
          AI suggestions are for guidance only. Always validate with stakeholders.
        </p>
      </div>
    </motion.div>
  );
}
