import { BrowserRouter, Route, Routes } from 'react-router';
import { IndexPage } from '@/pages/index';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AppLayout } from '@/app/layouts/AppLayout';
import { DashboardLayout } from '@/app/layouts/DashboardLayout';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { TestGuard } from '@/features/auth/TestGuard';
import { RoleGuard } from '@/features/auth/RoleGuard';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { CheckEmailPage } from '@/pages/auth/CheckEmailPage';
import { OnboardingPage } from '@/pages/onboarding/OnboardingPage';
import { DashboardHomePage } from '@/pages/dashboard/DashboardHomePage';
import { ProfilePage } from '@/pages/dashboard/ProfilePage';
import { SettingsPage } from '@/pages/dashboard/SettingsPage';
import { MessagesPage } from '@/pages/dashboard/MessagesPage';
import { ServicesPage } from '@/pages/dashboard/ServicesPage';
import { CupidonPage } from '@/pages/dashboard/CupidonPage';
import { ClassicSearchPage } from '@/pages/dashboard/ClassicSearchPage';
import { TargetedSearchPage } from '@/pages/dashboard/TargetedSearchPage';
import { UserProfilePage } from '@/pages/dashboard/UserProfilePage';
import { FortunePage } from '@/pages/dashboard/FortunePage';
import { PendingLikesPage } from '@/pages/dashboard/PendingLikesPage';
import { MatchesPage } from '@/pages/dashboard/MatchesPage';
import { AdminUsersPage } from '@/pages/dashboard/admin/AdminUsersPage';
import { AdminUserDetailPage } from '@/pages/dashboard/admin/AdminUserDetailPage';
import { ToastContainer } from '@/shared/toast/ToastContainer';
import { BookingPage } from '@/pages/dashboard/BookingPage';
import { PaymentPage } from '@/pages/dashboard/PaymentPage';
import { BookingSuccessPage } from '@/pages/dashboard/BookingSuccessPage';
import { PsychologistLayout } from '@/app/layouts/PsychologistLayout';
import { PsychologistDashboardPage } from '@/pages/psychologist/PsychologistDashboardPage';
import { PsychologistBookingsPage } from '@/pages/psychologist/PsychologistBookingsPage';
import { PsychologistServicesPage } from '@/pages/psychologist/PsychologistServicesPage';
import { ServiceFormPage } from '@/pages/psychologist/ServiceFormPage';
import { InterviewResultPage } from '@/pages/psychologist/InterviewResultPage';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path='/login' element={<LoginPage />} />
          <Route path='/registration' element={<RegistrationPage />} />
          <Route path='/forgot-password' element={<ForgotPasswordPage />} />
          <Route path='/check-email' element={<CheckEmailPage />} />
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
              <Route path='settings' element={<SettingsPage />} />
              <Route path='messages' element={<MessagesPage />} />
              <Route path='services' element={<ServicesPage />} />
              <Route path='services/:serviceId/booking' element={<BookingPage />} />
              <Route path='payment' element={<PaymentPage />} />
              <Route path='booking-success/:bookingId' element={<BookingSuccessPage />} />
              <Route path='search/classic' element={<ClassicSearchPage />} />
              <Route path='search/targeted' element={<TargetedSearchPage />} />
              <Route path='users/:keycloakId' element={<UserProfilePage />} />
              <Route path='cupidon' element={<CupidonPage />} />
              <Route path='fortune' element={<FortunePage />} />
              <Route path='likes' element={<PendingLikesPage />} />
              <Route path='matches' element={<MatchesPage />} />

              <Route element={<RoleGuard role='admin' />}>
                <Route path='admin' element={<AdminUsersPage />} />
                <Route path='admin/users/:keycloakId' element={<AdminUserDetailPage />} />
              </Route>
            </Route>
          </Route>
        </Route>

        <Route path='/psychologist' element={<AuthGuard />}>
          <Route element={<RoleGuard role='psychologist' />}>
            <Route element={<PsychologistLayout />}>
              <Route index element={<PsychologistDashboardPage />} />
              <Route path='bookings' element={<PsychologistBookingsPage />} />
              <Route path='bookings/:bookingId/result' element={<InterviewResultPage />} />
              <Route path='services' element={<PsychologistServicesPage />} />
              <Route path='services/new' element={<ServiceFormPage />} />
              <Route path='services/:serviceId/edit' element={<ServiceFormPage />} />
            </Route>
          </Route>
        </Route>
      </Routes>
      <ToastContainer />
    </BrowserRouter>
  );
}
