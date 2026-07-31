import React, { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import { Sun, Moon, Database, FileText, MessageSquare } from 'lucide-react';




function App() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[hsl(var(--background))]">
      <aside className="w-full md:w-64 border-r border-[hsl(var(--border))] bg-white/5 dark:bg-black/20 p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-10 text-primary">

          <Database size={32} />
          <h1 className="text-xl font-bold tracking-tight text-[hsl(var(--foreground))]">Enterprise<br/>Assistant</h1>
        </div>
        
        <nav className="flex-1 space-y-2">
          <Link to="/" className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-[hsl(var(--border))] text-[hsl(var(--foreground))]/70 hover:text-[hsl(var(--foreground))] transition-colors">
            <Database size={20} />
            SQL Analytics
          </Link>
          <Link to="/chat" className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-[hsl(var(--border))] text-[hsl(var(--foreground))]/70 hover:text-[hsl(var(--foreground))] transition-colors">
            <MessageSquare size={20} />
            AI Chat
          </Link>

          <Link to="/documents" className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-[hsl(var(--border))] text-[hsl(var(--foreground))]/70 hover:text-[hsl(var(--foreground))] transition-colors">
            <FileText size={20} />
            Knowledge Base
          </Link>
        </nav>

        <button 
          onClick={() => setDarkMode(!darkMode)}
          className="mt-auto flex items-center gap-3 px-4 py-3 rounded-xl border border-[hsl(var(--border))] hover:bg-[hsl(var(--border))] transition-colors"
        >
          {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </aside>

      <main className="flex-1 overflow-auto">
        <Routes>

          <Route path="/" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
        </Routes>


      </main>
    </div>
  );
}

export default App;
