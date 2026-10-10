import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { CopyButton } from '../../components/shared/EmptyState';
import { MarkdownRenderer } from '../../components/shared/MarkdownRenderer';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { Tabs } from '../../components/ui/Tabs';
import { SourcesView } from '../sources/SourcesView';
import { MediaGallery } from '../media/MediaGallery';
import {
  Download,
  Edit3,
  BookOpen,
  FileText,
  Image as ImageIcon,
  History,
  Share2,
  Calendar,
  Layers,
} from 'lucide-react';

export const BlogDetails: React.FC<{ generationId: string }> = ({ generationId }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('article');

  const { data: blog, isLoading, error } = useQuery({
    queryKey: ['generation', generationId],
    queryFn: () => generationsApi.getById(generationId),
  });

  if (isLoading) {
    return <div className="p-12 text-center text-xs text-text-muted">Loading blog article...</div>;
  }

  if (error || !blog) {
    return (
      <div className="p-8 text-center text-xs text-red-400">
        Could not load article. It may have been deleted or does not exist.
      </div>
    );
  }

  const exportUrl = generationsApi.exportMarkdownUrl(generationId);
  const sourceCount = (blog.evidence?.length || 0) + (blog.document_chunks_used?.length || 0);
  const imageCount = blog.image_specs?.length || 0;

  const tabs = [
    { id: 'article', label: 'Article', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { id: 'sources', label: 'Sources & Citations', icon: <FileText className="w-3.5 h-3.5" />, count: sourceCount },
    { id: 'media', label: 'Diagrams & Figures', icon: <ImageIcon className="w-3.5 h-3.5" />, count: imageCount },
    { id: 'run', label: 'Workflow Run', icon: <History className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <PageHeader
        title={blog.blog_title || blog.topic}
        description={`Topic: ${blog.topic}`}
        badge={<StatusBadge status={blog.status} />}
        actions={
          <div className="flex items-center gap-2">
            <CopyButton text={blog.final_markdown || ''} label="Copy Markdown" />
            <a href={exportUrl} download>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<Download className="w-3.5 h-3.5" />}
              >
                Download .md
              </Button>
            </a>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/blogs/${generationId}/edit`)}
              leftIcon={<Edit3 className="w-3.5 h-3.5" />}
            >
              Edit in Studio
            </Button>
          </div>
        }
      />

      {/* Meta Bar */}
      <div className="flex flex-wrap items-center gap-4 py-3 px-4 rounded-xl bg-surface border border-border/50 text-xs text-text-secondary">
        <span className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-text-muted" />
          {new Date(blog.created_at).toLocaleDateString()}
        </span>
        <span className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          Format: <span className="font-semibold text-text-primary capitalize">{blog.blog_kind}</span>
        </span>
        <span>•</span>
        <span>
          Audience: <span className="text-text-primary">{blog.audience}</span>
        </span>
        <span>•</span>
        <span>
          Tone: <span className="text-text-primary">{blog.tone}</span>
        </span>
      </div>

      {/* Navigation Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Panels */}
      {activeTab === 'article' && (
        <div className="p-6 sm:p-10 rounded-xl bg-surface border border-border/50 shadow-sm">
          <MarkdownRenderer content={blog.final_markdown || '*No markdown generated.*'} />
        </div>
      )}

      {activeTab === 'sources' && (
        <SourcesView
          webSources={blog.evidence || []}
          ragSources={blog.document_chunks_used || []}
        />
      )}

      {activeTab === 'media' && (
        <MediaGallery generationId={generationId} images={blog.image_specs || []} />
      )}

      {activeTab === 'run' && (
        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-surface border border-border/50 space-y-3">
            <h3 className="text-sm font-semibold text-text-primary">Generation Run Summary</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-surface-elevated">
                <span className="text-text-muted">Generation ID:</span>
                <p className="font-mono text-cyan-400 mt-0.5">{blog.id}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-elevated">
                <span className="text-text-muted">LangGraph Thread ID:</span>
                <p className="font-mono text-cyan-400 mt-0.5">{blog.thread_id}</p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/generations/${generationId}/progress`)}
              className="mt-3"
            >
              Inspect Workflow Timeline →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
