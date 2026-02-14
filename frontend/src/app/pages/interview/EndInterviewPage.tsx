import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

export function EndInterviewPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Text>/окончание собеседования</Text>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-6 pt-10 text-left md:gap-8 md:pt-20">
          <Text variant="base" size="lg">
            Идёт обработка результатов!
          </Text>
          <Text variant="base">
            Психолог анализирует ответы и готовит персональные рекомендации.
            Когда итоги будут готовы, ты сможешь увидеть их в личном кабинете.
            Мы уведомим тебя по почте, как только данные обновятся.
          </Text>
        </div>
        <div className="mt-20 flex w-full justify-end md:mt-40">
          <Button
            onClick={() => navigate('/interview/result')}
            variant="solid"
            className="w-full md:w-3xs"
          >
            Далее
          </Button>
        </div>
      </div>
    </div>
  );
}
