import { apiClient } from './client';
import { MediaAsset } from './types';

export const mediaApi = {
  list: (generationId?: string) => {
    const query = generationId ? `?generation_id=${encodeURIComponent(generationId)}` : '';
    return apiClient<MediaAsset[]>(`/api/media${query}`);
  },

  delete: (id: string) =>
    apiClient<{ message: string; id: string }>(`/api/media/${id}`, {
      method: 'DELETE',
    }),
};
