import { useNavigate } from 'react-router-dom';
import { useAuthStore, sessionApi } from '@/entities/session';
import { useProfileStore, profileApi } from '@/entities/profile';
import { testSessionApi } from '@/entities/test-session';
import { useAccountStore, accountApi } from '@/entities/account';

function getJwtPayload(token: string): Record<string, unknown> {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return {};
  }
}

export function useAuth() {
  const navigate = useNavigate();
  const { setAccessToken, setTestPassed, clear: clearAuth } = useAuthStore();
  const { setProfile, clear: clearProfile } = useProfileStore();
  const { setAccount, clear: clearAccount } = useAccountStore();

  const login = async (username: string, password: string) => {
    const { data } = await sessionApi.login({ username, password });
    setAccessToken(data.access_token);

    const payload = getJwtPayload(data.access_token);
    if (!payload.email_verified) {
      const email = payload.email as string | undefined;
      try { await sessionApi.requestVerification(); } catch { /* код уже выслан */ }
      navigate('/check-email', { state: { email } });
      return;
    }

    try {
      const { data: profile } = await profileApi.getMe();
      setProfile(profile.basic);
    } catch {
      navigate('/onboarding', { state: { step: 0 } });
      return;
    }

    accountApi
      .getMe()
      .then(({ data }) => setAccount(data))
      .catch(() => {});

    try {
      const { data } = await testSessionApi.getHistory();
      const hasPassed = data.history.some((item) => item.passed);
      setTestPassed(hasPassed);
      if (hasPassed) {
        navigate('/dashboard');
      } else {
        navigate('/onboarding', { state: { step: 1 } });
      }
    } catch {
      setTestPassed(false);
      navigate('/onboarding', { state: { step: 1 } });
    }
  };

  const register = async (email: string, username: string, password: string) => {
    await sessionApi.register({ email, username, password });
    const { data } = await sessionApi.login({ username: email, password });
    setAccessToken(data.access_token);
    await sessionApi.requestVerification();
    navigate('/check-email', { state: { email } });
  };

  const logout = async () => {
    try {
      await sessionApi.logout();
    } finally {
      clearAuth();
      clearProfile();
      clearAccount();
      navigate('/login');
    }
  };

  return { login, register, logout };
}
