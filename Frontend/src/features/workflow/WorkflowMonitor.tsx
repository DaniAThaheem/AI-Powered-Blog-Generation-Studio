import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { useGenerationStream } from '../../hooks/useGenerationStream';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { PageHeader } from '../../components/shared/PageHeader';
import {
  Compass,
  Globe,
  ListOrdered,
  Cpu,
  GitMerge,
  Lightbulb,
  Image as ImageIcon,
  Database,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Play,
  FileText,
} from 'lucide-react';
import { StageType, StageStatus } from '../../api/types';

interface StageMeta {
  key: StageType;
  title: string;
  description: string;
  icon: React.FC<{ className?: string }>;
}

const STAGES: StageMeta[] = [
  {
    key: 'analyze_topic',
    title: '1. Topic Routing & Strategy',
    description: 'Gemini evaluates topic evergreenness and formulates search queries',
    icon: Compass,
  },
  {
    key: 'research',
    title: '2. Web Evidence Synthesis',
    description: 'Tavily retrieves authoritative URLs, deduplicates sources, and extracts facts',
    icon: Globe,
  },
  {
    key: 'plan',
    title: '3. Section Outline & Architecture',
    description: 'Structured blog planning: title, audience, ordered goals, and code requirements',
    icon: ListOrdered,
  },
  {
    key: 'write_sections',
    title: '4. Parallel Section Workers',
    description: 'LangGraph fan-out: concurrent workers draft technical sections',
    icon: Cpu,
  },
  {
    key: 'merge',
    title: '5. Deterministic Document Assembly',
    description: 'Sections merged and ordered deterministically using task identifiers',
    icon: GitMerge,
  },
  {
    key: 'plan_images',
    title: '6. Diagram & Visual Planning',
    description: 'Identifies technical figures and inserts placeholders (max 3)',
    icon: Lightbulb,
  },
  {
    key: 'generate_images',
    title: '7. Image Generation & Cloudinary Upload',
    description: 'Generates diagrams via Gemini and uploads to Cloudinary storage',
    icon: ImageIcon,
  },
  {
    key: 'save',
    title: '8. Durable Persistence',
    description: 'Saves blog Markdown, media references, and checkpoints',
    icon: Database,
  },
];

export const WorkflowMonitor: React.FC<{ generationId: string }> = ({ generationId }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [streamError, setStreamError] = useState<string | null>(null);

  // Load initial generation state
  const { data: generation, isLoading } = useQuery({
    queryKey: ['generation', generationId],
    queryFn: () => generationsApi.getById(generationId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'queued' || status === 'running' ? 4000 : false;
    },
  });

  const isTerminal = generation?.status === 'completed' || generation?.status === 'failed';
  const isInterrupted = generation?.status === 'interrupted';

  // Real-time SSE streaming
  const { isStreaming, isReconnecting, lastEvent } = useGenerationStream({
    generationId,
    enabled: !isTerminal,
    onError: (err) => setStreamError(err),
  });

  // Resume workflow mutation for HITL
  const resumeMutation = useMutation({
    mutationFn: () => generationsApi.resume(generationId, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['generation', generationId] });
    },
  });

  if (isLoading && !generation) {
    return (
      <div className="p-12 text-center text-xs text-text-muted flex items-center justify-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-primary" />
        Loading execution state...
      </div>
    );
  }

  const stageStatuses = generation?.stage_statuses || {};

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title={generation?.blog_title || generation?.topic || 'Workflow Execution'}
        description={`Generation ID: ${generationId}`}
        badge={<StatusBadge status={generation?.status || 'queued'} />}
        actions={
          <div className="flex items-center gap-2">
            {generation?.status === 'completed' && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate(`/blogs/${generationId}`)}
                  rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                >
                  View Completed Blog
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate(`/blogs/${generationId}/edit`)}
                >
                  Edit Markdown
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* Stream connection banner */}
      {isReconnecting && (
        <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800 text-xs text-amber-300 flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>Stream connection interrupted. Reconnecting with exponential backoff...</span>
        </div>
      )}

      {/* HITL approval banner */}
      {isInterrupted && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-surface border border-amber-700/60 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-semibold text-amber-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Human Approval Checkpoint
            </h4>
            <p className="text-xs text-text-secondary mt-1">
              Blog plan outline is ready. Review and approve the plan to proceed with parallel section generation.
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => resumeMutation.mutate()}
            isLoading={resumeMutation.isPending}
            leftIcon={<Play className="w-3.5 h-3.5" />}
          >
            Approve & Continue
          </Button>
        </div>
      )}

      {/* Error banner if failed */}
      {generation?.status === 'failed' && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-xs text-red-300 space-y-1">
          <p className="font-semibold text-red-200">Execution Error</p>
          <p>{generation.error_message || streamError || 'An unexpected error occurred during execution.'}</p>
        </div>
      )}

      {/* Non-fatal warnings */}
      {generation?.warnings && generation.warnings.length > 0 && (
        <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-xs text-amber-300/90 space-y-1">
          <div className="font-semibold flex items-center gap-1.5 text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Workflow Warnings (Recovered Gracefully)</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-[11px] text-text-secondary">
            {generation.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Stage Progression Timeline */}
      <Card className="glass-panel">
        <CardHeader className="py-4 flex flex-row items-center justify-between">
          <CardTitle>LangGraph Workflow Stages</CardTitle>
          <span className="text-[11px] font-mono text-cyan-400">
            {isStreaming ? 'Streaming Live' : generation?.status === 'completed' ? 'All Stages Complete' : 'Finished'}
          </span>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border/40">
            {STAGES.map((stage, idx) => {
              const status: StageStatus = stageStatuses[stage.key] || 'pending';
              const Icon = stage.icon;

              return (
                <div
                  key={stage.key}
                  className={`p-4 flex items-start justify-between gap-4 transition-colors ${
                    status === 'running'
                      ? 'bg-cyan-950/15 border-l-2 border-cyan-400'
                      : status === 'completed'
                      ? 'bg-surface/30'
                      : 'opacity-70'
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`p-2 rounded-lg flex-shrink-0 mt-0.5 ${
                        status === 'running'
                          ? 'bg-cyan-500/20 text-cyan-300 animate-pulse'
                          : status === 'completed'
                          ? 'bg-emerald-500/15 text-emerald-400'
                          : status === 'skipped'
                          ? 'bg-surface-elevated text-text-muted'
                          : 'bg-surface-elevated text-text-muted'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-text-primary flex items-center gap-2">
                        {stage.title}
                      </h4>
                      <p className="text-[11px] text-text-secondary mt-0.5 max-w-lg">
                        {stage.description}
                      </p>
                      {/* Active stage live status message */}
                      {lastEvent?.stage === stage.key && lastEvent.message && (
                        <p className="text-[11px] font-mono text-cyan-400 mt-1">
                          ↳ {lastEvent.message}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    <StatusBadge status={status} size="sm" />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
