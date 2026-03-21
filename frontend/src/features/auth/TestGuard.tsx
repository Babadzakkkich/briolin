import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { testingApi } from '@/features/testing/api';

export function TestGuard() {
  const [checking, setChecking] = useState(true);
  const [passed, setPassed] = useState(false);

  useEffect(() => {
    testingApi
      .getHistory()
      .then(({ data }) => setPassed(data.history.some((item) => item.passed)))
      .catch(() => setPassed(false))
      .finally(() => setChecking(false));
  }, []);

  if (checking) return null;
  if (!passed) return <Navigate to='/onboarding' state={{ step: 1 }} replace />;
  return <Outlet />;
}
