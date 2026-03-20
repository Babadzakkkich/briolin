import { BrowserRouter, Route, Routes } from 'react-router';
import ReactDOM from 'react-dom/client';
import { IndexPage } from '@/pages/Index';
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AppLayout } from '@/shared/layouts/AppLayout';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { OnboardingPage } from '@/features/onboarding/OnboardingPage';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route element={<AppLayout />}>
        <Route path='/login' element={<LoginPage />} />
        <Route path='/registration' element={<RegistrationPage />} />
        <Route path='/forgot-password' element={<ForgotPasswordPage />} />
        <Route path='/' element={<IndexPage />} />

        <Route element={<AuthGuard />}>
          <Route path='/dashboard' element={<DashboardPage />} />
          <Route path='/onboarding' element={<OnboardingPage />} />
        </Route>
      </Route>
    </Routes>
  </BrowserRouter>,
);
