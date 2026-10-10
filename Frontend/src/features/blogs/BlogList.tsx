import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Input, Select } from '../../components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui/Card';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { EmptyState } from '../../components/shared/EmptyState';
import { ConfirmDialog } from '../../components/shared/EmptyState';
import {
  Search,
  BookOpen,
  Calendar,
  Image as ImageIcon,
  FileText,
  Trash2,
  Edit3,
  ExternalLink,
  Plus,
  Download,
} from 'lucide-react';
import { GenerationSummary } from '../../api/types';

export const BlogList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<GenerationSummary | null>(null);

  const { data: blogs, isLoading } = useQuery({
    queryKey: ['generations', statusFilter, search],
    queryFn: () =>
      generationsApi.list({
        status: statusFilter || undefined,
        search: search.trim() || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => generationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generations'] });
      setDeleteTarget(null);
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Blogs"
        description="Browse, review, edit, and export your generated technical articles"
        actions={
          <Button
            variant="primary"
            onClick={() => navigate('/generate')}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Article
          </Button>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search blogs by title or topic..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface-elevated/70 border border-border rounded-lg pl-9 pr-3.5 py-2 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
        </div>

        <div className="w-full sm:w-48">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="running">In Progress</option>
            <option value="failed">Failed</option>
            <option value="queued">Queued</option>
          </select>
        </div>
      </div>

      {/* Blog Cards Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-xs text-text-muted">Loading articles...</div>
      ) : !blogs || blogs.length === 0 ? (
        <EmptyState
          title="No articles found"
          description={search ? "No blogs matched your search criteria." : "You haven't generated any blogs yet."}
          actionText="Create Your First Blog"
          onAction={() => navigate('/generate')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {blogs.map((blog) => (
            <Card
              key={blog.id}
              className="glass-card hover:border-cyan-500/40 transition-all flex flex-col justify-between"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-surface-elevated text-cyan-400 font-semibold">
                    {blog.blog_kind}
                  </span>
                  <StatusBadge status={blog.status} size="sm" />
                </div>
                <CardTitle className="line-clamp-2 text-sm leading-snug">
                  {blog.blog_title || blog.topic}
                </CardTitle>
                <p className="text-xs text-text-muted line-clamp-2 mt-1">
                  Topic: {blog.topic}
                </p>
              </CardHeader>

              <CardContent className="pt-0 pb-3">
                <div className="flex items-center gap-4 text-[11px] text-text-muted pt-2 border-t border-border/40">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(blog.created_at).toLocaleDateString()}
                  </span>
                  {blog.source_count > 0 && (
                    <span className="flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5 text-emerald-400" />
                      {blog.source_count} sources
                    </span>
                  )}
                  {blog.image_count > 0 && (
                    <span className="flex items-center gap-1">
                      <ImageIcon className="w-3.5 h-3.5 text-purple-400" />
                      {blog.image_count} images
                    </span>
                  )}
                </div>
              </CardContent>

              <CardFooter className="py-2.5 px-4 bg-surface-muted/40 border-t border-border/40 flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {blog.status === 'completed' ? (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/blogs/${blog.id}`)}
                        leftIcon={<BookOpen className="w-3.5 h-3.5" />}
                        className="text-xs"
                      >
                        Read
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/blogs/${blog.id}/edit`)}
                        leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                        className="text-xs"
                      >
                        Edit
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/generations/${blog.id}/progress`)}
                      leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
                      className="text-xs text-cyan-400"
                    >
                      Monitor
                    </Button>
                  )}
                </div>

                <button
                  onClick={() => setDeleteTarget(blog)}
                  className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-950/20 transition-colors"
                  title="Delete article"
                  aria-label="Delete article"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="Delete Blog"
        description={`Are you sure you want to delete "${deleteTarget?.blog_title || deleteTarget?.topic}"? This will permanently remove the generation record, Markdown text, and associated media references.`}
        confirmText="Delete Blog"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
