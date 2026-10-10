import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { CopyButton } from '../../components/shared/EmptyState';
import { MarkdownRenderer } from '../../components/shared/MarkdownRenderer';
import {
  Save,
  Download,
  BookOpen,
  Eye,
  Edit,
  Columns,
  Check,
  Clock,
  AlertCircle,
  ArrowLeft,
} from 'lucide-react';

export const BlogEditor: React.FC<{ generationId: string }> = ({ generationId }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: blog, isLoading } = useQuery({
    queryKey: ['generation', generationId],
    queryFn: () => generationsApi.getById(generationId),
  });

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved' | 'error'>('saved');
  const [viewMode, setViewMode] = useState<'split' | 'edit' | 'preview'>('split');
  const debounceTimerRef = useRef<any>(null);

  useEffect(() => {
    if (blog) {
      setTitle(blog.blog_title || blog.topic || '');
      setContent(blog.final_markdown || '');
    }
  }, [blog]);

  const updateMutation = useMutation({
    mutationFn: (data: { blog_title: string; final_markdown: string }) =>
      generationsApi.update(generationId, data),
    onSuccess: () => {
      setSaveStatus('saved');
      queryClient.invalidateQueries({ queryKey: ['generation', generationId] });
      queryClient.invalidateQueries({ queryKey: ['generations'] });
    },
    onError: () => {
      setSaveStatus('error');
    },
  });

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setSaveStatus('unsaved');

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounced autosave after 2.5 seconds of inactivity
    debounceTimerRef.current = setTimeout(() => {
      setSaveStatus('saving');
      updateMutation.mutate({ blog_title: title, final_markdown: newContent });
    }, 2500);
  };

  const handleManualSave = () => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    setSaveStatus('saving');
    updateMutation.mutate({ blog_title: title, final_markdown: content });
  };

  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const exportUrl = generationsApi.exportMarkdownUrl(generationId);

  if (isLoading && !blog) {
    return <div className="p-12 text-center text-xs text-text-muted">Loading blog editor...</div>;
  }

  return (
    <div className="space-y-4 max-w-7xl mx-auto h-[calc(100vh-6rem)] flex flex-col">
      {/* Top Header & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/50 flex-shrink-0">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <button
            onClick={() => navigate(`/blogs/${generationId}`)}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
            title="Back to reading view"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <input
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setSaveStatus('unsaved');
            }}
            placeholder="Blog Title..."
            className="bg-transparent font-bold text-lg sm:text-xl text-text-primary focus:outline-none focus:ring-1 focus:ring-primary/40 rounded px-1.5 py-0.5 w-full max-w-xl"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Save Status Indicator */}
          <div className="text-[11px] font-mono flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-elevated border border-border/40 text-text-muted">
            {saveStatus === 'saved' && (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">Saved</span>
              </>
            )}
            {saveStatus === 'saving' && (
              <>
                <Clock className="w-3 h-3 text-cyan-400 animate-spin" />
                <span className="text-cyan-400">Saving...</span>
              </>
            )}
            {saveStatus === 'unsaved' && (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>Unsaved changes</span>
              </>
            )}
            {saveStatus === 'error' && (
              <>
                <AlertCircle className="w-3 h-3 text-red-400" />
                <span className="text-red-400">Save failed</span>
              </>
            )}
          </div>

          {/* View mode segmented switch */}
          <div className="hidden sm:flex items-center rounded-lg bg-surface-elevated border border-border/50 p-0.5">
            <button
              onClick={() => setViewMode('split')}
              className={`p-1.5 rounded-md text-xs flex items-center gap-1 transition-colors ${
                viewMode === 'split' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text-primary'
              }`}
              title="Split view"
            >
              <Columns className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('edit')}
              className={`p-1.5 rounded-md text-xs flex items-center gap-1 transition-colors ${
                viewMode === 'edit' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text-primary'
              }`}
              title="Editor only"
            >
              <Edit className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('preview')}
              className={`p-1.5 rounded-md text-xs flex items-center gap-1 transition-colors ${
                viewMode === 'preview' ? 'bg-primary text-white' : 'text-text-secondary hover:text-text-primary'
              }`}
              title="Preview only"
            >
              <Eye className="w-3.5 h-3.5" />
            </button>
          </div>

          <CopyButton text={content} label="Copy" />

          <a href={exportUrl} download>
            <Button variant="secondary" size="sm" leftIcon={<Download className="w-3.5 h-3.5" />}>
              Export
            </Button>
          </a>

          <Button
            variant="primary"
            size="sm"
            onClick={handleManualSave}
            isLoading={updateMutation.isPending}
            leftIcon={<Save className="w-3.5 h-3.5" />}
          >
            Save
          </Button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex items-center justify-between text-[11px] font-mono text-text-muted px-2 flex-shrink-0">
        <div className="flex items-center gap-3">
          <span>{wordCount} words</span>
          <span>•</span>
          <span>{content.length} characters</span>
        </div>
        <span className="text-cyan-400/80">GitHub Flavored Markdown</span>
      </div>

      {/* Editor & Preview Split Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0 overflow-hidden">
        {/* Editor Pane */}
        {(viewMode === 'split' || viewMode === 'edit') && (
          <div className="flex flex-col h-full rounded-xl border border-border/60 bg-surface overflow-hidden">
            <div className="px-4 py-2 bg-surface-elevated/70 border-b border-border/40 text-xs font-semibold text-text-secondary flex items-center justify-between">
              <span>Markdown Source</span>
              <span className="text-[10px] text-text-muted font-mono">Auto-saving</span>
            </div>
            <textarea
              value={content}
              onChange={(e) => handleContentChange(e.target.value)}
              placeholder="Start writing markdown..."
              className="flex-1 w-full p-4 bg-transparent text-sm font-mono text-text-primary focus:outline-none resize-none leading-relaxed overflow-y-auto selection:bg-cyan-500/20"
              spellCheck={false}
            />
          </div>
        )}

        {/* Preview Pane */}
        {(viewMode === 'split' || viewMode === 'preview') && (
          <div className="flex flex-col h-full rounded-xl border border-border/60 bg-surface overflow-hidden">
            <div className="px-4 py-2 bg-surface-elevated/70 border-b border-border/40 text-xs font-semibold text-text-secondary flex items-center justify-between">
              <span>Live Rendered Preview</span>
              <span className="text-[10px] text-cyan-400 font-mono">Sanitized Preview</span>
            </div>
            <div className="flex-1 p-6 overflow-y-auto bg-surface-muted/30">
              <MarkdownRenderer content={content || '*Empty document*'} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
