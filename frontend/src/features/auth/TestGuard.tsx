import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { testSessionApi } from '@/entities/test-session';

export function TestGuard() {
  const [checking, setChecking] = useState(true);
  const [passed, setPassed] = useState(false);

  useEffect(() => {
    testSessionApi
      .getHistory()
      .then(({ data }) => setPassed(data.history.some((item) => item.passed)))
      .catch(() => setPassed(false))
      .finally(() => setChecking(false));
  }, []);

  if (checking) return null;
  if (!passed) return <Navigate to='/onboarding' state={{ step: 1 }} replace />;
  return <Outlet />;
}
