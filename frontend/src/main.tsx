import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import { Home } from '@/app/Home';
import { LoginPage } from '@/app/pages/auth/LoginPage';
import { RegisterPage } from '@/app/pages/auth/RegisterPage';
import { ResetPasswordPage } from '@/app/pages/auth/ResetPasswordPage';
import { RegistrationCompletePage } from '@/app/pages/auth/RegistrationCompletePage';
import { WelcomeProfile } from '@/app/pages/welcome/WelcomeProfile';
import { TestPage } from '@/app/pages/welcome/TestPage';
import { AppointmentInterviewPage } from '@/app/pages/interview/AppointmentInterviewPage';
import { ResultInterviewPage } from '@/app/pages/interview/ResultInterviewPage';
import { StartInterviewPage } from '@/app/pages/interview/StartInterviewPage';
import { EndInterviewPage } from '@/app/pages/interview/EndInterviewPage';
import { PayInterviewPage } from '@/app/pages/interview/PayInterviewPage';
import { DetailsInterviewPage } from '@/app/pages/interview/DetailsInterviewPage';

const router = createBrowserRouter([
  { path: '/', element: <Home /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/reset-password', element: <ResetPasswordPage /> },
  { path: '/registration-complete', element: <RegistrationCompletePage /> },
  { path: '/welcome/profile', element: <WelcomeProfile /> },
  { path: '/welcome/test', element: <TestPage /> },
  { path: '/interview', element: <StartInterviewPage /> },
  { path: '/interview/appointment', element: <AppointmentInterviewPage /> },
  { path: '/interview/details', element: <DetailsInterviewPage /> },
  { path: '/interview/result', element: <ResultInterviewPage /> },
  { path: '/interview/end', element: <EndInterviewPage /> },
  { path: '/interview/pay', element: <PayInterviewPage /> },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router}></RouterProvider>
  </StrictMode>,
);
