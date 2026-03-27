import { Link } from 'react-router-dom';
import { Button } from '@/shared/uikit/Button';
import { Text } from '@/shared/uikit/Text';
import { useAuthStore } from '@/entities/session';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

const STEPS = [
  {
    n: '01',
    title: 'Расскажите о себе',
    body: 'Заполните профиль честно — что цените, чем живёте, чего ищете. Без анкет на пять страниц.',
  },
  {
    n: '02',
    title: 'Пройдите тест',
    body: 'Короткий тест помогает понять, кто вы в отношениях. Не ярлык — просто точка отсчёта.',
  },
  {
    n: '03',
    title: 'Напишите первым',
    body: 'Найдите кого-то близкого по духу и начните разговор. Всё остальное — за вами.',
  },
];

export function IndexPage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  });

  return (
    <div className='w-full self-start'>
      <section className='flex flex-col items-center gap-6 py-24 text-center'>
        <div className='flex flex-col gap-8'>
          <Text variant='overline' as='p'>
            Знакомства — Бриолин
          </Text>

          <div className='flex flex-col gap-4'>
            <Text variant='h1' className='text-primary text-[48px]!'>
              Найдите человека,
              <br />
              которому важно
              <br />
              то же, что и вам
            </Text>
            <Text
              variant='p-sm'
              className='text-secondary! max-w-sm text-[15px]! leading-7! font-normal!'
            >
              Бриолин — это не про свайпы и не про алгоритмы. Это про людей, которые знают, чего
              хотят.
            </Text>
          </div>

          <div className='flex items-center gap-3'>
            <Link to='/registration'>
              <Button size='lg'>Создать профиль</Button>
            </Link>
            <Link to='/login'>
              <Button variant='ghost' size='lg'>
                Уже есть аккаунт →
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section className='grid grid-cols-3 py-10'>
        {STEPS.map(({ n, title, body }, i) => (
          <div
            key={n}
            className={[
              'flex flex-col gap-5 py-8',
              i > 0 ? 'border-border border-l pl-10' : 'pr-10',
              i === 1 ? 'px-10' : '',
            ].join(' ')}
          >
            <span className='font-onest text-border text-[64px] leading-none font-medium select-none'>
              {n}
            </span>
            <div className='flex flex-col gap-2'>
              <Text variant='h4' className='text-primary'>
                {title}
              </Text>
              <Text variant='p-sm' className='text-secondary! text-[14px]! leading-6! font-normal!'>
                {body}
              </Text>
            </div>
          </div>
        ))}
      </section>

      <div className='mt-6 flex items-center justify-between py-10'>
        <Text variant='h3' className='text-primary'>
          Готовы начать?
        </Text>
        <Link to='/registration'>
          <Button size='lg'>Зарегистрироваться</Button>
        </Link>
      </div>

      <div className='py-6 text-center'>
        <Text variant='p-sm'>© 2026 Бриолин</Text>
      </div>
    </div>
  );
}
