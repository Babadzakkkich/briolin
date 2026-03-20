import { AvatarUpload } from '@/features/AvatarUpload';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { RadioCardGroup } from '@/shared/uikit/RadioCardGroup';
import { Text } from '@/shared/uikit/Text';
import { useState } from 'react';
import type { StepProps } from '../OnboardingPage';
import { toast } from '@/shared/toast/toast';

const GENDER_OPTIONS = ['Мужской', 'Женский'];

export function ProfileStep({ onNext }: StepProps) {
  const [gender, setGender] = useState('Мужской');
  toast.success('Заполните профиль');

  return (
    <>
      <div className='border-border flex w-120 flex-col gap-8 rounded-lg border bg-white px-8 py-8'>
        <div className='flex flex-col text-center'>
          <Text variant='h2' as='h2'>
            Заполните профиль
          </Text>
          <Text variant='p' as='p'>
            Расскажите нам о Вас подробнее
          </Text>
        </div>
        <div className='flex w-full gap-4'>
          <AvatarUpload />
          <div className='flex flex-col justify-between py-4'>
            <Text variant='p' as='p'>
              Загрузите фото
            </Text>
            <Text variant='p-sm' as='p'>
              JPG или PNG до 5МБ
            </Text>
          </div>
        </div>
        <div className='flex flex-col gap-4'>
          <div className='flex gap-4'>
            <Input label='Имя' placeholder='Введите ваше имя' />
            <Input label='Фамилия' placeholder='Введите вашу фамилию' />
          </div>
          <div className='flex gap-4'>
            <Input label='Имя' placeholder='Введите ваше имя' />
            <Input label='Фамилия' placeholder='Введите вашу фамилию' />
          </div>
          <div className='flex flex-col gap-2'>
            <label className='font-inter text-primary text-[12px] font-medium'>Пол</label>
            <RadioCardGroup items={GENDER_OPTIONS} value={gender} onChange={setGender} />
          </div>
        </div>
        <div className='flex flex-col gap-4 text-center'>
          <Button onClick={onNext}>Далее</Button>
        </div>
      </div>
    </>
  );
}
