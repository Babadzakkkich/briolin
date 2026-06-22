import { apiClient } from '@/shared/api/client';
import type { SagaStatus } from '@/shared/api/saga';
import type { UserRole } from '@/entities/account';
import type { AdminUser, AdminUserList, AdminProfileResponse, MatchingResetResponse } from '../model/types';

interface SagaAcceptedResponse {
  saga_id: string;
}

export const adminApi = {
  listUsers: (params: { skip?: number; limit?: number }) =>
    apiClient.get<AdminUserList>('/users/', { params }).then((r) => r.data),

  listByRole: (role: UserRole, params: { skip?: number; limit?: number }) =>
    apiClient.get<AdminUserList>(`/users/role/${role}`, { params }).then((r) => r.data),

  getUserById: (keycloakId: string) =>
    apiClient.get<AdminUser>(`/users/${keycloakId}`).then((r) => r.data),

  getUserByUsername: (username: string) =>
    apiClient.get<AdminUser>(`/users/username/${username}`).then((r) => r.data),

  getUserByEmail: (email: string) =>
    apiClient.get<AdminUser>(`/users/email/${email}`).then((r) => r.data),

  updateRoles: (keycloakId: string, roles: UserRole[]) =>
    apiClient.put<SagaAcceptedResponse>(`/users/${keycloakId}/roles`, { roles }).then((r) => r.data),

  toggleStatus: (keycloakId: string) =>
    apiClient.patch<SagaAcceptedResponse>(`/users/${keycloakId}/toggle-status`).then((r) => r.data),

  deleteUser: (keycloakId: string) =>
    apiClient.delete<SagaAcceptedResponse>(`/users/${keycloakId}`).then((r) => r.data),

  getUserSagaStatus: (sagaId: string) =>
    apiClient.get<SagaStatus>(`/users/saga/${sagaId}/status`).then((r) => r.data),

  getUserProfile: (keycloakId: string) =>
    apiClient.get<AdminProfileResponse>(`/profiles/${keycloakId}`).then((r) => r.data),

  deleteUserProfile: (keycloakId: string) =>
    apiClient.delete<SagaAcceptedResponse>(`/profiles/${keycloakId}`).then((r) => r.data),

  getProfileSagaStatus: (sagaId: string) =>
    apiClient.get<SagaStatus>(`/profiles/saga/${sagaId}/status`).then((r) => r.data),

  resetUserMatching: (userId: string) =>
    apiClient.delete<MatchingResetResponse>(`/matching/admin/reset/${userId}`).then((r) => r.data),
};
