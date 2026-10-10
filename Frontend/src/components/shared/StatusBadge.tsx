import React from 'react';
import { Badge } from '../ui/Badge';
import { CheckCircle2, Clock, AlertTriangle, XCircle, PauseCircle, SkipForward } from 'lucide-react';
import { GenerationStatus, StageStatus } from '../../api/types';

interface StatusBadgeProps {
  status: GenerationStatus | StageStatus | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md', className = '' }) => {
  const norm = status?.toLowerCase() || 'pending';

  switch (norm) {
    case 'completed':
      return (
        <Badge variant="success" size={size} className={className}>
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Completed
        </Badge>
      );
    case 'running':
      return (
        <Badge variant="info" size={size} className={className}>
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse mr-1.5" />
          Running
        </Badge>
      );
    case 'queued':
    case 'pending':
      return (
        <Badge variant="default" size={size} className={className}>
          <Clock className="w-3 h-3 mr-1 text-text-muted" />
          {norm === 'queued' ? 'Queued' : 'Pending'}
        </Badge>
      );
    case 'interrupted':
      return (
        <Badge variant="warning" size={size} className={className}>
          <PauseCircle className="w-3 h-3 mr-1" />
          Waiting Approval
        </Badge>
      );
    case 'skipped':
      return (
        <Badge variant="outline" size={size} className={className}>
          <SkipForward className="w-3 h-3 mr-1 text-text-muted" />
          Skipped
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="danger" size={size} className={className}>
          <XCircle className="w-3 h-3 mr-1" />
          Failed
        </Badge>
      );
    case 'ready':
      return (
        <Badge variant="success" size={size} className={className}>
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Ready
        </Badge>
      );
    case 'indexing':
    case 'extracting':
    case 'chunking':
      return (
        <Badge variant="info" size={size} className={className}>
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping mr-1.5" />
          {norm.charAt(0).toUpperCase() + norm.slice(1)}
        </Badge>
      );
    default:
      return (
        <Badge variant="default" size={size} className={className}>
          {norm}
        </Badge>
      );
  }
};
