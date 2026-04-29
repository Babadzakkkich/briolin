import { BrowserRouter, Route, Routes } from 'react-router';
import { IndexPage } from '@/pages/Index';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AppLayout } from '@/app/layouts/AppLayout';
import { DashboardLayout } from '@/app/layouts/DashboardLayout';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { TestGuard } from '@/features/auth/TestGuard';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { OnboardingPage } from '@/pages/onboarding/OnboardingPage';
import { DashboardHomePage } from '@/pages/dashboard/DashboardHomePage';
import { ProfilePage } from '@/pages/dashboard/ProfilePage';
import { MessagesPage } from '@/pages/dashboard/MessagesPage';
import { ServicesPage } from '@/pages/dashboard/ServicesPage';
import { CupidonPage } from '@/pages/dashboard/CupidonPage';
import { ClassicSearchPage } from '@/pages/dashboard/ClassicSearchPage';
import { TargetedSearchPage } from '@/pages/dashboard/TargetedSearchPage';
import { UserProfilePage } from '@/pages/dashboard/UserProfilePage';
import { FortunePage } from '@/pages/dashboard/FortunePage';

export function AppRouter() {
  return (
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
              <Route path='search/classic' element={<ClassicSearchPage />} />
              <Route path='search/targeted' element={<TargetedSearchPage />} />
              <Route path='users/:keycloakId' element={<UserProfilePage />} />
              <Route path='cupidon' element={<CupidonPage />} />
              <Route path='fortune' element={<FortunePage />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
