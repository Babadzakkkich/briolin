import { AvatarUpload } from '@/entities/profile';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { RadioCardGroup } from '@/shared/uikit/RadioCardGroup';
import { Text } from '@/shared/uikit/Text';
import { useState } from 'react';
import type { StepProps } from '@/features/onboarding/model/types';
import { toast } from '@/shared/toast/toast';
import { profileApi } from '@/entities/profile';
import { DatePickerField } from '@/shared/uikit/DatePicker';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const GENDER_OPTIONS = ['Мужской', 'Женский'];

const differenceInYears = (dateFrom: Date, dateTo: Date): number => {
  let years = dateFrom.getFullYear() - dateTo.getFullYear();
  const hasNotReachedAnniversary =
    dateFrom.getMonth() < dateTo.getMonth() ||
    (dateFrom.getMonth() === dateTo.getMonth() && dateFrom.getDate() < dateTo.getDate());
  if (hasNotReachedAnniversary) years--;
  return years;
};

const MAX_BIRTH_DATE = new Date();
MAX_BIRTH_DATE.setFullYear(MAX_BIRTH_DATE.getFullYear() - 18);
const MAX_BIRTH_DATE_STR = MAX_BIRTH_DATE.toISOString().split('T')[0];

const BasicProfileSchema = z.object({
  firstName: z.string().min(1, 'Введите имя').max(50),
  lastName: z.string().min(1, 'Введите фамилию').max(50),
  city: z.string().min(1, 'Введите город').max(100),
  gender: z.enum(['Мужской', 'Женский']),
  birthDate: z.iso.date().refine((date) => {
    return differenceInYears(new Date(), new Date(date)) >= 18;
  }, 'Вам должно быть не менее 18 лет'),
});

type BasicProfileForm = z.infer<typeof BasicProfileSchema>;

export function ProfileStep({ onNext }: StepProps) {
  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<BasicProfileForm>({
    resolver: zodResolver(BasicProfileSchema),
    defaultValues: {
      gender: 'Мужской',
      birthDate: MAX_BIRTH_DATE_STR,
    },
  });

  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  const [firstName, lastName] = watch(['firstName', 'lastName']);
  const fullName = [firstName, lastName].filter(Boolean).join(' ') || undefined;

  const onSubmit = async (data: BasicProfileForm) => {
    await profileApi.createBasicProfile({
      first_name: data.firstName,
      last_name: data.lastName,
      gender: data.gender === 'Мужской' ? 'male' : 'female',
      city: data.city,
      date_of_birth: new Date(data.birthDate),
    });
    toast.success('Профиль успешно создан');
    onNext();
  };

  const onError = () => {
    toast.error('Заполните все поля корректно');
  };

  return (
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
        <AvatarUpload
          src={avatarUrl}
          name={fullName}
          onUploaded={(url) => setAvatarUrl(url || null)}
        />
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
            {...register('firstName')}
            label='Имя'
            placeholder='Введите ваше имя'
            error={errors.firstName?.message}
          />
          <Input
            {...register('lastName')}
            label='Фамилия'
            placeholder='Введите вашу фамилию'
            error={errors.lastName?.message}
          />
          <Input
            {...register('city')}
            label='Город'
            placeholder='Например, Москва'
            error={errors.city?.message}
          />
          <Controller
            control={control}
            name='birthDate'
            render={({ field }) => (
              <DatePickerField
                label='Дата рождения'
                max={MAX_BIRTH_DATE_STR}
                value={field.value}
                onChange={field.onChange}
                error={errors.birthDate?.message}
              />
            )}
          />
        </div>

        <div className='flex flex-col gap-2'>
          <label className='font-inter text-primary text-[12px] font-medium'>Пол</label>
          <Controller
            control={control}
            name='gender'
            render={({ field }) => (
              <RadioCardGroup
                items={GENDER_OPTIONS}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </div>
      </div>

      <Button onClick={handleSubmit(onSubmit, onError)} disabled={isSubmitting}>
        {isSubmitting ? 'Сохранение...' : 'Далее'}
      </Button>
    </div>
  );
}
