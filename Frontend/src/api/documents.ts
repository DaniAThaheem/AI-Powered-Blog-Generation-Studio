import { apiClient } from './client';
import { DocumentRecord } from './types';

export const documentsApi = {
  list: (status?: string) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient<DocumentRecord[]>(`/api/documents${query}`);
  },

  getById: (id: string) =>
    apiClient<DocumentRecord>(`/api/documents/${id}`),

  getChunks: (id: string) =>
    apiClient<any[]>(`/api/documents/${id}/chunks`),

  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient<DocumentRecord>('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  delete: (id: string) =>
    apiClient<{ message: string; id: string }>(`/api/documents/${id}`, {
      method: 'DELETE',
    }),

  retrieve: (query: string, documentIds?: string[], topK: number = 4) =>
    apiClient<{ query: string; results: any[] }>('/api/documents/retrieve', {
      method: 'POST',
      body: JSON.stringify({
        query,
        document_ids: documentIds,
        top_k: topK,
      }),
    }),
};
