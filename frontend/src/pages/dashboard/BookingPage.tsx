import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CalendarDays, Check, Clock3, Globe2, UserRound } from 'lucide-react';
import { useAccountStore } from '@/entities/account';
import { useBookingStore, type Booking } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { EmptyState } from '@/shared/uikit/EmptyState';

const TIMES = ['09:30', '11:00', '13:30', '15:00', '16:30', '18:00'];

function getAvailableDates() {
  return Array.from({ length: 8 }, (_, offset) => {
    const date = new Date();
    date.setDate(date.getDate() + offset + 1);
    const iso = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    return {
      iso,
      weekday: new Intl.DateTimeFormat('ru-RU', { weekday: 'short' }).format(date),
      day: date.getDate(),
      month: new Intl.DateTimeFormat('ru-RU', { month: 'short' }).format(date).replace('.', ''),
    };
  });
}

export function BookingPage() {
  const { serviceId } = useParams();
  const navigate = useNavigate();
  const service = useBookingStore((state) => state.services.find((item) => item.id === serviceId));
  const setDraftBooking = useBookingStore((state) => state.setDraftBooking);
  const accountEmail = useAccountStore((state) => state.email);
  const dates = useMemo(getAvailableDates, []);
  const [date, setDate] = useState(dates[0]?.iso ?? '');
  const [time, setTime] = useState('');
  const [email, setEmail] = useState(accountEmail ?? '');
  const [emailError, setEmailError] = useState('');

  if (!service) {
    return (
      <EmptyState
        icon={CalendarDays}
        title='Услуга не найдена'
        description='Вернитесь к списку услуг и выберите другую встречу.'
      />
    );
  }

  function continueToPayment() {
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setEmailError('Введите корректный email');
      return;
    }
    if (!time) return;
    const booking: Booking = {
      id: `booking-${Date.now()}`,
      serviceId: service!.id,
      serviceTitle: service!.title,
      psychologistName: 'Анна Смирнова',
      clientName: 'Пользователь Бриолина',
      clientEmail: email,
      date,
      time,
      duration: service!.duration,
      price: service!.price,
      status: 'upcoming',
      paymentStatus: 'pending',
    };
    setDraftBooking(booking);
    navigate('/dashboard/payment');
  }

  return (
    <main className='flex-1 overflow-y-auto px-4 py-8 md:px-8'>
      <div className='mx-auto max-w-5xl'>
        <button
          onClick={() => navigate('/dashboard/services')}
          className='text-secondary hover:text-primary mb-5 cursor-pointer text-[13px]'
        >
          ← Назад к услугам
        </button>
        <div className='grid gap-6 lg:grid-cols-[1fr_340px]'>
          <section className='border-border rounded-3xl border bg-white p-5 sm:p-7'>
            <h1 className='font-onest text-primary text-2xl font-medium'>Выберите дату и время</h1>
            <div className='text-secondary mt-2 flex items-center gap-2 text-[12px]'>
              <Globe2 size={14} /> Время указано для вашего часового пояса
            </div>

            <h2 className='text-primary mt-7 mb-3 text-[13px] font-semibold'>Дата</h2>
            <div className='grid grid-cols-4 gap-2 sm:grid-cols-8'>
              {dates.map((item) => (
                <button
                  key={item.iso}
                  onClick={() => {
                    setDate(item.iso);
                    setTime('');
                  }}
                  className={[
                    'flex cursor-pointer flex-col items-center rounded-2xl border px-2 py-3 transition-colors',
                    date === item.iso
                      ? 'border-accent bg-accent text-white'
                      : 'border-border hover:border-accent/50 text-primary',
                  ].join(' ')}
                >
                  <span className='text-[10px] uppercase opacity-75'>{item.weekday}</span>
                  <span className='mt-1 text-lg font-semibold'>{item.day}</span>
                  <span className='text-[10px] opacity-75'>{item.month}</span>
                </button>
              ))}
            </div>

            <h2 className='text-primary mt-7 mb-3 text-[13px] font-semibold'>Свободное время</h2>
            <div className='grid grid-cols-3 gap-2 sm:grid-cols-6'>
              {TIMES.map((item, index) => {
                const unavailable = index === 1 && date === dates[0]?.iso;
                return (
                  <button
                    key={item}
                    disabled={unavailable}
                    onClick={() => setTime(item)}
                    className={[
                      'cursor-pointer rounded-xl border px-2 py-2.5 text-[13px] transition-colors disabled:cursor-not-allowed disabled:opacity-30',
                      time === item
                        ? 'border-accent bg-accent/10 text-accent'
                        : 'border-border text-primary hover:border-accent/50',
                    ].join(' ')}
                  >
                    {item}
                  </button>
                );
              })}
            </div>

            <div className='mt-7 max-w-sm'>
              <Input
                label='Email для ссылки на созвон'
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setEmailError('');
                }}
                error={emailError}
                placeholder='mail@example.ru'
                type='email'
              />
            </div>
          </section>

          <aside className='border-border h-fit rounded-3xl border bg-white p-6'>
            <p className='text-muted text-[11px] tracking-wider uppercase'>Ваша запись</p>
            <h2 className='font-onest text-primary mt-2 text-xl font-medium'>{service.title}</h2>
            <div className='mt-5 flex flex-col gap-3 text-[13px]'>
              <p className='text-secondary flex items-center gap-2'>
                <UserRound size={16} /> Анна Смирнова
              </p>
              <p className='text-secondary flex items-center gap-2'>
                <Clock3 size={16} /> {service.duration} минут · онлайн
              </p>
              {time && (
                <p className='text-accent flex items-center gap-2 font-semibold'>
                  <Check size={16} />{' '}
                  {new Date(`${date}T12:00:00`).toLocaleDateString('ru-RU', {
                    day: 'numeric',
                    month: 'long',
                  })}
                  , {time}
                </p>
              )}
            </div>
            <div className='border-border my-5 border-t' />
            <div className='mb-5 flex items-end justify-between'>
              <span className='text-secondary text-[12px]'>К оплате</span>
              <span className='text-primary text-xl font-semibold'>
                {service.price.toLocaleString('ru-RU')} ₽
              </span>
            </div>
            <Button className='w-full' disabled={!time} onClick={continueToPayment}>
              Перейти к оплате
            </Button>
          </aside>
        </div>
      </div>
    </main>
  );
}
