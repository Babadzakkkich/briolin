import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAccountStore, ensureAccountLoaded } from '@/entities/account';
import type { UserRole } from '@/entities/account';
import { Loader } from '@/shared/uikit/Loader';

/**
 * RoleGuard — защита маршрутов, требующих определённой роли (например, "admin").
 *
 * Роли не хранятся в JWT (выдаётся Keycloak без realm-ролей в payload), поэтому
 * их нельзя прочитать синхронно из токена — единственный источник правды это
 * GET /users/me. ensureAccountLoaded() дедуплицирует параллельные запросы,
 * если несколько компонентов (Sidebar, RoleGuard) маунтятся одновременно.
 */
export function RoleGuard({ role }: { role: UserRole }) {
  const { roles, loaded } = useAccountStore();
  const [checking, setChecking] = useState(!loaded);

  useEffect(() => {
    if (loaded) return;
    ensureAccountLoaded().finally(() => setChecking(false));
  }, [loaded]);

  if (checking) return <Loader center size='lg' />;
  if (!roles.includes(role)) return <Navigate to='/dashboard' replace />;
  return <Outlet />;
}
