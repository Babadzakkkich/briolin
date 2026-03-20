import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/features/auth/useAuth';
import { toast } from '@/shared/toast/toast';
import { Button } from '@/shared/uikit/Button';
import { Input } from '@/shared/uikit/Input';
import { Text } from '@/shared/uikit/Text';

export function RegistrationPage() {
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!username || !email || !password) return;

    setLoading(true);
    try {
      await register(email, username, password);
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
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <Input
          label='Почта'
          placeholder='mail@example.ru'
          type='email'
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label='Пароль'
          placeholder='Придумайте пароль'
          type='password'
          value={password}
          onChange={(e) => setPassword(e.target.value)}
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
