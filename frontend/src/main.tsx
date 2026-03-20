import { BrowserRouter, Route, Routes } from 'react-router';
import ReactDOM from 'react-dom/client';
import { IndexPage } from '@/pages';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { AuthGuard } from '@/features/auth/AuthGuard';
import { OnboardingPage } from '@/features/onboarding/OnboardingPage';
import { AppLayout } from '@/shared/layouts/AppLayout';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <BrowserRouter>
        <Routes>
            <Route element={<AppLayout />}>
                {/* Публичные роуты */}
                <Route path='/login' element={<LoginPage />} />
                <Route path='/registration' element={<RegistrationPage />} />
                <Route path='/forgot-password' element={<ForgotPasswordPage />} />

                {/* Защищённые роуты */}
                <Route element={<AuthGuard />}>
                    <Route path='/' element={<IndexPage />} />
                    <Route path='/onboarding' element={<OnboardingPage />} />
                </Route>
            </Route>
        </Routes>
    </BrowserRouter>,
);
