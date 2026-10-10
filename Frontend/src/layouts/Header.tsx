import React from 'react';
import { Menu, Plus, Activity, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { settingsApi } from '../api/chat';

interface HeaderProps {
  onToggleMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileMenu }) => {
  const navigate = useNavigate();

  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: settingsApi.getHealth,
    refetchInterval: 30000,
  });

  const isHealthy = health?.status === 'healthy';

  return (
    <header className="h-14 border-b border-border/50 bg-surface/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="hidden sm:inline-block text-xs font-medium text-text-muted">
          AI Technical Blog Studio
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend health status badge */}
        <div
          onClick={() => navigate('/settings')}
          className="cursor-pointer px-2.5 py-1 rounded-full bg-surface-elevated border border-border/50 text-[11px] flex items-center gap-2 hover:border-cyan-500/50 transition-colors"
          title="Click to view detailed service diagnostics"
        >
          {isLoading ? (
            <RefreshCw className="w-3 h-3 text-text-muted animate-spin" />
          ) : isHealthy ? (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-amber-400" />
          )}
          <span className="text-text-secondary font-mono text-[10px]">
            {isLoading ? 'Checking...' : isHealthy ? 'API Online' : 'Degraded'}
          </span>
        </div>

        {/* Generate quick button */}
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/generate')}
          leftIcon={<Plus className="w-3.5 h-3.5" />}
        >
          New Blog
        </Button>
      </div>
    </header>
  );
};
