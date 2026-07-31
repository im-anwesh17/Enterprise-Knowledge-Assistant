import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Loader2, Server, Search, CheckCircle } from 'lucide-react';
import { getDocuments, uploadDocument } from '../services/api';

interface Document {
  id: number;
  filename: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }

    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Knowledge Base</h1>
        <p className="text-[hsl(var(--foreground))]/60 text-lg">
          Upload enterprise documents to securely power the AI Assistant.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 rounded-xl">
          <p>{error}</p>
        </div>
      )}

      {/* Upload Zone */}
      <div 
        className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
          uploading ? 'bg-[hsl(var(--border))]/50 border-primary/50' : 'border-[hsl(var(--border))] hover:border-primary/50 hover:bg-black/5 dark:hover:bg-white/5'
        }`}
        onClick={() => !uploading && fileInputRef.current?.click()}
        style={{ cursor: uploading ? 'wait' : 'pointer' }}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileSelect} 
          accept="application/pdf"
          className="hidden" 
        />
        <div className="flex flex-col items-center justify-center gap-4">
          {uploading ? (
            <>
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
                <Loader2 size={48} className="animate-spin text-primary relative z-10" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-primary">Processing Document...</h3>
                <p className="text-[hsl(var(--foreground))]/60">Extracting text, chunking, and embedding into ChromaDB.</p>
              </div>
            </>
          ) : (
            <>
              <div className="p-4 bg-primary/10 rounded-full text-primary">
                <Upload size={32} />
              </div>
              <div>
                <h3 className="text-xl font-bold">Click to Upload PDF</h3>
                <p className="text-[hsl(var(--foreground))]/60">Maximum file size: 50MB</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[hsl(var(--border))] flex items-center justify-between bg-black/5 dark:bg-white/5">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Server size={20} className="text-primary" /> Indexed Documents
          </h2>
          <div className="text-sm text-[hsl(var(--foreground))]/60 font-medium bg-[hsl(var(--background))] px-3 py-1 rounded-full border border-[hsl(var(--border))]">
            {documents.length} Files
          </div>
        </div>
        
        {loading && documents.length === 0 ? (
          <div className="p-12 flex justify-center">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-[hsl(var(--foreground))]/50">
            <FileText size={48} className="mx-auto mb-4 opacity-20" />
            <p>No documents uploaded yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-[hsl(var(--card))] border-b border-[hsl(var(--border))]">
                <tr>
                  <th className="px-6 py-4 font-semibold text-[hsl(var(--foreground))]/70 uppercase tracking-wider">Filename</th>
                  <th className="px-6 py-4 font-semibold text-[hsl(var(--foreground))]/70 uppercase tracking-wider">Size</th>
                  <th className="px-6 py-4 font-semibold text-[hsl(var(--foreground))]/70 uppercase tracking-wider">Vector Chunks</th>
                  <th className="px-6 py-4 font-semibold text-[hsl(var(--foreground))]/70 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border))]/50 bg-[hsl(var(--background))]">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4 font-medium flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded text-primary">
                        <FileText size={16} />
                      </div>
                      {doc.filename}
                    </td>
                    <td className="px-6 py-4 text-[hsl(var(--foreground))]/70">
                      {formatBytes(doc.file_size)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">
                        <Search size={14} />
                        {doc.chunk_count}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-flex items-center gap-1.5 text-green-600 dark:text-green-500 font-medium">
                        <CheckCircle size={16} />
                        Indexed
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
