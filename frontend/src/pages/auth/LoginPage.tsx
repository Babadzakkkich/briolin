import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';
import { toast } from '@/shared/toast/toast';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';
import { z } from 'zod';

const LoginFormSchema = z.object({
  username: z.string().min(1, 'Введите логин'),
  password: z.string().min(1, 'Введите пароль'),
});

type LoginForm = z.infer<typeof LoginFormSchema>;
type FormErrors = Partial<Record<keyof LoginForm, string>>;

export function LoginPage() {
  const { login } = useAuth();

  const [fields, setFields] = useState<LoginForm>({ username: '', password: '' });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  const setField = (key: keyof LoginForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields((prev) => ({ ...prev, [key]: e.target.value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }));
  };

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();

    const result = LoginFormSchema.safeParse(fields);
    if (!result.success) {
      setErrors(
        Object.fromEntries(result.error.issues.map((issue) => [issue.path[0], issue.message])),
      );
      return;
    }

    setLoading(true);
    try {
      await login(result.data.username, result.data.password);
    } catch {
      toast.error('Неверный логин или пароль');
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
          Вход
        </Text>
        <Text variant='p-sm' as='p'>
          Войдите в свой аккаунт
        </Text>
      </div>

      <div className='flex w-full flex-col gap-4'>
        <Input
          label='Логин'
          placeholder='Введите логин'
          value={fields.username}
          onChange={setField('username')}
          error={errors.username}
        />
        <div className='flex flex-col gap-1.5'>
          <div className='flex items-center justify-between'>
            <span className='font-inter text-muted text-[12px] font-medium'>Пароль</span>
            <Link
              to='/forgot-password'
              className='font-inter text-secondary hover:text-accent text-[12px] transition-colors'
            >
              Забыли пароль?
            </Link>
          </div>
          <Input
            placeholder='Введите пароль'
            type='password'
            value={fields.password}
            onChange={setField('password')}
            error={errors.password}
          />
        </div>
      </div>

      <div className='flex flex-col gap-4 text-center'>
        <Button type='submit' disabled={loading}>
          {loading ? 'Входим...' : 'Войти'}
        </Button>
        <div className='flex flex-col'>
          <Text variant='p-sm'>Еще нет аккаунта?</Text>
          <Link to='/registration'>
            <Text className='text-accent! underline' variant='p-sm'>
              Зарегистрироваться
            </Text>
          </Link>
        </div>
      </div>
    </form>
  );
}
