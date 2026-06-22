import { apiClient } from '@/shared/api/client';
import type { SagaStatus } from '@/shared/api/saga';
import type {
  BasicProfileData,
  ProfileResponse,
  ProfileUpdateData,
  DetailedProfileData,
  ProfileQuestions,
  QuestionsStatus,
} from '../model/types';

interface SagaAcceptedResponse {
  saga_id: string;
}

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/profiles/basic', data),
  createDetailed: (data: DetailedProfileData) => apiClient.post('/profiles/detailed', data),
  getMe: () => apiClient.get<ProfileResponse>('/profiles/me'),
  updateMe: (data: ProfileUpdateData) => apiClient.put('/profiles/me', data),
  deleteProfile: () => apiClient.delete<SagaAcceptedResponse>('/profiles/me'),
  getByKeycloakId: (keycloakId: string, signal?: AbortSignal) =>
    apiClient.get<ProfileResponse>(`/profiles/${keycloakId}`, { signal }),
  getMyQuestions: () => apiClient.get<ProfileQuestions>('/profiles/me/questions'),
  getQuestionsStatus: () => apiClient.get<QuestionsStatus>('/profiles/me/questions/status'),
  createOrUpdateQuestions: (data: Omit<ProfileQuestions, 'created_at' | 'updated_at'>) =>
    apiClient.post<ProfileResponse>('/profiles/me/questions', data),
  patchQuestion: (key: keyof Omit<ProfileQuestions, 'created_at' | 'updated_at'>, value: string) =>
    apiClient.patch<ProfileResponse>('/profiles/me/questions', { [key]: value }),
  getUserQuestions: (keycloakId: string, signal?: AbortSignal) =>
    apiClient.get<ProfileQuestions>(`/profiles/${keycloakId}/questions`, { signal }),
  getSagaStatus: (sagaId: string) => apiClient.get<SagaStatus>(`/profiles/saga/${sagaId}/status`),
};
