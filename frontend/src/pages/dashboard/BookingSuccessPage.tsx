import { CalendarCheck, Copy, Mail, Video } from 'lucide-react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { toast } from '@/shared/toast/toast';

export function BookingSuccessPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const booking = useBookingStore((state) => state.bookings.find((item) => item.id === bookingId));
  if (!booking) return <Navigate to='/dashboard/services' replace />;

  return (
    <main className='flex flex-1 items-center justify-center overflow-y-auto px-4 py-8'>
      <section className='border-border w-full max-w-xl rounded-3xl border bg-white p-7 text-center shadow-sm sm:p-10'>
        <div className='bg-accent/10 text-accent mx-auto flex h-20 w-20 items-center justify-center rounded-full'>
          <CalendarCheck size={36} />
        </div>
        <h1 className='font-onest text-primary mt-5 text-3xl font-medium'>Встреча забронирована</h1>
        <p className='text-secondary mt-3 text-[14px] leading-6'>
          Мы подготовили ссылку на созвон. В рабочем режиме подтверждение также придёт на{' '}
          <strong className='text-primary'>{booking.clientEmail}</strong>.
        </p>
        <div className='bg-surface mt-6 rounded-2xl p-5 text-left'>
          <p className='text-primary font-semibold'>{booking.serviceTitle}</p>
          <p className='text-secondary mt-2 text-[13px]'>
            {new Date(`${booking.date}T12:00:00`).toLocaleDateString('ru-RU', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
            , {booking.time}
          </p>
          <div className='border-border my-4 border-t' />
          <div className='flex items-center justify-between gap-3'>
            <span className='text-secondary flex min-w-0 items-center gap-2 truncate text-[12px]'>
              <Video size={15} /> {booking.meetingUrl}
            </span>
            <button
              onClick={() => {
                navigator.clipboard?.writeText(booking.meetingUrl ?? '');
                toast.success('Ссылка скопирована');
              }}
              className='text-accent cursor-pointer rounded-lg p-2 hover:bg-white'
            >
              <Copy size={16} />
            </button>
          </div>
        </div>
        <div className='mt-6 flex flex-col gap-3 sm:flex-row'>
          <Button
            variant='secondary'
            className='flex-1'
            onClick={() => navigate('/dashboard/services')}
          >
            <Mail size={16} /> К услугам
          </Button>
          <Button className='flex-1' onClick={() => window.open(booking.meetingUrl, '_blank')}>
            Открыть ссылку
          </Button>
        </div>
      </section>
    </main>
  );
}
