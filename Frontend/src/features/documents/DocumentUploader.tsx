import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import { Button } from '../../components/ui/Button';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

const ALLOWED_EXTS = ['.pdf', '.txt', '.md'];
const MAX_SIZE_MB = 25;

export const DocumentUploader: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(file),
    onSuccess: (data) => {
      setSuccessMsg(`Document "${data.original_name}" uploaded and indexed successfully (${data.chunk_count} chunks).`);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Upload failed');
      setSuccessMsg(null);
    },
  });

  const handleFile = (file: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) {
      setErrorMsg(`Invalid file type "${ext}". Supported formats: ${ALLOWED_EXTS.join(', ')}`);
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File exceeds maximum size of ${MAX_SIZE_MB}MB`);
      return;
    }

    uploadMutation.mutate(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-8 border-2 border-dashed rounded-xl text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-cyan-400 bg-cyan-950/20'
            : 'border-border/80 bg-surface/40 hover:border-border hover:bg-surface-elevated/30'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-2">
          <div className="p-3 bg-surface-elevated rounded-xl text-cyan-400 shadow-inner">
            {uploadMutation.isPending ? (
              <RefreshCw className="w-6 h-6 animate-spin text-primary" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>
          <h4 className="text-sm font-semibold text-text-primary">
            {uploadMutation.isPending ? 'Processing, Chunking & Indexing...' : 'Upload Reference Document'}
          </h4>
          <p className="text-xs text-text-secondary max-w-sm">
            Drag and drop your PDF, TXT, or MD documents here, or click to browse.
          </p>
          <span className="text-[10px] text-text-muted font-mono">
            Supported: PDF, TXT, MD • Max {MAX_SIZE_MB}MB
          </span>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-red-950/30 border border-red-800 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
