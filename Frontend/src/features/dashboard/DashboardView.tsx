import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { documentsApi } from '../../api/documents';
import { mediaApi } from '../../api/media';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PageHeader } from '../../components/shared/PageHeader';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { EmptyState } from '../../components/shared/EmptyState';
import {
  BookOpen,
  FileText,
  Image as ImageIcon,
  PenTool,
  Clock,
  ArrowRight,
  Sparkles,
  CheckCircle,
} from 'lucide-react';

export const DashboardView: React.FC = () => {
  const navigate = useNavigate();

  const { data: generations, isLoading: genLoading } = useQuery({
    queryKey: ['generations'],
    queryFn: () => generationsApi.list({ limit: 10 }),
  });

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(),
  });

  const { data: media } = useQuery({
    queryKey: ['media'],
    queryFn: () => mediaApi.list(),
  });

  const completedCount = generations?.filter((g) => g.status === 'completed').length || 0;
  const runningCount = generations?.filter((g) => g.status === 'running' || g.status === 'queued').length || 0;
  const docsCount = documents?.length || 0;
  const mediaCount = media?.length || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your technical content generation studio and knowledge base"
        actions={
          <Button
            variant="primary"
            onClick={() => navigate('/generate')}
            leftIcon={<Sparkles className="w-4 h-4" />}
          >
            Start New Generation
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted font-medium">Completed Blogs</p>
              <h3 className="text-2xl font-bold text-text-primary mt-1">{completedCount}</h3>
            </div>
            <div className="p-2.5 rounded-lg bg-primary/10 text-primary-light">
              <BookOpen className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted font-medium">In Progress</p>
              <h3 className="text-2xl font-bold text-cyan-400 mt-1">{runningCount}</h3>
            </div>
            <div className="p-2.5 rounded-lg bg-cyan-950/40 text-cyan-400">
              <Clock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted font-medium">Reference Docs</p>
              <h3 className="text-2xl font-bold text-text-primary mt-1">{docsCount}</h3>
            </div>
            <div className="p-2.5 rounded-lg bg-emerald-950/40 text-emerald-400">
              <FileText className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted font-medium">Generated Media</p>
              <h3 className="text-2xl font-bold text-text-primary mt-1">{mediaCount}</h3>
            </div>
            <div className="p-2.5 rounded-lg bg-purple-950/40 text-purple-400">
              <ImageIcon className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Launch Banner */}
      <div className="rounded-xl p-5 bg-gradient-to-r from-primary/20 via-surface to-accent/10 border border-primary/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Create Multi-Agent Technical Article
          </h3>
          <p className="text-xs text-text-secondary mt-1 max-w-xl">
            Input a complex topic. Our LangGraph workflow autonomously handles topic routing, web research, parallel section writing, and architecture diagrams.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/generate')}
          rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
        >
          Generate Now
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Generations */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="glass-panel">
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <CardTitle>Recent Generations</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/history')}>
                View all
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              {genLoading ? (
                <div className="p-6 text-center text-xs text-text-muted">Loading generations...</div>
              ) : !generations || generations.length === 0 ? (
                <div className="p-6">
                  <EmptyState
                    title="No generations yet"
                    description="Launch your first AI-written technical blog to see execution progress here."
                    actionText="Create Blog"
                    onAction={() => navigate('/generate')}
                  />
                </div>
              ) : (
                <div className="divide-y divide-border/40">
                  {generations.slice(0, 5).map((gen) => (
                    <div
                      key={gen.id}
                      onClick={() =>
                        navigate(
                          gen.status === 'completed'
                            ? `/blogs/${gen.id}`
                            : `/generations/${gen.id}/progress`
                        )
                      }
                      className="p-4 hover:bg-surface-elevated/40 cursor-pointer transition-colors flex items-center justify-between gap-4"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-semibold text-text-primary truncate">
                            {gen.blog_title || gen.topic}
                          </h4>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-elevated text-text-muted">
                            {gen.blog_kind}
                          </span>
                        </div>
                        <p className="text-[11px] text-text-secondary truncate mt-0.5">
                          {gen.topic}
                        </p>
                        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-text-muted">
                          <span>{new Date(gen.created_at).toLocaleDateString()}</span>
                          {gen.source_count > 0 && <span>• {gen.source_count} sources</span>}
                          {gen.image_count > 0 && <span>• {gen.image_count} images</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <StatusBadge status={gen.status} size="sm" />
                        <ArrowRight className="w-4 h-4 text-text-muted" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Knowledge Base Overview */}
        <div className="space-y-4">
          <Card className="glass-panel">
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <CardTitle>Reference Documents (RAG)</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/documents')}>
                Manage
              </Button>
            </CardHeader>
            <CardContent className="p-4">
              {!documents || documents.length === 0 ? (
                <div className="text-center py-6">
                  <p className="text-xs text-text-muted mb-3">No reference documents indexed</p>
                  <Button variant="outline" size="sm" onClick={() => navigate('/documents')}>
                    Upload PDF / Doc
                  </Button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {documents.slice(0, 4).map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => navigate(`/documents/${doc.id}`)}
                      className="p-2.5 rounded-lg bg-surface-elevated/50 border border-border/40 hover:border-cyan-500/40 cursor-pointer transition-colors flex items-center justify-between"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="text-xs font-medium text-text-primary truncate">{doc.original_name}</p>
                        <p className="text-[10px] text-text-muted mt-0.5">{doc.chunk_count} chunks indexed</p>
                      </div>
                      <StatusBadge status={doc.status} size="sm" />
                    </div>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-xs text-cyan-400 mt-2"
                    onClick={() => navigate('/chat')}
                  >
                    Chat with Reference Documents →
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
