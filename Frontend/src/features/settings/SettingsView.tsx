import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { settingsApi } from '../../api/chat';
import { PageHeader } from '../../components/shared/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, Select } from '../../components/ui/Input';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Database,
  Cpu,
  Globe,
  HardDrive,
  Save,
  Info,
} from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings(),
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => settingsApi.getHealth(),
  });

  const [defaultTone, setDefaultTone] = useState(
    localStorage.getItem('blog_default_tone') || 'Technical and Engaging'
  );
  const [defaultKind, setDefaultKind] = useState(
    localStorage.getItem('blog_default_kind') || 'explainer'
  );
  const [savedNotice, setSavedNotice] = useState(false);

  const handleSavePreferences = () => {
    localStorage.setItem('blog_default_tone', defaultTone);
    localStorage.setItem('blog_default_kind', defaultKind);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2000);
  };

  const providers = settings?.providers;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Settings & Diagnostics"
        description="Inspect backend integrations, service connectivity, and configure UI defaults"
      />

      {/* Integration Connectivity Grid */}
      <Card className="glass-panel">
        <CardHeader>
          <div className="flex items-center gap-2 text-cyan-400 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-[10px] font-mono font-semibold uppercase">Security & Service Status</span>
          </div>
          <CardTitle>Connected Service Integrations</CardTitle>
          <CardDescription>
            Live status verified by the FastAPI backend. Secrets remain securely on the server.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Gemini */}
            <div className="p-3.5 rounded-xl bg-surface-elevated/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/20 text-primary-light">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">Large Language Model</h4>
                  <p className="text-[10px] text-text-muted font-mono">{settings?.models?.text_model || 'gemini-flash-latest'}</p>
                </div>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1 ${
                  providers?.gemini?.configured
                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                    : 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                }`}
              >
                {providers?.gemini?.configured ? <CheckCircle2 className="w-3 h-3" /> : <Info className="w-3 h-3" />}
                {providers?.gemini?.configured ? 'Active' : 'Unconfigured'}
              </span>
            </div>

            {/* Tavily */}
            <div className="p-3.5 rounded-xl bg-surface-elevated/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-950/40 text-cyan-400">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">Tavily Web Search</h4>
                  <p className="text-[10px] text-text-muted">Web evidence retrieval</p>
                </div>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1 ${
                  providers?.tavily?.configured
                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                    : 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                }`}
              >
                {providers?.tavily?.configured ? <CheckCircle2 className="w-3 h-3" /> : <Info className="w-3 h-3" />}
                {providers?.tavily?.configured ? 'Active' : 'Offline'}
              </span>
            </div>

            {/* Database */}
            <div className="p-3.5 rounded-xl bg-surface-elevated/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-950/40 text-emerald-400">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">Application Database</h4>
                  <p className="text-[10px] text-text-muted capitalize">
                    {health?.database?.type || 'SQLite / PostgreSQL'}
                  </p>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Connected
              </span>
            </div>

            {/* Pinecone */}
            <div className="p-3.5 rounded-xl bg-surface-elevated/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-950/40 text-purple-400">
                  <HardDrive className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-text-primary">Pinecone Vector DB</h4>
                  <p className="text-[10px] text-text-muted font-mono">{settings?.providers?.pinecone?.index_name || 'blog-rag'}</p>
                  {providers?.pinecone?.warning && (
                    <p className="text-[10px] text-amber-400/90 font-mono mt-0.5">{providers.pinecone.warning}</p>
                  )}
                </div>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1 ${
                  providers?.pinecone?.configured
                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                    : 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/60'
                }`}
              >
                {providers?.pinecone?.configured ? 'Cloud Index' : 'Local Vector Store'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generation Defaults */}
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle>Default Generation Preferences</CardTitle>
          <CardDescription>
            Personalize your default preferences for tone and article format across generation sessions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Default Writing Tone"
              value={defaultTone}
              onChange={(e) => setDefaultTone(e.target.value)}
              options={[
                { value: 'Technical and Engaging', label: 'Technical and Engaging' },
                { value: 'Rigorous and Academic', label: 'Rigorous and Academic' },
                { value: 'Practical and Hands-on', label: 'Practical and Hands-on' },
                { value: 'Architectural and High-level', label: 'Architectural and High-level' },
              ]}
            />

            <Select
              label="Default Article Format"
              value={defaultKind}
              onChange={(e) => setDefaultKind(e.target.value)}
              options={[
                { value: 'explainer', label: 'Technical Explainer' },
                { value: 'tutorial', label: 'Step-by-Step Tutorial' },
                { value: 'comparison', label: 'Architecture Comparison' },
                { value: 'system_design', label: 'System Design Spec' },
              ]}
            />
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-border/40">
            {savedNotice ? (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Preferences saved!
              </span>
            ) : (
              <span />
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={handleSavePreferences}
              leftIcon={<Save className="w-3.5 h-3.5" />}
            >
              Save Preferences
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
