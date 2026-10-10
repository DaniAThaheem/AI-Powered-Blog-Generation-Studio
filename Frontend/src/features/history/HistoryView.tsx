import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { EmptyState } from '../../components/shared/EmptyState';
import {
  History,
  Calendar,
  Layers,
  ArrowRight,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

export const HistoryView: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState('');

  const { data: runs, isLoading } = useQuery({
    queryKey: ['generations_history', statusFilter],
    queryFn: () => generationsApi.list({ status: statusFilter || undefined, limit: 100 }),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Execution History"
        description="Durable log of all LangGraph multi-agent generation workflows and checkpoints"
      />

      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface-elevated border border-border rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        >
          <option value="">All Executions</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="queued">Queued</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <Card className="glass-panel">
        <CardHeader className="py-4 flex flex-row items-center justify-between">
          <CardTitle>Workflow Execution Records</CardTitle>
          <span className="text-xs text-text-muted font-mono">{runs?.length || 0} total</span>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-12 text-center text-xs text-text-muted">Loading history...</div>
          ) : !runs || runs.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No workflow executions found"
                description="Your past and current generation workflows will be durably tracked here."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-elevated/80 border-b border-border/50 text-text-secondary font-semibold">
                    <th className="p-3.5 pl-5">Topic / Title</th>
                    <th className="p-3.5">Thread ID</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Stage</th>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5 pr-5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {runs.map((run) => (
                    <tr key={run.id} className="hover:bg-surface-elevated/30 transition-colors">
                      <td className="p-3.5 pl-5 max-w-sm">
                        <p className="font-semibold text-text-primary truncate">{run.blog_title || run.topic}</p>
                        <p className="text-[10px] text-text-muted truncate mt-0.5">{run.topic}</p>
                      </td>
                      <td className="p-3.5 font-mono text-[11px] text-cyan-400">
                        {run.thread_id}
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={run.status} size="sm" />
                      </td>
                      <td className="p-3.5 text-text-muted capitalize">
                        {run.current_stage?.replace('_', ' ') || 'Queued'}
                      </td>
                      <td className="p-3.5 text-text-muted">
                        {new Date(run.created_at).toLocaleString()}
                      </td>
                      <td className="p-3.5 pr-5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              navigate(
                                run.status === 'completed'
                                  ? `/blogs/${run.id}`
                                  : `/generations/${run.id}/progress`
                              )
                            }
                            className="text-xs"
                          >
                            {run.status === 'completed' ? 'Open Blog' : 'Inspect'}
                          </Button>
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
    </div>
  );
};
