import { Clock3, Pencil, Plus, Power, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';
import { ConfirmDialog } from '@/shared/uikit/ConfirmDialog';
import { useState } from 'react';

export function PsychologistServicesPage() {
  const navigate = useNavigate();
  const services = useBookingStore((state) => state.services);
  const toggleService = useBookingStore((state) => state.toggleService);
  const removeService = useBookingStore((state) => state.removeService);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  return (
    <main className='px-4 py-8 md:px-10'>
      <div className='mx-auto max-w-5xl'>
        <div className='flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between'>
          <div>
            <h1 className='font-onest text-primary text-3xl font-medium'>Мои услуги</h1>
            <p className='text-secondary mt-2 text-[13px]'>
              Настройте консультации, которые доступны пользователям.
            </p>
          </div>
          <Button onClick={() => navigate('/psychologist/services/new')}>
            <Plus size={17} /> Добавить услугу
          </Button>
        </div>
        <div className='mt-7 grid gap-4 md:grid-cols-2'>
          {services.map((service) => (
            <article
              key={service.id}
              className={`border-border rounded-3xl border bg-white p-6 ${!service.active ? 'opacity-60' : ''}`}
            >
              <div className='flex items-start justify-between gap-3'>
                <span className='bg-surface text-secondary rounded-full px-3 py-1 text-[11px]'>
                  {service.type}
                </span>
                <span
                  className={`rounded-full px-3 py-1 text-[10px] ${service.active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}
                >
                  {service.active ? 'Активна' : 'Скрыта'}
                </span>
              </div>
              <h2 className='font-onest text-primary mt-5 text-xl font-medium'>{service.title}</h2>
              <p className='text-secondary mt-2 min-h-10 text-[12px] leading-5'>
                {service.description}
              </p>
              <div className='mt-5 flex items-end justify-between'>
                <p className='text-secondary flex items-center gap-1.5 text-[12px]'>
                  <Clock3 size={15} /> {service.duration} минут
                </p>
                <p className='text-primary text-xl font-semibold'>
                  {service.price.toLocaleString('ru-RU')} ₽
                </p>
              </div>
              <div className='border-border mt-5 flex gap-2 border-t pt-4'>
                <Button
                  variant='secondary'
                  size='sm'
                  className='flex-1'
                  onClick={() => navigate(`/psychologist/services/${service.id}/edit`)}
                >
                  <Pencil size={14} /> Изменить
                </Button>
                <Button
                  variant='ghost'
                  size='sm'
                  onClick={() => toggleService(service.id)}
                  title={service.active ? 'Скрыть услугу' : 'Опубликовать услугу'}
                >
                  <Power size={15} />
                </Button>
                <Button
                  variant='ghost'
                  size='sm'
                  className='text-destructive!'
                  onClick={() => setDeletingId(service.id)}
                  title='Удалить'
                >
                  <Trash2 size={15} />
                </Button>
              </div>
            </article>
          ))}
        </div>
        {deletingId && (
          <ConfirmDialog
            title='Удалить услугу?'
            description='Она исчезнет из списка доступных консультаций. Это действие нельзя отменить.'
            confirmLabel='Удалить'
            destructive
            onConfirm={() => {
              removeService(deletingId);
              setDeletingId(null);
            }}
            onClose={() => setDeletingId(null)}
          />
        )}
      </div>
    </main>
  );
}
