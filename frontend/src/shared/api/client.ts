import axios from 'axios';
import { useAuthStore } from '@/entities/session/model/store';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

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

// Используется в useChatSocket для явного рефреша токена при WS-ошибке (код 1008).
export async function refreshAccessToken(): Promise<string> {
  const { data } = await refreshClient.post<{ access_token: string }>('/auth/refresh');
  useAuthStore.getState().setAccessToken(data.access_token);
  return data.access_token;
}

// Флаг "refresh уже идёт" — защита от параллельных рефрешей.
// Если несколько запросов одновременно получили 401, только один делает /auth/refresh,
// остальные ждут в очереди и повторяются с новым токеном.
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

// Перехватчик ответа: автоматически рефрешит access token при 401.
//
// Алгоритм:
//   1. Пришёл 401 на защищённый endpoint.
//   2. Если refresh уже идёт — добавляем запрос в очередь; он повторится, когда refresh завершится.
//   3. Иначе — помечаем запрос `_retry` (чтобы не зациклиться) и делаем POST /auth/refresh.
//      - Успех: сохраняем новый токен, сбрасываем очередь, повторяем исходный запрос.
//      - Ошибка: значит и refresh token истёк — чистим стор и редиректим на /login.
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

    if (isRefreshing) {
      // Ставим запрос в очередь; он разрешится после завершения текущего refresh
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
      const { data } = await refreshClient.post<{ access_token: string }>('/auth/refresh');
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
