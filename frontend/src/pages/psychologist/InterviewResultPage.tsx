import { useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { CheckCircle2, Save, XCircle } from 'lucide-react';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { Textarea } from '@/shared/uikit/Textarea';
import { toast } from '@/shared/toast/toast';

export function InterviewResultPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const booking = useBookingStore((state) => state.bookings.find((item) => item.id === bookingId));
  const saveInterviewResult = useBookingStore((state) => state.saveInterviewResult);
  const [result, setResult] = useState<'passed' | 'failed' | undefined>(booking?.result);
  const [recommendations, setRecommendations] = useState(booking?.recommendations ?? '');
  const [privateNote, setPrivateNote] = useState(booking?.privateNote ?? '');
  const [error, setError] = useState('');
  if (!booking) return <Navigate to='/psychologist/bookings' replace />;

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!result) {
      setError('Выберите результат собеседования');
      return;
    }
    if (recommendations.trim().length < 10) {
      setError('Добавьте персональные рекомендации');
      return;
    }
    saveInterviewResult(booking!.id, { result, recommendations, privateNote });
    toast.success('Результат сохранён');
    navigate('/psychologist/bookings');
  }

  return (
    <main className='px-4 py-8 md:px-10'>
      <div className='mx-auto max-w-3xl'>
        <button
          onClick={() => navigate('/psychologist/bookings')}
          className='text-secondary mb-5 cursor-pointer text-[13px]'
        >
          ← К записям
        </button>
        <form onSubmit={submit} className='border-border rounded-3xl border bg-white p-6 sm:p-8'>
          <div className='border-border border-b pb-5'>
            <p className='text-accent text-[11px] font-semibold tracking-wider uppercase'>
              Результат собеседования
            </p>
            <h1 className='font-onest text-primary mt-2 text-2xl font-medium'>
              {booking.clientName}
            </h1>
            <p className='text-secondary mt-1 text-[12px]'>
              {booking.serviceTitle} · {booking.date}, {booking.time}
            </p>
          </div>
          <div className='mt-6'>
            <p className='text-primary mb-3 text-[13px] font-semibold'>Решение по кандидату</p>
            <div className='grid gap-3 sm:grid-cols-2'>
              <button
                type='button'
                onClick={() => {
                  setResult('passed');
                  setError('');
                }}
                className={`flex cursor-pointer items-center gap-3 rounded-2xl border p-4 text-left ${result === 'passed' ? 'border-green-500 bg-green-50 text-green-800' : 'border-border text-secondary'}`}
              >
                <CheckCircle2 size={22} />
                <span>
                  <strong className='block text-[13px]'>Кандидат прошёл</strong>
                  <small>Рекомендовать продолжение</small>
                </span>
              </button>
              <button
                type='button'
                onClick={() => {
                  setResult('failed');
                  setError('');
                }}
                className={`flex cursor-pointer items-center gap-3 rounded-2xl border p-4 text-left ${result === 'failed' ? 'border-red-400 bg-red-50 text-red-800' : 'border-border text-secondary'}`}
              >
                <XCircle size={22} />
                <span>
                  <strong className='block text-[13px]'>Кандидат не прошёл</strong>
                  <small>Завершить отбор</small>
                </span>
              </button>
            </div>
          </div>
          <div className='mt-6 flex flex-col gap-5'>
            <Textarea
              label='Персональные рекомендации'
              value={recommendations}
              onChange={(value) => {
                setRecommendations(value);
                setError('');
              }}
              rows={6}
              placeholder='Рекомендации, которые увидит кандидат'
            />
            <Textarea
              label='Внутренняя заметка'
              value={privateNote}
              onChange={setPrivateNote}
              rows={4}
              placeholder='Эта информация не показывается кандидату'
            />
            {error && <p className='text-destructive text-[12px]'>{error}</p>}
          </div>
          <div className='border-border mt-6 flex justify-end gap-3 border-t pt-5'>
            <Button
              type='button'
              variant='secondary'
              onClick={() => {
                localStorage.setItem(
                  `interview-draft-${booking.id}`,
                  JSON.stringify({ result, recommendations, privateNote }),
                );
                toast.success('Черновик сохранён');
              }}
            >
              Сохранить черновик
            </Button>
            <Button type='submit'>
              <Save size={16} /> Завершить
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}
