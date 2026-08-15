import { ArrowRight, Check } from 'lucide-react';
import { Button } from '@/shared/uikit/Button';
import { LogoIcon } from '@/shared/icons/Logo';
import type { StepProps } from '@/features/onboarding/model/types';

const NEXT_STEPS = [
  {
    title: 'Заполните профиль',
    text: 'Добавьте основную информацию о себе.',
  },
  {
    title: 'Ответьте на вопросы',
    text: 'Обязательная анкета займёт около 7 минут.',
  },
  {
    title: 'Получите результат',
    text: 'Покажем результат и предложим следующий шаг.',
  },
];

export function WelcomeStep({ onNext }: StepProps) {
  return (
    <section className='border-border w-full max-w-lg rounded-2xl border bg-white px-6 py-7 sm:px-9 sm:py-9'>
      <div className='flex items-center gap-2'>
        <LogoIcon size={24} />
        <span className='font-onest text-primary text-[15px] font-medium'>Бриолин</span>
      </div>

      <div className='mt-8'>
        <div className='border-border text-accent flex h-9 w-9 items-center justify-center rounded-full border'>
          <Check size={17} strokeWidth={2.4} />
        </div>
        <h1 className='font-onest text-primary mt-5 text-[28px] leading-tight font-medium sm:text-[32px]'>
          Регистрация завершена
        </h1>
        <p className='text-secondary mt-3 max-w-md text-[14px] leading-6'>
          Теперь подготовим ваш профиль к работе. Нужно пройти три коротких шага.
        </p>
      </div>

      <ol className='border-border mt-8 border-t'>
        {NEXT_STEPS.map(({ title, text }, index) => (
          <li
            key={title}
            className='border-border grid grid-cols-[28px_1fr] gap-3 border-b py-4 last:border-b-0'
          >
            <span className='text-muted pt-0.5 text-[12px] tabular-nums'>
              {String(index + 1).padStart(2, '0')}
            </span>
            <div>
              <p className='text-primary text-[13px] font-semibold'>{title}</p>
              <p className='text-secondary mt-1 text-[12px] leading-5'>{text}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className='mt-7 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'>
        <p className='text-muted text-[11px]'>Примерное время — 10 минут</p>
        <Button onClick={() => onNext()} className='sm:min-w-40'>
          Продолжить <ArrowRight size={16} />
        </Button>
      </div>
    </section>
  );
}
