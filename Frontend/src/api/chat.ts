import { apiClient } from './client';
import { HealthResponse, SettingsResponse } from './types';

export const chatApi = {
  sendMessage: (message: string, history: Array<{ role: string; content: string }> = [], selectedDocumentIds: string[] = []) =>
    apiClient<{ reply: string; sources: any[] }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history,
        selected_document_ids: selectedDocumentIds,
      }),
    }),
};

export const settingsApi = {
  getHealth: () =>
    apiClient<HealthResponse>('/api/health'),

  getSettings: () =>
    apiClient<SettingsResponse>('/api/settings'),
};
