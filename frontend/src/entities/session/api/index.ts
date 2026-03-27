import { apiClient } from '@/shared/api/client';
import type { LoginRequest, RegisterRequest, TokenResponse, RegisterResponse } from '../model/types';

export const sessionApi = {
  login: (data: LoginRequest) => apiClient.post<TokenResponse>('/api/v1/auth/login', data),

  register: (data: RegisterRequest) =>
    apiClient.post<RegisterResponse>('/api/v1/auth/register', data),

  refresh: () => apiClient.post<TokenResponse>('/api/v1/auth/refresh'),

  logout: () => apiClient.post('/api/v1/auth/logout'),
};
