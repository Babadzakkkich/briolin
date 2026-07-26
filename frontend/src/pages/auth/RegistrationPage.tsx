import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';
import { toast } from '@/shared/toast/toast';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { z } from 'zod';

const RegistrationFormSchema = z.object({
  email: z.email('Некорректный email'),
  password: z.string().min(6, 'Минимум 6 символов'),
  username: z
    .string()
    .min(3, 'Минимум 3 символа')
    .max(50, 'Максимум 50 символов')
    .regex(/^[a-zA-Z0-9]+$/, 'Только латиница и цифры'),
});

type RegistrationForm = z.infer<typeof RegistrationFormSchema>;
type FormErrors = Partial<Record<keyof RegistrationForm, string>>;

export function RegistrationPage() {
  const { register } = useAuth();

  const [fields, setFields] = useState<RegistrationForm>({
    username: '',
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  const setField = (key: keyof RegistrationForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields((prev) => ({ ...prev, [key]: e.target.value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();

    const result = RegistrationFormSchema.safeParse(fields);
    if (!result.success) {
      const fieldErrors = Object.fromEntries(
        result.error.issues.map((issue) => [issue.path[0], issue.message]),
      );
      setErrors(fieldErrors);
      return;
    }

    setLoading(true);
    try {
      await register(result.data.email, result.data.username, result.data.password);
      toast.success('Аккаунт создаётся, войдите через несколько секунд');
    } catch {
      toast.error('Не удалось создать аккаунт');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className='border-border flex w-100 flex-col gap-8 rounded-lg border bg-white px-8 py-8'
    >
      <div className='flex flex-col text-center'>
        <Text variant='h2' as='h2'>
          Регистрация
        </Text>
        <Text variant='p-sm' as='p'>
          Создайте свой профиль
        </Text>
      </div>

      <div className='flex w-full flex-col gap-4'>
        <Input
          label='Логин'
          placeholder='Придумайте логин'
          value={fields.username}
          onChange={setField('username')}
          error={errors.username}
        />
        <Input
          label='Почта'
          placeholder='mail@example.ru'
          type='email'
          value={fields.email}
          onChange={setField('email')}
          error={errors.email}
        />
        <Input
          label='Пароль'
          placeholder='Придумайте пароль'
          type='password'
          value={fields.password}
          onChange={setField('password')}
          error={errors.password}
        />
      </div>

      <div className='flex flex-col gap-4 text-center'>
        <Button type='submit' disabled={loading}>
          {loading ? 'Создаём...' : 'Создать аккаунт'}
        </Button>
        <div className='flex flex-col'>
          <Text variant='p-sm'>Уже есть аккаунт?</Text>
          <Link to='/login'>
            <Text className='text-accent! underline' variant='p-sm'>
              Войти
            </Text>
          </Link>
        </div>
      </div>
    </form>
  );
}
