import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { JwtPayload } from './types';

const decodeJwt = (token: string): JwtPayload | null => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
};

interface AuthState {
  accessToken: string | null;
  username: string | null;
  keycloakId: string | null;
  isAuthenticated: boolean;
  isTestPassed: boolean;
  setAccessToken: (token: string | null) => void;
  setTestPassed: (passed: boolean) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      username: null,
      keycloakId: null,
      isAuthenticated: false,
      isTestPassed: false,
      setAccessToken: (token) => {
        const payload = token ? decodeJwt(token) : null;
        set({
          accessToken: token,
          isAuthenticated: !!token,
          username: payload?.preferred_username ?? null,
          keycloakId: payload?.sub ?? null,
        });
      },
      setTestPassed: (passed) => set({ isTestPassed: passed }),
      clear: () => set({ accessToken: null, isAuthenticated: false, username: null, keycloakId: null, isTestPassed: false }),
    }),
    { name: 'auth' },
  ),
);
