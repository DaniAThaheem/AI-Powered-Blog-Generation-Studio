import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { CopyButton } from '../../components/shared/EmptyState';
import {
  FileText,
  Calendar,
  Layers,
  HardDrive,
  ArrowLeft,
  ExternalLink,
  BookOpen,
} from 'lucide-react';

export const DocumentDetails: React.FC<{ documentId: string }> = ({ documentId }) => {
  const navigate = useNavigate();

  const { data: document, isLoading } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => documentsApi.getById(documentId),
  });

  const { data: chunks } = useQuery({
    queryKey: ['document_chunks', documentId],
    queryFn: () => documentsApi.getChunks(documentId),
  });

  if (isLoading && !document) {
    return <div className="p-12 text-center text-xs text-text-muted">Loading document...</div>;
  }

  if (!document) {
    return <div className="p-8 text-center text-xs text-red-400">Document not found</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/documents')}
          leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
          className="text-xs"
        >
          Back to Reference Library
        </Button>
      </div>

      <PageHeader
        title={document.original_name}
        description={`Document ID: ${document.id}`}
        badge={<StatusBadge status={document.status} />}
        actions={
          document.cloudinary_url && (
            <a href={document.cloudinary_url} target="_blank" rel="noopener noreferrer">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
              >
                Open File
              </Button>
            </a>
          )
        }
      />

      {/* Metadata Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-surface border border-border/50">
          <p className="text-[11px] text-text-muted">Format</p>
          <p className="text-xs font-semibold text-text-primary uppercase mt-0.5">{document.file_type}</p>
        </div>
        <div className="p-3.5 rounded-xl bg-surface border border-border/50">
          <p className="text-[11px] text-text-muted">File Size</p>
          <p className="text-xs font-semibold text-text-primary mt-0.5">{(document.file_size / 1024).toFixed(1)} KB</p>
        </div>
        <div className="p-3.5 rounded-xl bg-surface border border-border/50">
          <p className="text-[11px] text-text-muted">Indexed Chunks</p>
          <p className="text-xs font-semibold text-cyan-400 font-mono mt-0.5">{document.chunk_count}</p>
        </div>
        <div className="p-3.5 rounded-xl bg-surface border border-border/50">
          <p className="text-[11px] text-text-muted">Uploaded</p>
          <p className="text-xs font-semibold text-text-primary mt-0.5">{new Date(document.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      {/* Extracted Text Preview */}
      {document.extracted_text_preview && (
        <Card className="glass-panel">
          <CardHeader className="py-3 flex flex-row items-center justify-between">
            <CardTitle>Extracted Text Preview</CardTitle>
            <CopyButton text={document.extracted_text_preview} label="Copy Preview" />
          </CardHeader>
          <CardContent className="p-4">
            <pre className="text-xs text-text-secondary font-mono leading-relaxed bg-surface-muted/40 p-3.5 rounded-lg border border-border/30 whitespace-pre-wrap max-h-48 overflow-y-auto">
              {document.extracted_text_preview}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Chunks List */}
      <Card className="glass-panel">
        <CardHeader className="py-4 flex flex-row items-center justify-between">
          <CardTitle>Vector Chunks ({chunks?.length || document.chunk_count})</CardTitle>
          <span className="text-[11px] text-text-muted font-mono">Pinecone Namespace: blog_docs</span>
        </CardHeader>
        <CardContent className="p-0">
          {!chunks || chunks.length === 0 ? (
            <div className="p-6 text-center text-xs text-text-muted">No chunks found</div>
          ) : (
            <div className="divide-y divide-border/40 max-h-[600px] overflow-y-auto">
              {chunks.map((c: any) => (
                <div key={c.id} className="p-4 space-y-1.5 hover:bg-surface-elevated/20 transition-colors">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-cyan-400 font-semibold">Chunk #{c.chunk_index}</span>
                    {c.page_number && <span className="text-text-muted">Page {c.page_number}</span>}
                  </div>
                  <p className="text-xs text-text-secondary font-mono leading-relaxed bg-surface-muted/50 p-3 rounded-lg border border-border/30">
                    {c.text_content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
