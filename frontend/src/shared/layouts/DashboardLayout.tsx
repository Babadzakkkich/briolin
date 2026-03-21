import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/features/dashboard/components/Sidebar';
import { ToastContainer } from '@/shared/toast/ToastContainer';

export function DashboardLayout() {
  return (
    <>
      <div className='bg-surface flex min-h-screen'>
        <Sidebar />
        <Outlet />
      </div>
      <ToastContainer />
    </>
  );
}
