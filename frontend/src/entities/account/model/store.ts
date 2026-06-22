import { create } from 'zustand';
import { accountApi } from '../api';
import type { AccountResponse, UserRole } from './types';

interface AccountState {
  username: string | null;
  email: string | null;
  roles: UserRole[];
  isActive: boolean;
  isTestPassed: boolean;
  createdAt: string | null;
  loaded: boolean;
  setAccount: (account: AccountResponse) => void;
  clear: () => void;
}

export const useAccountStore = create<AccountState>()((set) => ({
  username: null,
  email: null,
  roles: [],
  isActive: true,
  isTestPassed: false,
  createdAt: null,
  loaded: false,
  setAccount: (account) =>
    set({
      username: account.username,
      email: account.email,
      roles: account.roles,
      isActive: account.is_active,
      isTestPassed: account.is_test_passed,
      createdAt: account.created_at,
      loaded: true,
    }),
  clear: () =>
    set({
      username: null,
      email: null,
      roles: [],
      isActive: true,
      isTestPassed: false,
      createdAt: null,
      loaded: false,
    }),
}));

// Гарантирует, что роли загружены до первой проверки (RoleGuard, Sidebar).
// Дедуплицирует параллельные вызовы при одновременном маунте нескольких компонентов.
let loadPromise: Promise<void> | null = null;

export function ensureAccountLoaded(): Promise<void> {
  if (useAccountStore.getState().loaded) return Promise.resolve();
  if (!loadPromise) {
    loadPromise = accountApi
      .getMe()
      .then((res) => useAccountStore.getState().setAccount(res.data))
      .catch(() => {})
      .finally(() => {
        loadPromise = null;
      });
  }
  return loadPromise;
}
