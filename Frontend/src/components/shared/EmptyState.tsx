import React from 'react';
import { Button } from '../ui/Button';
import { AlertCircle, FolderOpen, Check, Copy } from 'lucide-react';
import { Modal } from '../ui/Modal';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
}) => (
  <div className="flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-border/80 bg-surface/40 my-4">
    <div className="p-3 bg-surface-elevated text-text-secondary rounded-xl mb-3 shadow-inner">
      {icon || <FolderOpen className="w-8 h-8 text-text-muted" />}
    </div>
    <h3 className="text-base font-semibold text-text-primary mb-1">{title}</h3>
    <p className="text-xs sm:text-sm text-text-secondary max-w-sm mb-5">{description}</p>
    {actionText && onAction && (
      <Button variant="primary" size="sm" onClick={onAction}>
        {actionText}
      </Button>
    )}
  </div>
);

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center p-8 text-center rounded-xl border border-red-900/40 bg-red-950/20 my-4">
    <div className="p-3 bg-red-900/30 text-red-400 rounded-xl mb-3">
      <AlertCircle className="w-7 h-7" />
    </div>
    <h3 className="text-sm font-semibold text-text-primary mb-1">{title}</h3>
    <p className="text-xs text-text-secondary max-w-md mb-4">{message}</p>
    {onRetry && (
      <Button variant="secondary" size="sm" onClick={onRetry}>
        Try Again
      </Button>
    )}
  </div>
);

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  variant?: 'danger' | 'primary';
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Delete',
  variant = 'danger',
  isLoading = false,
}) => (
  <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="sm">
    <p className="text-xs sm:text-sm text-text-secondary mb-6 leading-relaxed">{description}</p>
    <div className="flex items-center justify-end gap-2.5">
      <Button variant="ghost" size="sm" onClick={onClose} disabled={isLoading}>
        Cancel
      </Button>
      <Button variant={variant} size="sm" onClick={onConfirm} isLoading={isLoading}>
        {confirmText}
      </Button>
    </div>
  </Modal>
);

export const CopyButton: React.FC<{ text: string; label?: string; className?: string }> = ({
  text,
  label = 'Copy',
  className = '',
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy text', e);
    }
  };

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleCopy}
      leftIcon={copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      className={className}
    >
      {copied ? 'Copied!' : label}
    </Button>
  );
};
