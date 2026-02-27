import { create } from "zustand";

type UserRole = "user" | "psych" | "admin";

export type User = {
  id: string;
  keycloakId: string;
  username: string;
  email: string;
  roles: UserRole[];
  isActive: boolean;
  isTestPassed: false;
  createdAt: Date;
};

type AuthStore = {
  accessToken: string | null;
  setToken: (token: string) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthStore>((set) => ({
  accessToken: null,

  setToken: (token) =>
    set({
      accessToken: token,
    }),

  logout: () =>
    set({
      accessToken: null,
    }),
}));
