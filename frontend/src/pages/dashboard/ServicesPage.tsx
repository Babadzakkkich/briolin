import { ArrowRight, Clock3, Monitor, ShieldCheck, Star } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBookingStore } from '@/entities/booking';
import { Button } from '@/shared/uikit/Button';

export function ServicesPage() {
  const navigate = useNavigate();
  const allServices = useBookingStore((state) => state.services);
  const services = useMemo(() => allServices.filter((service) => service.active), [allServices]);

  return (
    <main className='flex-1 overflow-y-auto px-4 py-8 md:px-8'>
      <div className='mx-auto max-w-5xl'>
        <div className='mb-8 max-w-2xl'>
          <p className='text-accent mb-2 text-[12px] font-semibold tracking-[0.14em] uppercase'>
            Поддержка специалиста
          </p>
          <h1 className='font-onest text-primary text-3xl font-medium'>Встречи с психологом</h1>
          <p className='text-secondary mt-3 text-[14px] leading-6'>
            Выберите формат встречи, удобные дату и время. После подтверждения ссылка на созвон
            появится в записи и будет отправлена на вашу почту.
          </p>
        </div>

        <div className='grid gap-5 md:grid-cols-2'>
          {services.map((service, index) => (
            <article
              key={service.id}
              className='border-border flex flex-col rounded-3xl border bg-white p-6 shadow-sm'
            >
              <div className='mb-5 flex items-start justify-between gap-4'>
                <div className='bg-accent/10 text-accent flex h-11 w-11 items-center justify-center rounded-2xl'>
                  {index === 0 ? <ShieldCheck size={21} /> : <Star size={21} />}
                </div>
                <span className='bg-surface text-secondary rounded-full px-3 py-1 text-[11px]'>
                  {service.type}
                </span>
              </div>
              <h2 className='font-onest text-primary text-xl font-medium'>{service.title}</h2>
              <p className='text-secondary mt-2 min-h-12 text-[13px] leading-5'>
                {service.description}
              </p>
              <div className='text-secondary my-5 flex gap-4 text-[12px]'>
                <span className='flex items-center gap-1.5'>
                  <Clock3 size={15} /> {service.duration} минут
                </span>
                <span className='flex items-center gap-1.5'>
                  <Monitor size={15} /> {service.format === 'online' ? 'Онлайн' : 'Очно'}
                </span>
              </div>
              <div className='border-border mt-auto flex items-end justify-between border-t pt-5'>
                <div>
                  <p className='text-muted text-[11px]'>Стоимость</p>
                  <p className='text-primary text-xl font-semibold'>
                    {service.price.toLocaleString('ru-RU')} ₽
                  </p>
                </div>
                <Button onClick={() => navigate(`/dashboard/services/${service.id}/booking`)}>
                  Выбрать <ArrowRight size={16} />
                </Button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
