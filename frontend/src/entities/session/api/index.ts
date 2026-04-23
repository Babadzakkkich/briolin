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
};
