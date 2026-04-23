import { apiClient } from '@/shared/api/client';
import type {
  BasicProfileData,
  ProfileResponse,
  ProfileUpdateData,
  DetailedProfileData,
} from '../model/types';

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/profiles/basic', data),
  createDetailed: (data: DetailedProfileData) => apiClient.post('/profiles/detailed', data),
  getMe: () => apiClient.get<ProfileResponse>('/profiles/me'),
  updateMe: (data: ProfileUpdateData) => apiClient.put('/profiles/me', data),
  getByKeycloakId: (keycloakId: string) =>
    apiClient.get<ProfileResponse>(`/profiles/${keycloakId}`),
};
