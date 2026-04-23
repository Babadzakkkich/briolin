import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/entities/session';

export function TestGuard() {
  const isTestPassed = useAuthStore((s) => s.isTestPassed);

  if (!isTestPassed) return <Navigate to='/onboarding' state={{ step: 1 }} replace />;
  return <Outlet />;
}
