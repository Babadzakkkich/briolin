import { apiClient } from '@/shared/api/client';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RegisterResponse,
} from '../model/types';

export const sessionApi = {
  login: (data: LoginRequest) => apiClient.post<TokenResponse>('/auth/login', data),

  register: (data: RegisterRequest) => apiClient.post<RegisterResponse>('/auth/register', data),

  refresh: () => apiClient.post<TokenResponse>('/auth/refresh'),

  logout: () => apiClient.post('/auth/logout'),

  requestVerification: () => apiClient.post<{ message: string }>('/auth/verify/request'),

  confirmVerification: (code: string) =>
    apiClient.post<{ message: string }>('/auth/verify/confirm', { code }),

  requestPasswordReset: (email: string) =>
    apiClient.post<{ message: string }>('/auth/password-reset/request', { email }),

  confirmPasswordReset: (email: string, code: string, new_password: string) =>
    apiClient.post<{ message: string }>('/auth/password-reset/confirm', {
      email,
      code,
      new_password,
    }),
};
