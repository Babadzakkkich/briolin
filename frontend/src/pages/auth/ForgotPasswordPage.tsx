import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PinInput } from '@ark-ui/react/pin-input';
import { sessionApi } from '@/entities/session';
import { toast } from '@/shared/toast/toast';
import { IconCard } from '@/shared/cards/IconCard';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { z } from 'zod';

const EmailSchema = z.object({
  email: z.email('Некорректный email'),
});

const ConfirmSchema = z
  .object({
    new_password: z.string().min(6, 'Минимум 6 символов'),
    confirm_password: z.string().min(1, 'Подтвердите пароль'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'Пароли не совпадают',
    path: ['confirm_password'],
  });

type Step = 'request' | 'confirm';

const PIN_CELL_CLASS = [
  'size-12 rounded-xl border text-center caret-accent',
  'font-inter text-primary text-[20px] font-medium',
  'transition-colors outline-none',
  'border-border focus:border-accent',
].join(' ');

export function ForgotPasswordPage() {
  const navigate = useNavigate();

  const [step, setStep] = useState<Step>('request');
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [code, setCode] = useState('');
  const [passwords, setPasswords] = useState({ new_password: '', confirm_password: '' });
  const [passwordErrors, setPasswordErrors] = useState<
    Partial<Record<'new_password' | 'confirm_password', string>>
  >({});
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const resendTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startResendCooldown = () => {
    setResendCooldown(60);
    const tick = () => {
      setResendCooldown((prev) => {
        if (prev <= 1) return 0;
        resendTimerRef.current = setTimeout(tick, 1000);
        return prev - 1;
      });
    };
    resendTimerRef.current = setTimeout(tick, 1000);
  };

  const handleRequestReset = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    const result = EmailSchema.safeParse({ email });
    if (!result.success) {
      setEmailError(result.error.issues[0].message);
      return;
    }
    setEmailError('');
    setLoading(true);
    try {
      await sessionApi.requestPasswordReset(email);
      setStep('confirm');
      startResendCooldown();
    } catch {
      toast.error('Не удалось отправить код. Проверьте адрес почты.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setLoading(true);
    try {
      await sessionApi.requestPasswordReset(email);
      toast.success('Код отправлен повторно');
      startResendCooldown();
    } catch {
      toast.error('Не удалось отправить код повторно');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (code.length < 6) {
      toast.error('Введите 6-значный код из письма');
      return;
    }
    const result = ConfirmSchema.safeParse(passwords);
    if (!result.success) {
      setPasswordErrors(
        Object.fromEntries(result.error.issues.map((i) => [i.path[0], i.message])),
      );
      return;
    }
    setPasswordErrors({});
    setLoading(true);
    try {
      await sessionApi.confirmPasswordReset(email, code, result.data.new_password);
      toast.success('Пароль успешно изменён');
      navigate('/login');
    } catch {
      toast.error('Неверный или устаревший код');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'request') {
    return (
      <form
        onSubmit={handleRequestReset}
        className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'
      >
        <div className='flex flex-col items-center gap-2 text-center'>
          <IconCard icon='lock' />
          <Text variant='h2' as='h2'>
            Забыли пароль?
          </Text>
          <Text variant='p-sm' as='p'>
            Введите адрес почты — мы отправим код для сброса пароля.
          </Text>
        </div>

        <Input
          label='Почта'
          placeholder='mail@example.ru'
          type='email'
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (emailError) setEmailError('');
          }}
          error={emailError}
        />

        <div className='flex flex-col gap-4 text-center'>
          <Button type='submit' disabled={loading}>
            {loading ? 'Отправляем...' : 'Отправить код'}
          </Button>
          <div className='flex flex-col'>
            <Text variant='p-sm'>Вспомнили пароль?</Text>
            <Link to='/login'>
              <Text className='text-accent! underline' variant='p-sm'>
                Войти
              </Text>
            </Link>
          </div>
        </div>
      </form>
    );
  }

  return (
    <form
      onSubmit={handleConfirm}
      className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'
    >
      <div className='flex flex-col items-center gap-2 text-center'>
        <IconCard icon='mail' />
        <Text variant='h2' as='h2'>
          Проверьте почту
        </Text>
        <Text variant='p-sm' as='p'>
          Мы отправили 6-значный код на{' '}
          <span className='text-primary font-bold'>{email}</span>
        </Text>
      </div>

      <div className='flex flex-col gap-1.5'>
        <span className='font-inter text-primary text-[12px] font-medium'>Код из письма</span>
        <PinInput.Root
          count={6}
          otp
          onValueChange={(details) => setCode(details.valueAsString)}
        >
          <PinInput.Control className='flex justify-between gap-2'>
            {Array.from({ length: 6 }).map((_, i) => (
              <PinInput.Input key={i} index={i} className={PIN_CELL_CLASS} />
            ))}
          </PinInput.Control>
          <PinInput.HiddenInput />
        </PinInput.Root>
      </div>

      <div className='flex flex-col gap-4'>
        <Input
          label='Новый пароль'
          placeholder='Минимум 6 символов'
          type='password'
          value={passwords.new_password}
          onChange={(e) => {
            setPasswords((p) => ({ ...p, new_password: e.target.value }));
            if (passwordErrors.new_password)
              setPasswordErrors((p) => ({ ...p, new_password: undefined }));
          }}
          error={passwordErrors.new_password}
        />
        <Input
          label='Повторите пароль'
          placeholder='Введите пароль ещё раз'
          type='password'
          value={passwords.confirm_password}
          onChange={(e) => {
            setPasswords((p) => ({ ...p, confirm_password: e.target.value }));
            if (passwordErrors.confirm_password)
              setPasswordErrors((p) => ({ ...p, confirm_password: undefined }));
          }}
          error={passwordErrors.confirm_password}
        />
      </div>

      <div className='flex flex-col gap-4 text-center'>
        <Button type='submit' disabled={loading || code.length < 6}>
          {loading ? 'Сохраняем...' : 'Сохранить новый пароль'}
        </Button>
        <div className='flex flex-col items-center gap-0.5'>
          <Text variant='p-sm'>Не получили письмо?</Text>
          {resendCooldown > 0 ? (
            <Text variant='p-sm' className='text-secondary!'>
              Отправить повторно через {resendCooldown} с
            </Text>
          ) : (
            <button
              type='button'
              onClick={handleResend}
              disabled={loading}
              className='font-inter text-accent hover:text-accent-hover text-[14px] font-semibold transition-colors disabled:opacity-40'
            >
              Отправить повторно
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
