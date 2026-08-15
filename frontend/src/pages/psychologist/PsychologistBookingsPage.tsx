import { useMemo, useState } from 'react';
import { CalendarX, Search, Video } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBookingStore, type BookingStatus } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { EmptyState } from '@/shared/uikit/EmptyState';

const FILTERS: { value: BookingStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'upcoming', label: 'Предстоящие' },
  { value: 'completed', label: 'Завершённые' },
  { value: 'cancelled', label: 'Отменённые' },
];

export function PsychologistBookingsPage() {
  const navigate = useNavigate();
  const bookings = useBookingStore((state) => state.bookings);
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');
  const [query, setQuery] = useState('');
  const filtered = useMemo(
    () =>
      bookings.filter(
        (item) =>
          (filter === 'all' || item.status === filter) &&
          item.clientName.toLowerCase().includes(query.toLowerCase()),
      ),
    [bookings, filter, query],
  );

  return (
    <main className='px-4 py-8 md:px-10'>
      <div className='mx-auto max-w-6xl'>
        <h1 className='font-onest text-primary text-3xl font-medium'>Записи</h1>
        <p className='text-secondary mt-2 text-[13px]'>
          Управляйте встречами и заполняйте результаты собеседований.
        </p>
        <div className='mt-7 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
          <div className='flex gap-1 overflow-x-auto'>
            {FILTERS.map((item) => (
              <button
                key={item.value}
                onClick={() => setFilter(item.value)}
                className={`cursor-pointer rounded-xl px-4 py-2 text-[12px] whitespace-nowrap ${filter === item.value ? 'bg-accent text-white' : 'text-secondary bg-white'}`}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className='w-full sm:w-64'>
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder='Поиск по клиенту'
            />
          </div>
        </div>
        <div className='mt-5 flex flex-col gap-3'>
          {filtered.map((booking) => (
            <article
              key={booking.id}
              className='border-border flex flex-col gap-4 rounded-2xl border bg-white p-5 lg:flex-row lg:items-center'
            >
              <div className='bg-surface flex min-w-28 flex-row items-center gap-2 rounded-xl px-3 py-2 lg:flex-col lg:gap-0'>
                <span className='text-primary text-[13px] font-semibold'>{booking.date}</span>
                <span className='text-accent text-[16px] font-semibold'>{booking.time}</span>
              </div>
              <div className='min-w-0 flex-1'>
                <h2 className='text-primary text-[14px] font-semibold'>{booking.clientName}</h2>
                <p className='text-secondary mt-1 text-[12px]'>
                  {booking.serviceTitle} · {booking.duration} минут
                </p>
              </div>
              <span
                className={`w-fit rounded-full px-3 py-1 text-[11px] ${booking.status === 'upcoming' ? 'bg-blue-50 text-blue-700' : booking.result ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}
              >
                {booking.status === 'upcoming'
                  ? 'Предстоит'
                  : booking.result
                    ? 'Результат заполнен'
                    : 'Ждёт результата'}
              </span>
              <div className='flex gap-2'>
                {booking.meetingUrl && (
                  <Button
                    variant='secondary'
                    size='sm'
                    onClick={() => window.open(booking.meetingUrl, '_blank')}
                  >
                    <Video size={15} /> Созвон
                  </Button>
                )}
                <Button
                  size='sm'
                  onClick={() => navigate(`/psychologist/bookings/${booking.id}/result`)}
                >
                  {booking.result ? 'Просмотреть' : 'Заполнить результат'}
                </Button>
              </div>
            </article>
          ))}
          {filtered.length === 0 && (
            <EmptyState
              icon={query ? Search : CalendarX}
              title='Записей не найдено'
              description='Измените фильтр или поисковый запрос.'
            />
          )}
        </div>
      </div>
    </main>
  );
}
