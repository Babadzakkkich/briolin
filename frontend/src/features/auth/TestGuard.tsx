import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/entities/session';

/**
 * TestGuard — защита маршрутов дашборда от пользователей, не прошедших психотест.
 *
 * Зачем нужен:
 *   Платформа требует пройти психологический тест перед доступом к мэтчингу
 *   и другим социальным функциям. TestGuard стоит внутри AuthGuard и проверяет
 *   флаг isTestPassed из стора. Если тест не пройден — отправляет на шаг 1
 *   онбординга (страница теста).
 *
 * Флаг isTestPassed устанавливается в useAuth.login() после проверки истории
 * тестовых сессий (GET /test-sessions/history) и сохраняется в localStorage.
 */
export function TestGuard() {
  const isTestPassed = useAuthStore((s) => s.isTestPassed);

  if (!isTestPassed) return <Navigate to='/onboarding' state={{ step: 1 }} replace />;
  return <Outlet />;
}
