import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { EmptyState } from '../../components/shared/EmptyState';
import { ConfirmDialog } from '../../components/shared/EmptyState';
import { DocumentUploader } from './DocumentUploader';
import { RetrievalTester } from './RetrievalTester';
import {
  FileText,
  Trash2,
  Calendar,
  Layers,
  Database,
  ExternalLink,
  MessageSquare,
} from 'lucide-react';
import { DocumentRecord } from '../../api/types';

export const DocumentList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<DocumentRecord | null>(null);

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setDeleteTarget(null);
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reference Library (RAG)"
        description="Upload technical documentation, PDFs, and notes to ground blog generation and interactive chat"
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate('/chat')}
            leftIcon={<MessageSquare className="w-3.5 h-3.5 text-cyan-400" />}
          >
            Chat with Documents
          </Button>
        }
      />

      {/* Upload Zone */}
      <DocumentUploader />

      {/* Documents Table */}
      <Card className="glass-panel">
        <CardHeader className="py-4 flex flex-row items-center justify-between">
          <CardTitle>Indexed Reference Documents</CardTitle>
          <span className="text-xs text-text-muted font-mono">{documents?.length || 0} documents</span>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-text-muted">Loading documents...</div>
          ) : !documents || documents.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No documents uploaded"
                description="Upload PDFs or Markdown notes above to enable retrieval-augmented generation (RAG)."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-elevated/80 border-b border-border/50 text-text-secondary font-semibold">
                    <th className="p-3.5 pl-5">Document</th>
                    <th className="p-3.5">Type & Size</th>
                    <th className="p-3.5">Chunks</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Uploaded</th>
                    <th className="p-3.5 pr-5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-surface-elevated/30 transition-colors">
                      <td className="p-3.5 pl-5">
                        <div
                          onClick={() => navigate(`/documents/${doc.id}`)}
                          className="flex items-center gap-2.5 cursor-pointer group"
                        >
                          <div className="p-2 rounded-lg bg-surface-elevated text-cyan-400 group-hover:bg-cyan-950/40 transition-colors">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-semibold text-text-primary group-hover:text-cyan-400 transition-colors">
                              {doc.original_name}
                            </p>
                            <p className="text-[10px] font-mono text-text-muted truncate max-w-xs">{doc.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-3.5 uppercase font-mono text-text-secondary">
                        {doc.file_type} • {(doc.file_size / 1024).toFixed(1)} KB
                      </td>
                      <td className="p-3.5 font-mono text-cyan-400">
                        {doc.chunk_count} chunks
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={doc.status} size="sm" />
                      </td>
                      <td className="p-3.5 text-text-muted">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3.5 pr-5 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/documents/${doc.id}`)}
                            className="text-xs"
                          >
                            Inspect
                          </Button>
                          <button
                            onClick={() => setDeleteTarget(doc)}
                            className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-950/20 transition-colors"
                            title="Delete document and vector embeddings"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Retrieval Tester Sandbox */}
      <RetrievalTester />

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="Delete Document & Vectors"
        description={`Are you sure you want to delete "${deleteTarget?.original_name}"? This will permanently delete the file, all its chunks, and all corresponding embeddings from Pinecone.`}
        confirmText="Delete Document"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
