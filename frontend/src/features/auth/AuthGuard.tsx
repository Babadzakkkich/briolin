import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/shared/stores/authStore';
import { useProfileStore } from '@/shared/stores/profileStore';
import { authApi } from './api';
import { profileApi } from '../profile/api';
import { toast } from '@/shared/toast/toast';

export function AuthGuard() {
  const { accessToken, setAccessToken } = useAuthStore();
  const { firstName, setProfile } = useProfileStore();
  const [checking, setChecking] = useState(!accessToken);

  useEffect(() => {
    if (accessToken) return;

    authApi
      .refresh()
      .then(({ data }) => setAccessToken(data.access_token))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  if (!firstName) {
    profileApi
      .getMe()
      .then(({ data }) => setProfile(data.basic))
      .catch(() => {
        toast.error('Не удалось получить данные о профиле');
      });
  }

  if (checking) return null;
  if (!accessToken) return <Navigate to='/login' replace />;
  return <Outlet />;
}
