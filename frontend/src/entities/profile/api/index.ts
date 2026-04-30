import { apiClient } from '@/shared/api/client';
import type {
  BasicProfileData,
  ProfileResponse,
  ProfileUpdateData,
  DetailedProfileData,
  ProfileQuestions,
  QuestionsStatus,
} from '../model/types';

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/profiles/basic', data),
  createDetailed: (data: DetailedProfileData) => apiClient.post('/profiles/detailed', data),
  getMe: () => apiClient.get<ProfileResponse>('/profiles/me'),
  updateMe: (data: ProfileUpdateData) => apiClient.put('/profiles/me', data),
  getByKeycloakId: (keycloakId: string, signal?: AbortSignal) =>
    apiClient.get<ProfileResponse>(`/profiles/${keycloakId}`, { signal }),
  getMyQuestions: () => apiClient.get<ProfileQuestions>('/profiles/me/questions'),
  getQuestionsStatus: () => apiClient.get<QuestionsStatus>('/profiles/me/questions/status'),
  createOrUpdateQuestions: (data: Omit<ProfileQuestions, 'created_at' | 'updated_at'>) =>
    apiClient.post<ProfileResponse>('/profiles/me/questions', data),
  getUserQuestions: (keycloakId: string, signal?: AbortSignal) =>
    apiClient.get<ProfileQuestions>(`/profiles/${keycloakId}/questions`, { signal }),
};
