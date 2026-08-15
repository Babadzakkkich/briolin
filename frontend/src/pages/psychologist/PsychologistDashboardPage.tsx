import { CalendarCheck, CheckCircle2, Clock3, WalletCards } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';

export function PsychologistDashboardPage() {
  const navigate = useNavigate();
  const bookings = useBookingStore((state) => state.bookings);
  const activeServices = useBookingStore(
    (state) => state.services.filter((service) => service.active).length,
  );
  const upcoming = bookings.filter((item) => item.status === 'upcoming');
  const waitingResult = bookings.filter((item) => item.status === 'completed' && !item.result);
  const todayLabel = new Intl.DateTimeFormat('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date());

  const stats = [
    { label: 'Предстоящие записи', value: upcoming.length, icon: CalendarCheck },
    { label: 'Ждут результата', value: waitingResult.length, icon: Clock3 },
    { label: 'Активные услуги', value: activeServices, icon: CheckCircle2 },
    {
      label: 'Оплачено записей',
      value: bookings.filter((item) => item.paymentStatus === 'paid').length,
      icon: WalletCards,
    },
  ];

  return (
    <main className='px-4 py-8 md:px-10'>
      <div className='mx-auto max-w-6xl'>
        <p className='text-secondary text-[13px]'>{todayLabel}</p>
        <h1 className='font-onest text-primary mt-1 text-3xl font-medium'>Добрый день, Анна</h1>
        <div className='mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
          {stats.map(({ label, value, icon: Icon }) => (
            <article key={label} className='border-border rounded-2xl border bg-white p-5'>
              <div className='text-accent bg-accent/10 flex h-9 w-9 items-center justify-center rounded-xl'>
                <Icon size={18} />
              </div>
              <p className='text-primary mt-5 text-3xl font-semibold'>{value}</p>
              <p className='text-secondary mt-1 text-[12px]'>{label}</p>
            </article>
          ))}
        </div>
        <section className='border-border mt-6 rounded-3xl border bg-white p-6'>
          <div className='flex items-center justify-between'>
            <div>
              <h2 className='font-onest text-primary text-xl font-medium'>Ближайшие встречи</h2>
              <p className='text-secondary mt-1 text-[12px]'>
                Запланированные собеседования и консультации
              </p>
            </div>
            <Button
              variant='secondary'
              size='sm'
              onClick={() => navigate('/psychologist/bookings')}
            >
              Все записи
            </Button>
          </div>
          <div className='mt-5 flex flex-col gap-2'>
            {upcoming.slice(0, 4).map((booking) => (
              <div
                key={booking.id}
                className='bg-surface flex flex-col gap-3 rounded-2xl p-4 sm:flex-row sm:items-center'
              >
                <div className='text-accent flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white font-semibold'>
                  {booking.time}
                </div>
                <div className='min-w-0 flex-1'>
                  <p className='text-primary text-[14px] font-semibold'>{booking.clientName}</p>
                  <p className='text-secondary truncate text-[12px]'>
                    {booking.serviceTitle} · {booking.date}
                  </p>
                </div>
                <Button
                  size='sm'
                  onClick={() => navigate(`/psychologist/bookings/${booking.id}/result`)}
                >
                  Открыть
                </Button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
