import { AvatarUpload } from '@/entities/profile';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { RadioCardGroup } from '@/shared/uikit/RadioCardGroup';
import { Text } from '@/shared/uikit/Text';
import { useEffect, useState } from 'react';
import type { StepProps } from '@/features/onboarding/OnboardingPage';
import { toast } from '@/shared/toast/toast';
import { profileApi } from '@/entities/profile';
import { DatePickerField } from '@/shared/uikit/DatePicker';

const GENDER_OPTIONS = ['Мужской', 'Женский'];

export function ProfileStep({ onNext }: StepProps) {
  useEffect(() => {
    toast.info('Заполните профиль');
  }, []);

  const maxBirthDate = new Date();
  maxBirthDate.setFullYear(maxBirthDate.getFullYear() - 18);
  const maxBirthDateStr = maxBirthDate.toISOString().split('T')[0];

  function handleSubmit() {
    profileApi
      .createBasicProfile({
        first_name: firstName,
        last_name: lastName,
        gender: gender === 'Мужской' ? 'male' : 'female',
        city,
        date_of_birth: new Date(birthDate),
      })
      .then(() => {
        toast.success('Профиль успешно создан');
        onNext();
      })
      .catch(() => {
        toast.error('Ошибка при создании профиля');
      });
  }

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [gender, setGender] = useState<string>('Мужской');
  const [city, setCity] = useState('');
  const [birthDate, setBirthDate] = useState(maxBirthDate.toISOString().split('T')[0]);

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
          <AvatarUpload name={[firstName, lastName].filter(Boolean).join(' ') || undefined} />
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
          <div className='grid grid-cols-2 gap-4'>
            <Input
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              label='Имя'
              placeholder='Введите ваше имя'
            />
            <Input
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              label='Фамилия'
              placeholder='Введите вашу фамилию'
            />
            <Input
              value={city}
              onChange={(e) => setCity(e.target.value)}
              label='Город'
              placeholder='Например, Москва'
            />
            <DatePickerField
              label='Дата рождения'
              max={maxBirthDateStr}
              value={birthDate}
              onChange={setBirthDate}
            />
          </div>
          <div className='flex flex-col gap-2'>
            <label className='font-inter text-primary text-[12px] font-medium'>Пол</label>
            <RadioCardGroup items={GENDER_OPTIONS} value={gender} onChange={setGender} />
          </div>
        </div>
        <div className='flex flex-col gap-4 text-center'>
          <Button onClick={handleSubmit}>Далее</Button>
        </div>
      </div>
    </>
  );
}
