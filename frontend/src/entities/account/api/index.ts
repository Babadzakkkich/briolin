import { apiClient } from '@/shared/api/client';
import type { SagaStatus } from '@/shared/api/saga';
import type { AccountResponse, AccountUpdateData } from '../model/types';

interface SagaAcceptedResponse {
  saga_id: string;
}

export const accountApi = {
  getMe: () => apiClient.get<AccountResponse>('/users/me'),

  updateMe: (keycloakId: string, data: AccountUpdateData) =>
    apiClient.put<SagaAcceptedResponse>(`/users/${keycloakId}`, data),

  deleteMe: (keycloakId: string) =>
    apiClient.delete<SagaAcceptedResponse>(`/users/${keycloakId}`),

  getSagaStatus: (sagaId: string) =>
    apiClient.get<SagaStatus>(`/users/saga/${sagaId}/status`),
};
