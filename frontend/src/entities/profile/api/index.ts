import { apiClient } from '@/shared/api/client';
import type { BasicProfileData, ProfileResponse, ProfileUpdateData, DetailedProfileData } from '../model/types';

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/api/v1/profiles/basic', data),
  createDetailed: (data: DetailedProfileData) => apiClient.post('/api/v1/profiles/detailed', data),
  getMe: () => apiClient.get<ProfileResponse>('/api/v1/profiles/me'),
  updateMe: (data: ProfileUpdateData) => apiClient.put('/api/v1/profiles/me', data),
};
