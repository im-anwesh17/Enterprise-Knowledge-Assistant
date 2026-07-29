import React, { useState } from 'react';
import { Sparkles, Terminal, Loader2 } from 'lucide-react';
import { executeNLQuery } from '../services/api';
import { DynamicChart } from '../components/analytics/DynamicChart';
import { KPIContainer } from '../components/analytics/KPIContainer';

interface QueryResult {
  generated_sql: string;
  columns: string[];
  results: any[];
  explanation: string;
}

export default function DashboardPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await executeNLQuery(query);
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An unexpected error occurred while processing the query.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Text-to-SQL Analytics</h1>
        <p className="text-[hsl(var(--foreground))]/60 text-lg">
          Ask questions about enterprise sales data in plain English.
        </p>
      </div>

      <form onSubmit={handleQuery} className="relative group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">

          <Sparkles className="text-primary/70" size={24} />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What was the total revenue by region last month?"
          className="w-full bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-2xl py-5 pl-14 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-primary/50 shadow-sm transition-all group-hover:border-primary/30"
          disabled={loading}
        />
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="absolute inset-y-2 right-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center min-w-[120px]"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : 'Analyze'}
        </button>
      </form>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 rounded-xl flex items-start gap-3">
          <Terminal className="shrink-0 mt-0.5" size={20} />

          <div>
            <h4 className="font-semibold">Query Failed</h4>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
          
          <div className="glass-card rounded-2xl p-6 border-l-4 border-l-primary">
            <h3 className="flex items-center gap-2 text-lg font-bold mb-3 text-primary">
              <Sparkles size={20} /> AI Executive Summary
            </h3>
            <p className="text-lg leading-relaxed">{result.explanation}</p>
          </div>

          {result.results.length === 1 ? (
            <KPIContainer data={result.results} columns={result.columns} />
          ) : (
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-lg font-bold mb-6">Data Visualization</h3>
              <DynamicChart data={result.results} columns={result.columns} />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-black/5 dark:bg-black/40 rounded-2xl p-6 border border-[hsl(var(--border))]">

              <h3 className="flex items-center gap-2 font-bold mb-4">
                <Terminal size={18} /> Generated SQL
              </h3>
              <pre className="text-sm font-mono overflow-x-auto p-4 bg-white dark:bg-black/50 rounded-xl border border-[hsl(var(--border))]">
                {result.generated_sql}
              </pre>
            </div>
            
            <div className="bg-black/5 dark:bg-black/40 rounded-2xl p-6 border border-[hsl(var(--border))]">
              <h3 className="flex items-center gap-2 font-bold mb-4">
                <Database size={18} /> Raw Data Preview
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-[hsl(var(--card))] border-b border-[hsl(var(--border))]">
                    <tr>
                      {result.columns.map(col => (
                        <th key={col} className="px-4 py-3 font-semibold">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.slice(0, 5).map((row, i) => (
                      <tr key={i} className="border-b border-[hsl(var(--border))]/50">
                        {result.columns.map(col => (
                          <td key={`${i}-${col}`} className="px-4 py-3">{row[col]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}
