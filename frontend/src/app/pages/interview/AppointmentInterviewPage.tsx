import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

export function AppointmentInterviewPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Text>/запись на собеседование</Text>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-6 pt-10 text-left md:gap-8 md:pt-20">
          <Text variant="base" size="lg">
            Выбери удобное время для созвона!
          </Text>
          <Text variant="base">
            Следующий этап — короткое собеседование с нашим психологом. Это
            дружеский разговор, где мы уточним твои ответы и лучше поймём, кого
            тебе стоит встретить. Выбери удобный слот и будь собой — именно так
            мы сможем найти людей, которые подходят тебе по-настоящему.
          </Text>
        </div>
        <div className="mt-20 flex w-full justify-end md:mt-40">
          <Button
            variant="solid"
            onClick={() => navigate('/interview/details')}
            className="w-full md:w-3xs"
          >
            Записаться
          </Button>
        </div>
      </div>
    </div>
  );
}
