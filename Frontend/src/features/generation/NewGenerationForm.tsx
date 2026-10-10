import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { generationsApi } from '../../api/generations';
import { documentsApi } from '../../api/documents';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Input, Textarea, Select } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Sparkles, Globe, FileText, Check, ShieldCheck, Info } from 'lucide-react';

export const NewGenerationForm: React.FC = () => {
  const navigate = useNavigate();

  // Load defaults from localStorage
  const savedTone = localStorage.getItem('blog_default_tone') || 'Technical and Engaging';
  const savedKind = localStorage.getItem('blog_default_kind') || 'explainer';

  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('Developers & Technical Practitioners');
  const [tone, setTone] = useState(savedTone);
  const [blogKind, setBlogKind] = useState(savedKind);
  const [targetWordCount, setTargetWordCount] = useState<number>(1500);
  const [enableResearch, setEnableResearch] = useState(true);
  const [enableHitl, setEnableHitl] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch available ready reference documents for RAG
  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list('ready'),
  });

  const createMutation = useMutation({
    mutationFn: generationsApi.create,
    onSuccess: (data) => {
      // Save non-sensitive defaults to localStorage
      localStorage.setItem('blog_default_tone', tone);
      localStorage.setItem('blog_default_kind', blogKind);
      // Navigate to Workflow Monitor
      navigate(`/generations/${data.id}/progress`);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to start generation workflow');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!topic.trim() || topic.trim().length < 3) {
      setErrorMsg('Please enter a blog topic of at least 3 characters.');
      return;
    }

    createMutation.mutate({
      topic: topic.trim(),
      audience,
      tone,
      blog_kind: blogKind,
      target_word_count: targetWordCount,
      enable_research: enableResearch,
      enable_hitl: enableHitl,
      selected_document_ids: selectedDocIds,
    });
  };

  const toggleDoc = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl mx-auto">
      <Card className="glass-panel">
        <CardHeader>
          <div className="flex items-center gap-2 text-cyan-400 mb-1">
            <Sparkles className="w-4 h-4" />
            <span className="text-xs font-mono font-semibold uppercase tracking-wider">Multi-Agent Studio</span>
          </div>
          <CardTitle>Configure New Blog Generation</CardTitle>
          <CardDescription>
            Specify your technical topic and authoring preferences. The LangGraph agent graph will orchestrate research, planning, parallel section workers, and diagrams.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {errorMsg && (
            <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-xs text-red-300">
              {errorMsg}
            </div>
          )}

          {/* Topic */}
          <div>
            <Textarea
              label="Blog Topic or Premise"
              required
              rows={3}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Deep dive into LangGraph multi-agent orchestration, state reducers, and human-in-the-loop checkpointing"
              helperText="Be specific. Mention particular libraries, comparison targets, or architectural questions."
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Blog Format */}
            <Select
              label="Article Format"
              value={blogKind}
              onChange={(e) => setBlogKind(e.target.value)}
              options={[
                { value: 'explainer', label: 'Technical Explainer (Concept Deep Dive)' },
                { value: 'tutorial', label: 'Step-by-Step Tutorial & Code Guide' },
                { value: 'comparison', label: 'Architecture Comparison & Trade-offs' },
                { value: 'system_design', label: 'System Design & Engineering Spec' },
                { value: 'new_roundup', label: 'Ecosystem & News Roundup' },
              ]}
            />

            {/* Target Word Count */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Target Word Count: <span className="font-mono text-cyan-400">{targetWordCount} words</span>
              </label>
              <input
                type="range"
                min={600}
                max={4000}
                step={100}
                value={targetWordCount}
                onChange={(e) => setTargetWordCount(Number(e.target.value))}
                className="w-full accent-primary h-2 bg-surface-elevated rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-text-muted mt-1">
                <span>Quick Read (600w)</span>
                <span>Standard (1500w)</span>
                <span>Deep Spec (4000w)</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Audience */}
            <Input
              label="Target Audience"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              placeholder="e.g. Senior Backend Engineers, AI Researchers"
            />

            {/* Tone */}
            <Select
              label="Writing Tone"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              options={[
                { value: 'Technical and Engaging', label: 'Technical and Engaging' },
                { value: 'Rigorous and Academic', label: 'Rigorous and Academic' },
                { value: 'Practical and Hands-on', label: 'Practical and Hands-on' },
                { value: 'Architectural and High-level', label: 'Architectural and High-level' },
              ]}
            />
          </div>

          {/* Workflow Switches */}
          <div className="pt-2 border-t border-border/50 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Research toggle */}
            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-border/60 bg-surface-elevated/40 cursor-pointer hover:border-cyan-500/40 transition-colors">
              <input
                type="checkbox"
                checked={enableResearch}
                onChange={(e) => setEnableResearch(e.target.checked)}
                className="mt-1 w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
              />
              <div>
                <div className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-xs font-semibold text-text-primary">Tavily Web Research</span>
                </div>
                <p className="text-[11px] text-text-secondary mt-0.5">
                  Autonomously query the web for real docs, benchmarks, and citations.
                </p>
              </div>
            </label>

            {/* HITL approval toggle */}
            <label className="flex items-start gap-3 p-3.5 rounded-xl border border-border/60 bg-surface-elevated/40 cursor-pointer hover:border-cyan-500/40 transition-colors">
              <input
                type="checkbox"
                checked={enableHitl}
                onChange={(e) => setEnableHitl(e.target.checked)}
                className="mt-1 w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
              />
              <div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs font-semibold text-text-primary">Human-in-the-Loop Approval</span>
                </div>
                <p className="text-[11px] text-text-secondary mt-0.5">
                  Pause workflow after planning so you can inspect/approve the outline.
                </p>
              </div>
            </label>
          </div>

          {/* Reference Documents (RAG) Multi-select */}
          <div className="pt-2 border-t border-border/50">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                Select Reference Documents for RAG (Optional)
              </label>
              <span className="text-[10px] text-text-muted font-mono">
                {selectedDocIds.length} selected
              </span>
            </div>

            {!documents || documents.length === 0 ? (
              <div className="p-3 rounded-lg bg-surface-muted/50 border border-border/40 text-xs text-text-secondary flex items-center justify-between">
                <span>No indexed reference documents available yet.</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/documents')}
                  className="text-cyan-400 text-xs"
                >
                  Upload PDFs →
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1">
                {documents.map((doc) => {
                  const isSelected = selectedDocIds.includes(doc.id);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => toggleDoc(doc.id)}
                      className={`p-2.5 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                        isSelected
                          ? 'border-cyan-500 bg-cyan-950/20 text-text-primary'
                          : 'border-border/60 bg-surface-elevated/40 text-text-secondary hover:border-border'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <p className="font-medium truncate">{doc.original_name}</p>
                        <p className="text-[10px] text-text-muted">{doc.chunk_count} chunks</p>
                      </div>
                      <div
                        className={`w-4 h-4 rounded flex items-center justify-center border ${
                          isSelected
                            ? 'bg-cyan-500 border-cyan-400 text-black'
                            : 'border-border'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Info className="w-3.5 h-3.5" />
            <span>Workflow takes 30-90s depending on research depth</span>
          </div>
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={createMutation.isPending}
            disabled={createMutation.isPending || !topic.trim()}
            leftIcon={<Sparkles className="w-4 h-4" />}
          >
            {createMutation.isPending ? 'Initiating Workflow...' : 'Launch Generation'}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
};
