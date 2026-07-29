import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, MessageSquare, Loader2, FileText, Database } from 'lucide-react';
import { getChatSessions, createChatSession, sendChatMessage } from '../services/api';

interface ChatSession {
  id: number;
  title: string;
}

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const data = await getChatSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
        // Note: Realistically, you would fetch history for this session here.
        // For simplicity in Phase 5, we'll start with empty UI messages on session switch.
        setMessages([]); 
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewSession = async () => {
    try {
      const newSession = await createChatSession(`Chat ${sessions.length + 1}`);
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeSessionId) return;

    const userMessage: ChatMessage = { id: Date.now(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const result = await sendChatMessage(activeSessionId, userMessage.content);
      const aiMessage: ChatMessage = { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: result.answer,
        citations: result.citations
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (e) {
      const errorMessage: ChatMessage = { id: Date.now() + 1, role: 'assistant', content: "Sorry, I encountered an error answering your question." };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Session Sidebar */}
      <div className="w-64 border-r border-[hsl(var(--border))] bg-black/5 dark:bg-black/20 p-4 flex flex-col">
        <button 
          onClick={handleNewSession}
          className="flex items-center gap-2 w-full justify-center bg-primary text-primary-foreground font-semibold py-3 px-4 rounded-xl mb-6 hover:bg-primary/90 transition-all"
        >
          <Plus size={18} /> New Chat
        </button>
        
        <h3 className="text-sm font-semibold text-[hsl(var(--foreground))]/50 mb-3 px-2">RECENT</h3>
        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => { setActiveSessionId(s.id); setMessages([]); }}
              className={`flex items-center gap-3 w-full text-left px-3 py-3 rounded-lg transition-all ${
                activeSessionId === s.id 
                  ? 'bg-primary/10 text-primary font-medium' 
                  : 'hover:bg-[hsl(var(--border))] text-[hsl(var(--foreground))]/70'
              }`}
            >
              <MessageSquare size={18} />
              <span className="truncate">{s.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-[hsl(var(--background))]">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-[hsl(var(--foreground))]/40 space-y-4">
              <Database size={48} className="opacity-20" />
              <p className="text-xl font-medium">Start a conversation</p>
              <p className="text-sm">Ask about enterprise data or documents.</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-5 ${
                msg.role === 'user' 
                  ? 'bg-primary text-primary-foreground ml-auto' 
                  : 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]'
              }`}>
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                
                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-[hsl(var(--border))] space-y-2">
                    <h4 className="text-xs font-semibold text-[hsl(var(--foreground))]/50 uppercase tracking-wider">Sources</h4>
                    {msg.citations.map((c, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-[hsl(var(--foreground))]/70 bg-black/5 dark:bg-black/20 p-2 rounded">
                        <FileText size={14} className="mt-0.5 shrink-0" />
                        <div>
                          <span className="font-medium">{c.filename}</span> (Pg. {c.page_number})
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-2xl p-5 flex items-center gap-3 text-[hsl(var(--foreground))]/60">
                <Loader2 size={18} className="animate-spin text-primary" />
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="p-4 bg-[hsl(var(--background))] border-t border-[hsl(var(--border))]">
          <div className="max-w-4xl mx-auto relative">
            <form onSubmit={handleSend}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                className="w-full bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-2xl py-4 pl-6 pr-16 focus:outline-none focus:ring-2 focus:ring-primary/50 shadow-sm"
                disabled={loading || !activeSessionId}
              />
              <button 
                type="submit"
                disabled={loading || !input.trim() || !activeSessionId}
                className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
