import { MoveLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

export function ResetPasswordPage() {
  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MoveLeft />
          <Link to="/">Назад</Link>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex max-w-3xl flex-col gap-6 pt-10 text-center md:gap-8 md:pt-20">
          <Text variant="heading" size="xl">
            Эх, забыли пароль?
          </Text>
          <Text variant="base">
            Сбросьте свой пароль, перейдя по ссылке в письме, которое мы вам
            отправили. После этого вы сможете войти в свой профиль с новым
            паролем!
          </Text>
        </div>
        <div className="h-20 md:h-40"></div>
        <Button variant="solid" className="w-full md:w-3xs">
          Сбросить пароль
        </Button>
      </div>
    </div>
  );
}
