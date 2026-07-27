import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { BottomNav, Sidebar } from '@/features/dashboard/ui/Sidebar';
import { ensureAccountLoaded } from '@/entities/account';

export function DashboardLayout() {
  // Роли нужны и Sidebar (пункт "Админка"), и RoleGuard на вложенных маршрутах —
  // загружаем один раз здесь, чтобы оба компонента не делали отдельных запросов.
  useEffect(() => {
    ensureAccountLoaded();
  }, []);

  return (
    <>
      <div className='bg-surface flex h-screen overflow-hidden'>
        <Sidebar />
        <div className='flex flex-1 flex-col overflow-hidden pb-16 md:pb-0'>
          <Outlet />
        </div>
      </div>
      <BottomNav />
    </>
  );
}
