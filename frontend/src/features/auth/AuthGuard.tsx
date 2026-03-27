import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore, sessionApi } from '@/entities/session';

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

  if (checking) return null;
  if (!accessToken) return <Navigate to='/login' replace />;
  return <Outlet />;
}
