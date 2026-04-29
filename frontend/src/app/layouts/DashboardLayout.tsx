import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/features/dashboard/ui/Sidebar';
import { ToastContainer } from '@/shared/toast/ToastContainer';

export function DashboardLayout() {
  return (
    <>
      <div className='bg-surface flex h-screen overflow-hidden'>
        <Sidebar />
        <div className='flex flex-1 flex-col overflow-hidden'>
          <Outlet />
        </div>
      </div>
      <ToastContainer />
    </>
  );
}
