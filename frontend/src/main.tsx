import { BrowserRouter, Route, Routes } from 'react-router';
import ReactDOM from 'react-dom/client';
import { IndexPage } from '@/pages/Index';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AppLayout } from '@/shared/layouts/AppLayout';
import { DashboardLayout } from '@/shared/layouts/DashboardLayout';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { TestGuard } from '@/features/auth/TestGuard';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { OnboardingPage } from '@/features/onboarding/OnboardingPage';
import { DashboardHomePage } from '@/pages/dashboard/DashboardHomePage';
import { ProfilePage } from '@/pages/dashboard/ProfilePage';
import { MessagesPage } from '@/pages/dashboard/MessagesPage';
import { ServicesPage } from '@/pages/dashboard/ServicesPage';
import { CupidonPage } from '@/pages/dashboard/CupidonPage';
import { SearchPage } from '@/pages/dashboard/SearchPage';
import { FortunePage } from '@/pages/dashboard/FortunePage';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <Routes>
      <Route element={<AppLayout />}>
        <Route path='/login' element={<LoginPage />} />
        <Route path='/registration' element={<RegistrationPage />} />
        <Route path='/forgot-password' element={<ForgotPasswordPage />} />
        <Route path='/' element={<IndexPage />} />

        <Route element={<AuthGuard />}>
          <Route path='/onboarding' element={<OnboardingPage />} />
        </Route>
      </Route>
      <Route path='/dashboard' element={<AuthGuard />}>
        <Route element={<TestGuard />}>
          <Route element={<DashboardLayout />}>
            <Route index element={<DashboardHomePage />} />
            <Route path='profile' element={<ProfilePage />} />
            <Route path='messages' element={<MessagesPage />} />
            <Route path='services' element={<ServicesPage />} />
            <Route path='search' element={<SearchPage />} />
            <Route path='cupidon' element={<CupidonPage />} />
            <Route path='fortune' element={<FortunePage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  </BrowserRouter>,
);
