import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

export function PayInterviewPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Text>/оплата</Text>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex w-full flex-col gap-6 pt-10 text-left md:gap-8 md:pt-20">
          <Text variant="base" size="lg">
            Ваша запись подверждена!
          </Text>
          <Text variant="base">
            Мы зарезервировали для вас время с психологом. Пожалуйста, перейдите
            к оплате, чтобы завершить процесс.
          </Text>
        </div>
        <div className="mt-20 flex w-full justify-end md:mt-40">
          <Button
            onClick={() => navigate('/interview/end')}
            variant="solid"
            className="w-full md:w-3xs"
          >
            Оплатить
          </Button>
        </div>
      </div>
    </div>
  );
}
