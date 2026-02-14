import { MoveLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Text } from '@/components/ui/Text';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function RegisterPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between gap-4">
        <Link className="flex items-center gap-2" to="/">
          <MoveLeft />
          Назад
        </Link>
        <div className="hidden items-center gap-4 sm:flex md:gap-8">
          <Link to="/login">Авторизация</Link>
          <Link to="/reset-password">Забыли пароль?</Link>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-6 pt-10 text-center md:gap-8 md:pt-20">
          <Text variant="heading" size="xl">
            Регистрация
          </Text>
          <Text variant="base" className="mx-auto max-w-md">
            Заполни полностью профиль, чтобы мы помогли тебе найти идеального
            партнера.
          </Text>
        </div>
        <div className="flex w-full max-w-md flex-col gap-4 px-4">
          <Input placeholder="Почта" />
          <Input placeholder="Логин" />
          <Input type="password" placeholder="Пароль" />
        </div>
        <Button
          variant="solid"
          onClick={() => navigate('/registration-complete')}
          className="w-full md:w-3xs"
        >
          Далее
        </Button>
      </div>
    </div>
  );
}
