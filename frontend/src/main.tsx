import { BrowserRouter, Route, Routes } from 'react-router';
import ReactDOM from 'react-dom/client';
import { IndexPage } from '@/pages';
import { RegistrationPage } from '@/pages/auth/RegistrationPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AppLayout } from '@/shared/layouts/AppLayout';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { OnboardingPage } from './features/onboarding/OnboardingPage';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <BrowserRouter>
        <Routes>
            <Route element={<AppLayout />}>
                <Route path='/' element={<IndexPage />} />
                <Route path='/login' element={<LoginPage />} />
                <Route path='/registration' element={<RegistrationPage />} />
                <Route path='/forgot-password' element={<ForgotPasswordPage />} />
                <Route path='/onboarding' element={<OnboardingPage />} />
            </Route>
        </Routes>
    </BrowserRouter>,
);
