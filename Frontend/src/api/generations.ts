import { apiClient } from './client';
import {
  Generation,
  GenerationSummary,
  CreateGenerationInput,
} from './types';

export const generationsApi = {
  create: (data: CreateGenerationInput) =>
    apiClient<Generation>('/api/generations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  list: (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    const query = searchParams.toString();
    return apiClient<GenerationSummary[]>(`/api/generations${query ? `?${query}` : ''}`);
  },

  getById: (id: string) =>
    apiClient<Generation>(`/api/generations/${id}`),

  update: (id: string, data: { blog_title?: string; final_markdown?: string }) =>
    apiClient<Generation>(`/api/generations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    apiClient<{ message: string; id: string }>(`/api/generations/${id}`, {
      method: 'DELETE',
    }),

  resume: (id: string, decision: any = true) =>
    apiClient<Generation>(`/api/generations/${id}/resume`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  exportMarkdownUrl: (id: string) => {
    const base = import.meta.env.VITE_API_BASE_URL || '';
    return `${base}/api/generations/${id}/export`;
  },
};
