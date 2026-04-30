import { apiClient } from '@/shared/api/client';

export interface AvatarUploadResponse {
  avatar_id: string;
  url: string;
  thumbnail_url: string;
  width: number;
  height: number;
  file_size: number;
}

export interface AvatarHistoryItem {
  avatar_id: string;
  url: string;
  thumbnail_url: string;
  width: number;
  height: number;
  file_size: number;
  is_current: boolean;
  created_at: string;
  file_name: string;
}

export const mediaApi = {
  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.post<AvatarUploadResponse>('/media/avatar', form);
  },

  deleteCurrentAvatar: () =>
    apiClient.delete<{ deleted: boolean; avatar_id: string }>('/media/my-avatar'),

  getAvatarHistory: () => apiClient.get<AvatarHistoryItem[]>('/media/avatars'),

  setCurrentAvatar: (avatarId: string) =>
    apiClient.put<{ message: string }>(`/media/avatar/${avatarId}/set-current`),
};
