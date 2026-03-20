import axios from 'axios';
import { useAuthStore } from '@/shared/stores/authStore';

export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
    withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

let isRefreshing = false;
let failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
    failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
    failedQueue = [];
};

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config;

        const isAuthEndpoint = original.url?.includes('/api/v1/auth/');
        if (error.response?.status !== 401 || original._retry || isAuthEndpoint) {
            return Promise.reject(error);
        }

        if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then((token) => {
                original.headers.Authorization = `Bearer ${token}`;
                return apiClient(original);
            });
        }

        original._retry = true;
        isRefreshing = true;

        try {
            const { data } = await apiClient.post<{ access_token: string }>(
                '/api/v1/auth/refresh',
            );
            useAuthStore.getState().setAccessToken(data.access_token);
            processQueue(null, data.access_token);
            original.headers.Authorization = `Bearer ${data.access_token}`;
            return apiClient(original);
        } catch (err) {
            processQueue(err, null);
            useAuthStore.getState().clear();
            window.location.href = '/login';
            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    },
);
