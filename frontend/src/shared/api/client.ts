import axios from 'axios';
import { useAuthStore } from '@/entities/session/model/store';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

// apiClient — основной инстанс для всех запросов к бэку.
// withCredentials нужен, чтобы браузер автоматически передавал HTTP-only cookie
// с refresh token при запросах на /auth/refresh.
export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// Отдельный инстанс без перехватчиков — используется только для /auth/refresh,
// чтобы не попасть в бесконечную рекурсию: 401 → refresh → 401 → refresh → ...
const refreshClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// Перехватчик запроса: добавляет Authorization header из стора.
// Токен читается из стора (а не из замыкания), чтобы всегда брать актуальное значение
// после refresh.
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Единый refresh для HTTP и WebSocket. Пока запрос выполняется, все следующие
// вызовы получают тот же Promise и не используют refresh token повторно.
let refreshPromise: Promise<string> | null = null;

export function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post<{ access_token: string }>('/auth/refresh')
      .then(({ data }) => {
        useAuthStore.getState().setAccessToken(data.access_token);
        return data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

export function isRefreshTokenRejected(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 401;
}

// Перехватчик ответа: автоматически рефрешит access token при 401.
//
// Алгоритм:
//   1. Пришёл 401 на защищённый endpoint.
//   2. Все параллельные запросы ждут единый refreshAccessToken().
//   3. Помечаем запрос `_retry` (чтобы не зациклиться) и обновляем токен.
//      - Успех: сохраняем новый токен и повторяем исходный запрос.
//      - 401 от refresh: refresh token отклонён — чистим стор и редиректим на /login.
//      - Сетевая или серверная ошибка: сохраняем сессию и возвращаем ошибку вызывающему коду.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // Auth-эндпоинты не рефрешим: у них 401 — легитимная ошибка (неверный логин и т.п.)
    const isAuthEndpoint =
      original?.url?.includes('/auth/login') ||
      original?.url?.includes('/auth/register') ||
      original?.url?.includes('/auth/forgot-password') ||
      original?.url?.includes('/auth/refresh');

    if (error.response?.status !== 401 || original?._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      const token = await refreshAccessToken();
      original.headers.Authorization = `Bearer ${token}`;
      return apiClient(original);
    } catch (err) {
      if (isRefreshTokenRejected(err)) {
        useAuthStore.getState().clear();
        window.location.href = '/login';
      }
      return Promise.reject(err);
    }
  },
);
