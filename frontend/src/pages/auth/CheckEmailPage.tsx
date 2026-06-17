import { useState, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { PinInput } from '@ark-ui/react/pin-input';
import { sessionApi } from '@/entities/session';
import { toast } from '@/shared/toast/toast';
import { IconCard } from '@/shared/cards/IconCard';
import { Button } from '@/shared/uikit/Button';
import { Text } from '@/shared/uikit/Text';

const PIN_CELL_CLASS = [
  'size-12 rounded-xl border text-center caret-accent',
  'font-inter text-primary text-[20px] font-medium',
  'transition-colors outline-none',
  'border-border focus:border-accent',
].join(' ');

export function CheckEmailPage() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const email = state?.email as string | undefined;

  const [code, setCode] = useState('');
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

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setLoading(true);
    try {
      await sessionApi.requestVerification();
      toast.success('Код отправлен повторно');
      startResendCooldown();
    } catch {
      toast.error('Не удалось отправить код повторно');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (code.length < 6) {
      toast.error('Введите 6-значный код из письма');
      return;
    }
    setLoading(true);
    try {
      await sessionApi.confirmVerification(code);
      toast.success('Email успешно подтверждён');
      navigate('/onboarding', { state: { step: 0 } });
    } catch {
      toast.error('Неверный или устаревший код');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'
    >
      <div className='flex flex-col items-center gap-2 text-center'>
        <IconCard icon='mail' />
        <Text variant='h2' as='h2'>
          Проверьте почту
        </Text>
        <Text variant='p-sm' as='p'>
          Мы отправили 6-значный код на{' '}
          {email && <span className='text-primary font-bold'>{email}</span>}
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

      <div className='flex flex-col gap-4 text-center'>
        <Button type='submit' disabled={loading || code.length < 6}>
          {loading ? 'Проверяем...' : 'Подтвердить email'}
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

        <div className='flex flex-col items-center gap-1'>
          <Text variant='p-sm'>Уже подтверждали ранее?</Text>
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
