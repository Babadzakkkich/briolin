import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/shared/stores/authStore';
import { authApi } from './api';
import { profileApi } from '@/features/profile/api';

export function useAuth() {
  const navigate = useNavigate();
  const { setAccessToken, clear } = useAuthStore();

  const login = async (username: string, password: string) => {
    const { data } = await authApi.login({ username, password });
    setAccessToken(data.access_token);
    try {
      await profileApi.getMe();
      navigate('/dashboard');
    } catch {
      navigate('/onboarding');
    }
  };

  const register = async (email: string, username: string, password: string) => {
    await authApi.register({ email, username, password });
    navigate('/login');
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      clear();
      navigate('/login');
    }
  };

  return { login, register, logout };
}
