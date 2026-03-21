import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/shared/stores/authStore';
import { useProfileStore } from '@/shared/stores/profileStore';
import { authApi } from './api';
import { profileApi } from '@/features/profile/api';
import { testingApi } from '@/features/testing/api';

export function useAuth() {
  const navigate = useNavigate();
  const { setAccessToken, clear: clearAuth } = useAuthStore();
  const { setProfile, clear: clearProfile } = useProfileStore();

  const login = async (username: string, password: string) => {
    const { data } = await authApi.login({ username, password });
    setAccessToken(data.access_token);

    try {
      const { data: profile } = await profileApi.getMe();
      setProfile(profile.basic);
    } catch {
      navigate('/onboarding', { state: { step: 0 } });
      return;
    }

    try {
      const { data } = await testingApi.getHistory();
      const hasPassed = data.history.some((item) => item.passed);
      if (hasPassed) {
        navigate('/dashboard');
      } else {
        navigate('/onboarding', { state: { step: 1 } });
      }
    } catch {
      navigate('/onboarding', { state: { step: 1 } });
    }
  };

  const register = async (email: string, username: string, password: string) => {
    try {
      await authApi.register({ email, username, password });
    } catch (error) {
      console.error(error);
      return;
    }
    navigate('/login');
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      clearProfile();
      navigate('/login');
    }
  };

  return { login, register, logout };
}
