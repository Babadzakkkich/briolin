import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { CalendarDays, CreditCard, LockKeyhole, Mail, ShieldCheck } from 'lucide-react';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';

export function PaymentPage() {
  const navigate = useNavigate();
  const draft = useBookingStore((state) => state.draftBooking);
  const confirmDraftPayment = useBookingStore((state) => state.confirmDraftPayment);
  const [processing, setProcessing] = useState(false);
  const [agreed, setAgreed] = useState(false);

  if (!draft) return <Navigate to='/dashboard/services' replace />;

  function pay() {
    setProcessing(true);
    window.setTimeout(() => {
      const confirmed = confirmDraftPayment();
      if (confirmed) navigate(`/dashboard/booking-success/${confirmed.id}`, { replace: true });
    }, 900);
  }

  return (
    <main className='flex-1 overflow-y-auto px-4 py-8 md:px-8'>
      <div className='mx-auto max-w-2xl'>
        <button
          onClick={() => navigate(-1)}
          className='text-secondary hover:text-primary mb-5 cursor-pointer text-[13px]'
        >
          ← Изменить время
        </button>
        <section className='border-border overflow-hidden rounded-3xl border bg-white'>
          <div className='bg-surface px-6 py-6 sm:px-8'>
            <div className='flex items-center gap-3'>
              <div className='bg-accent/10 text-accent flex h-11 w-11 items-center justify-center rounded-2xl'>
                <CreditCard size={21} />
              </div>
              <div>
                <h1 className='font-onest text-primary text-2xl font-medium'>Оплата записи</h1>
                <p className='text-secondary text-[12px]'>Демонстрационный платёж</p>
              </div>
            </div>
          </div>
          <div className='px-6 py-7 sm:px-8'>
            <h2 className='text-primary text-[16px] font-semibold'>{draft.serviceTitle}</h2>
            <div className='mt-4 grid gap-3 text-[13px] sm:grid-cols-2'>
              <p className='text-secondary flex items-center gap-2'>
                <CalendarDays size={16} />{' '}
                {new Date(`${draft.date}T12:00:00`).toLocaleDateString('ru-RU', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })}
                , {draft.time}
              </p>
              <p className='text-secondary flex items-center gap-2'>
                <Mail size={16} /> {draft.clientEmail}
              </p>
            </div>
            <div className='border-border my-6 border-t' />
            <div className='flex items-center justify-between'>
              <span className='text-secondary text-[13px]'>Итого</span>
              <span className='text-primary text-2xl font-semibold'>
                {draft.price.toLocaleString('ru-RU')} ₽
              </span>
            </div>
            <label className='bg-surface mt-6 flex cursor-pointer items-start gap-3 rounded-2xl p-4'>
              <input
                type='checkbox'
                checked={agreed}
                onChange={(event) => setAgreed(event.target.checked)}
                className='accent-accent mt-0.5 h-4 w-4'
              />
              <span className='text-secondary text-[12px] leading-5'>
                Я подтверждаю данные записи и соглашаюсь с условиями оплаты и отмены.
              </span>
            </label>
            <Button
              size='lg'
              className='mt-5 w-full'
              disabled={!agreed || processing}
              onClick={pay}
            >
              <LockKeyhole size={17} />{' '}
              {processing
                ? 'Обрабатываем оплату...'
                : `Оплатить ${draft.price.toLocaleString('ru-RU')} ₽`}
            </Button>
            <p className='text-muted mt-4 flex items-center justify-center gap-1.5 text-[11px]'>
              <ShieldCheck size={13} /> Платёжные данные защищены
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
