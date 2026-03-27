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
  isAuthenticated: boolean;
  setAccessToken: (token: string | null) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      username: null,
      isAuthenticated: false,
      setAccessToken: (token) => {
        const payload = token ? decodeJwt(token) : null;
        set({
          accessToken: token,
          isAuthenticated: !!token,
          username: payload?.preferred_username ?? null,
        });
      },
      clear: () => set({ accessToken: null, isAuthenticated: false, username: null }),
    }),
    { name: 'auth' },
  ),
);
