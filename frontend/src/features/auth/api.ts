import { apiClient } from '@/shared/api/client';

export interface LoginRequest {
    username: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
}

export interface RegisterResponse {
    status: string;
    saga_id: string;
    check_status_url: string;
}

export const authApi = {
    login: (data: LoginRequest) =>
        apiClient.post<TokenResponse>('/api/v1/auth/login', data),

    register: (data: RegisterRequest) =>
        apiClient.post<RegisterResponse>('/api/v1/auth/register', data),

    refresh: () =>
        apiClient.post<TokenResponse>('/api/v1/auth/refresh'),

    logout: () =>
        apiClient.post('/api/v1/auth/logout'),
};
