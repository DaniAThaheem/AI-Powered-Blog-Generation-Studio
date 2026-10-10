import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Globe, FileText, ExternalLink, Calendar, BookOpen } from 'lucide-react';
import { EvidenceItem, DocumentChunk } from '../../api/types';

interface SourcesViewProps {
  webSources: EvidenceItem[];
  ragSources: DocumentChunk[];
}

export const SourcesView: React.FC<SourcesViewProps> = ({ webSources, ragSources }) => {
  const hasWeb = webSources && webSources.length > 0;
  const hasRag = ragSources && ragSources.length > 0;

  if (!hasWeb && !hasRag) {
    return (
      <div className="p-8 text-center rounded-xl bg-surface border border-border/50 text-xs text-text-muted">
        No external web sources or reference document chunks were cited for this article.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Web Sources Section */}
      {hasWeb && (
        <Card className="glass-panel">
          <CardHeader className="py-4 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-cyan-400" />
              <CardTitle>Web Research Sources (Tavily)</CardTitle>
            </div>
            <span className="text-xs text-text-muted font-mono">{webSources.length} sources verified</span>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/40">
              {webSources.map((source, idx) => (
                <div key={idx} className="p-4 hover:bg-surface-elevated/30 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1.5"
                    >
                      <span>{source.title || source.url}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                    {source.published_at && (
                      <span className="text-[10px] text-text-muted flex items-center gap-1 flex-shrink-0">
                        <Calendar className="w-3 h-3" />
                        {source.published_at}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] font-mono text-text-muted truncate mt-1">{source.url}</p>
                  {source.snippet && (
                    <p className="text-xs text-text-secondary mt-2 bg-surface-muted/40 p-2.5 rounded-lg border border-border/30 leading-relaxed">
                      "{source.snippet}"
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* RAG Reference Documents Section */}
      {hasRag && (
        <Card className="glass-panel">
          <CardHeader className="py-4 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              <CardTitle>Uploaded Reference Documents (Pinecone RAG)</CardTitle>
            </div>
            <span className="text-xs text-text-muted font-mono">{ragSources.length} chunks retrieved</span>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/40">
              {ragSources.map((chunk, idx) => (
                <div key={idx} className="p-4 hover:bg-surface-elevated/30 transition-colors">
                  <div className="flex items-center justify-between gap-3 mb-1.5">
                    <span className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
                      {chunk.filename}
                      {chunk.page_number && (
                        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded">
                          Page {chunk.page_number}
                        </span>
                      )}
                    </span>
                    {chunk.score !== undefined && (
                      <span className="text-[10px] font-mono text-text-muted">
                        Sim: {(chunk.score * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-text-secondary bg-surface-muted/40 p-3 rounded-lg border border-border/30 font-mono text-[11px] leading-relaxed">
                    {chunk.content}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
