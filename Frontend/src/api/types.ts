import { z } from 'zod';

export type StageType =
  | 'analyze_topic'
  | 'research'
  | 'plan'
  | 'write_sections'
  | 'merge'
  | 'plan_images'
  | 'generate_images'
  | 'save';

export type StageStatus = 'pending' | 'running' | 'completed' | 'skipped' | 'failed';

export type GenerationStatus = 'queued' | 'running' | 'interrupted' | 'completed' | 'failed' | 'cancelled';

export interface Task {
  id: number;
  title: string;
  goal: string;
  bullets: string[];
  brief: string;
  target_word: number;
  tags?: string[];
  requires_research?: boolean;
  requires_citation?: boolean;
  requires_code?: boolean;
}

export interface Plan {
  blog_title: string;
  audience: string;
  tone: string;
  blog_kind: string;
  constraint: string[];
  tasks: Task[];
}

export interface Section {
  id: number;
  title: string;
  content: string;
}

export interface EvidenceItem {
  title: string;
  url: string;
  published_at?: string | null;
  snippet?: string | null;
  source?: string | null;
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number?: number | null;
  score?: number;
  content: string;
}

export interface ImageSpec {
  placeholder: string;
  filename: string;
  alt: string;
  caption: string;
  prompt: string;
  url?: string | null;
  cloudinary_public_id?: string | null;
}

export interface Generation {
  id: string;
  thread_id: string;
  topic: string;
  blog_title?: string | null;
  audience: string;
  tone: string;
  blog_kind: string;
  target_word_count: number;
  enable_research: boolean;
  enable_hitl: boolean;
  status: GenerationStatus;
  current_stage: string;
  stage_statuses: Record<string, StageStatus>;
  selected_document_ids: string[];
  plan?: Plan | null;
  sections: Section[];
  final_markdown?: string | null;
  evidence: EvidenceItem[];
  document_chunks_used: DocumentChunk[];
  image_specs: ImageSpec[];
  warnings: string[];
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GenerationSummary {
  id: string;
  thread_id: string;
  topic: string;
  blog_title?: string | null;
  blog_kind: string;
  status: GenerationStatus;
  current_stage: string;
  created_at: string;
  updated_at: string;
  image_count: number;
  source_count: number;
}

export interface CreateGenerationInput {
  topic: string;
  audience?: string;
  tone?: string;
  blog_kind?: string;
  target_word_count?: number;
  enable_research?: boolean;
  enable_hitl?: boolean;
  selected_document_ids?: string[];
}

export interface DocumentRecord {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  cloudinary_url?: string | null;
  status: 'uploaded' | 'extracting' | 'chunking' | 'indexing' | 'ready' | 'failed';
  chunk_count: number;
  extracted_text_preview?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaAsset {
  id: string;
  generation_id?: string | null;
  placeholder?: string | null;
  filename: string;
  alt_text?: string | null;
  caption?: string | null;
  prompt: string;
  cloudinary_url: string;
  cloudinary_public_id?: string | null;
  created_at: string;
}

export interface WorkflowEvent {
  event_type: 'stage' | 'warning' | 'interrupted' | 'completed' | 'failed' | 'ping';
  generation_id: string;
  stage?: StageType;
  stage_status?: StageStatus;
  message?: string;
  data?: any;
  timestamp: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  database: {
    status: 'connected' | 'disconnected';
    type: 'postgresql' | 'sqlite';
  };
  services: {
    gemini: { configured: boolean; text_model: string; image_model: string };
    tavily: { configured: boolean };
    pinecone: { configured: boolean; index_name: string; index_exists?: boolean | null; warning?: string | null };
    cloudinary: { configured: boolean; cloud_name?: string | null };
  };
}

export interface SettingsResponse {
  app_name: string;
  environment: string;
  max_upload_size_mb: number;
  models: {
    text_model: string;
    image_model: string;
    embedding_model: string;
  };
  providers: {
    gemini: { name: string; configured: boolean };
    tavily: { name: string; configured: boolean };
    pinecone: { name: string; configured: boolean; index_name: string; index_exists?: boolean | null; warning?: string | null };
    cloudinary: { name: string; configured: boolean };
    database: { name: string; type: string };
  };
}
