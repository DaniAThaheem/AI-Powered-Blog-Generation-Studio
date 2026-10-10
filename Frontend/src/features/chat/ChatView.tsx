import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import { chatApi } from '../../api/chat';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Sparkles,
  BookOpen,
  Check,
  RefreshCw,
} from 'lucide-react';

interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

export const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am your Technical Reference Assistant. Ask me anything grounded in your uploaded documents, architecture specs, or CVs.',
    },
  ]);
  const [input, setInput] = useState('');
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list('ready'),
  });

  const chatMutation = useMutation({
    mutationFn: (msg: string) => {
      const history = messages
        .filter((m) => m.id !== 'welcome')
        .map((m) => ({ role: m.role, content: m.content }));
      return chatApi.sendMessage(msg, history, selectedDocs);
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.reply,
          sources: data.sources,
        },
      ]);
    },
    onError: (err: any) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${err.message || 'Failed to query assistant'}`,
        },
      ]);
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatMutation.isPending]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userText = input.trim();
    setInput('');
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: userText,
      },
    ]);

    chatMutation.mutate(userText);
  };

  const toggleDoc = (docId: string) => {
    setSelectedDocs((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="space-y-4 max-w-5xl mx-auto h-[calc(100vh-7rem)] flex flex-col">
      <PageHeader
        title="Reference Document Chatbot"
        description="Interactive Q&A powered by LangGraph, Pinecone vector embeddings, and Gemini"
      />

      {/* Document filter bar */}
      {documents && documents.length > 0 && (
        <div className="p-3 rounded-xl bg-surface border border-border/50 flex items-center gap-2 overflow-x-auto flex-shrink-0 text-xs">
          <span className="text-text-muted font-medium whitespace-nowrap">Filter Sources:</span>
          {documents.map((doc) => {
            const isSelected = selectedDocs.includes(doc.id);
            return (
              <button
                key={doc.id}
                type="button"
                onClick={() => toggleDoc(doc.id)}
                className={`px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                  isSelected
                    ? 'border-cyan-400 bg-cyan-950/40 text-cyan-300'
                    : 'border-border/60 bg-surface-elevated/40 text-text-secondary hover:text-text-primary'
                }`}
              >
                <span>{doc.original_name}</span>
                {isSelected && <Check className="w-3 h-3 text-cyan-400" />}
              </button>
            );
          })}
        </div>
      )}

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto p-4 rounded-xl bg-surface border border-border/50 space-y-4">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  isUser ? 'bg-primary text-white' : 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/40'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-2xl rounded-xl p-4 text-xs leading-relaxed space-y-2.5 ${
                  isUser
                    ? 'bg-primary text-white ml-12'
                    : 'bg-surface-elevated/80 border border-border/60 text-text-primary mr-12'
                }`}
              >
                <p className="whitespace-pre-wrap">{m.content}</p>

                {/* Grounded reference citations */}
                {!isUser && m.sources && m.sources.length > 0 && (
                  <div className="pt-2 border-t border-border/40 space-y-1.5">
                    <p className="text-[10px] font-mono uppercase text-cyan-400 font-semibold flex items-center gap-1">
                      <BookOpen className="w-3 h-3" />
                      Grounded References ({m.sources.length}):
                    </p>
                    <div className="space-y-1">
                      {m.sources.map((s, sIdx) => (
                        <div
                          key={sIdx}
                          className="text-[11px] p-2 rounded bg-surface/60 border border-border/30 text-text-secondary"
                        >
                          <span className="font-semibold text-text-primary">
                            {s.filename} (Page {s.page_number || 1})
                          </span>
                          : "{s.content?.slice(0, 150)}..."
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {chatMutation.isPending && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3 rounded-xl bg-surface-elevated border border-border/60 text-xs text-text-secondary flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
              <span>Retrieving context & generating answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input box */}
      <form onSubmit={handleSend} className="flex gap-2 flex-shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a technical question about your reference documents..."
          className="flex-1 bg-surface border border-border rounded-xl px-4 py-3 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
        />
        <Button
          type="submit"
          variant="primary"
          size="md"
          isLoading={chatMutation.isPending}
          disabled={!input.trim() || chatMutation.isPending}
          rightIcon={<Send className="w-3.5 h-3.5" />}
        >
          Send
        </Button>
      </form>
    </div>
  );
};
