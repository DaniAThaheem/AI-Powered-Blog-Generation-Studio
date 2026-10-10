import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Search, Sparkles, BookOpen, Layers } from 'lucide-react';

export const RetrievalTester: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const retrieveMutation = useMutation({
    mutationFn: (q: string) => documentsApi.retrieve(q),
    onSuccess: (data) => {
      setResults(data.results || []);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    retrieveMutation.mutate(query.trim());
  };

  return (
    <Card className="glass-panel">
      <CardHeader className="py-4">
        <div className="flex items-center gap-2 text-cyan-400 mb-1">
          <Sparkles className="w-4 h-4" />
          <span className="text-[10px] font-mono font-semibold uppercase">Vector Retrieval Sandbox</span>
        </div>
        <CardTitle>Test Vector Retrieval (Pinecone RAG)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a test query to retrieve relevant document chunks..."
            className="flex-1 text-xs"
          />
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={retrieveMutation.isPending}
            disabled={!query.trim() || retrieveMutation.isPending}
            leftIcon={<Search className="w-3.5 h-3.5" />}
          >
            Query
          </Button>
        </form>

        {results.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-border/40">
            <p className="text-xs font-semibold text-text-primary">
              Matched Chunks ({results.length}):
            </p>
            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {results.map((r, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-surface-elevated/60 border border-border/40 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-text-primary flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                      {r.filename}
                      {r.page_number && (
                        <span className="text-[10px] text-text-muted">Page {r.page_number}</span>
                      )}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/40 text-cyan-400">
                      Score: {(r.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-text-secondary leading-relaxed bg-surface/50 p-2 rounded">
                    {r.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
