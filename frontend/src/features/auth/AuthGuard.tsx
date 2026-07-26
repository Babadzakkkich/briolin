import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore, sessionApi } from '@/entities/session';
import { Loader } from '@/shared/uikit/Loader';

/**
 * AuthGuard — защита маршрутов, требующих авторизации.
 *
 * Зачем нужен:
 *   Не даёт неавторизованному пользователю зайти на защищённые страницы.
 *   Также восстанавливает сессию после перезагрузки страницы — access token
 *   мог протухнуть, пока вкладка была закрыта, поэтому при его отсутствии
 *   делается попытка рефреша через HTTP-only cookie с refresh token.
 *
 * Алгоритм:
 *   1. Если access token уже есть в сторе — сразу пропускаем (checking = false).
 *   2. Если токена нет — делаем POST /auth/refresh (cookie передаётся автоматически).
 *      - Успех: сохраняем новый токен, рендерим дочерние маршруты.
 *      - Ошибка (refresh token протух): редиректим на /login.
 *   3. Пока идёт проверка — показываем лоадер, чтобы не было мигания.
 */
export function AuthGuard() {
  const { accessToken, setAccessToken } = useAuthStore();
  const [checking, setChecking] = useState(!accessToken);

  useEffect(() => {
    if (accessToken) return;
    sessionApi
      .refresh()
      .then(({ data }) => setAccessToken(data.access_token))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  if (checking) return <Loader center size='lg' />;
  if (!accessToken) return <Navigate to='/login' replace />;
  return <Outlet />;
}
