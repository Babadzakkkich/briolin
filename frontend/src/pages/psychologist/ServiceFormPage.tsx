import { useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { Save } from 'lucide-react';
import { useBookingStore, type PsychologistService, type ServiceFormat } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Textarea } from '@/shared/uikit/Textarea';
import { toast } from '@/shared/toast/toast';

export function ServiceFormPage() {
  const { serviceId } = useParams();
  const navigate = useNavigate();
  const existing = useBookingStore((state) => state.services.find((item) => item.id === serviceId));
  const saveService = useBookingStore((state) => state.saveService);
  const isNew = !serviceId;
  const [form, setForm] = useState<PsychologistService>(
    existing ?? {
      id: `service-${Date.now()}`,
      title: '',
      type: 'Индивидуальная консультация',
      description: '',
      duration: 50,
      price: 0,
      format: 'online',
      active: true,
    },
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  if (!isNew && !existing) return <Navigate to='/psychologist/services' replace />;

  function set<K extends keyof PsychologistService>(key: K, value: PsychologistService[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: '' }));
  }
  function submit(event: React.FormEvent) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (form.title.trim().length < 3) nextErrors.title = 'Введите название услуги';
    if (form.description.trim().length < 20)
      nextErrors.description = 'Добавьте описание не короче 20 символов';
    if (form.duration < 15) nextErrors.duration = 'Минимум 15 минут';
    if (form.price < 0) nextErrors.price = 'Стоимость не может быть отрицательной';
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }
    saveService(form);
    toast.success(isNew ? 'Услуга добавлена' : 'Изменения сохранены');
    navigate('/psychologist/services');
  }

  return (
    <main className='px-4 py-8 md:px-10'>
      <div className='mx-auto max-w-2xl'>
        <button
          onClick={() => navigate('/psychologist/services')}
          className='text-secondary mb-5 cursor-pointer text-[13px]'
        >
          ← К услугам
        </button>
        <form onSubmit={submit} className='border-border rounded-3xl border bg-white p-6 sm:p-8'>
          <h1 className='font-onest text-primary text-2xl font-medium'>
            {isNew ? 'Новая услуга' : 'Редактирование услуги'}
          </h1>
          <p className='text-secondary mt-2 text-[12px]'>
            Эти данные увидят пользователи перед записью.
          </p>
          <div className='mt-7 flex flex-col gap-5'>
            <Input
              label='Название'
              value={form.title}
              onChange={(event) => set('title', event.target.value)}
              error={errors.title}
              placeholder='Например, первичное собеседование'
            />
            <Input
              label='Тип консультации'
              value={form.type}
              onChange={(event) => set('type', event.target.value)}
              placeholder='Индивидуальная консультация'
            />
            <Textarea
              label='Описание'
              value={form.description}
              onChange={(value) => set('description', value)}
              error={errors.description}
              rows={5}
              placeholder='Расскажите, кому подходит услуга и как пройдёт встреча'
            />
            <div className='grid gap-4 sm:grid-cols-2'>
              <Input
                label='Продолжительность, минут'
                type='number'
                min={15}
                step={5}
                value={form.duration}
                onChange={(event) => set('duration', Number(event.target.value))}
                error={errors.duration}
              />
              <Input
                label='Стоимость, ₽'
                type='number'
                min={0}
                value={form.price}
                onChange={(event) => set('price', Number(event.target.value))}
                error={errors.price}
              />
            </div>
            <div>
              <p className='text-primary mb-2 text-[12px]'>Формат</p>
              <div className='grid grid-cols-2 gap-2'>
                {(['online', 'offline'] as ServiceFormat[]).map((format) => (
                  <button
                    type='button'
                    key={format}
                    onClick={() => set('format', format)}
                    className={`cursor-pointer rounded-xl border px-4 py-3 text-[13px] ${form.format === format ? 'border-accent bg-accent/10 text-accent' : 'border-border text-secondary'}`}
                  >
                    {format === 'online' ? 'Онлайн' : 'Очно'}
                  </button>
                ))}
              </div>
            </div>
            <label className='bg-surface flex cursor-pointer items-center justify-between rounded-2xl p-4'>
              <span>
                <strong className='text-primary block text-[13px]'>Услуга активна</strong>
                <small className='text-secondary'>Показывать пользователям в каталоге</small>
              </span>
              <input
                type='checkbox'
                checked={form.active}
                onChange={(event) => set('active', event.target.checked)}
                className='accent-accent h-5 w-5'
              />
            </label>
            <div className='border-border flex justify-end gap-3 border-t pt-5'>
              <Button
                type='button'
                variant='secondary'
                onClick={() => navigate('/psychologist/services')}
              >
                Отмена
              </Button>
              <Button type='submit'>
                <Save size={16} /> Сохранить
              </Button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
