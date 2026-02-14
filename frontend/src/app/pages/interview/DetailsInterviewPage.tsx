import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { Calendar, GraduationCap } from 'lucide-react';

export function DetailsInterviewPage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Text>/детали записи</Text>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="gap-6 pt-10 text-left md:gap-8 md:pt-20">
          <Text variant="base" size="lg">
            Проверьте детали вашей записи!
          </Text>
        </div>
        <div className="flex w-full flex-col gap-12">
          <div className="flex w-full flex-col gap-4">
            <div className="flex items-center gap-4">
              <Calendar className="stroke-accent/80 size-10" />
              <div className="flex flex-col gap-1">
                <Text className="text-xl!">Вторник, 29 сентября</Text>
                <span className="text-brown/60 text-sm">18:00</span>
              </div>
            </div>
            <div className="bg-brown/10 h-[1px] w-full" />
          </div>
          <div className="flex w-full flex-col gap-4">
            <div className="flex items-center gap-4">
              <GraduationCap className="stroke-accent/80 size-10" />
              <div className="flex flex-col gap-1">
                <Text className="text-xl!">Психолог</Text>
                <span className="text-brown/60 text-sm">
                  Татьяна Стабровская
                </span>
              </div>
            </div>
            <div className="bg-brown/10 h-[1px] w-full" />
          </div>
        </div>
        <div className="mt-20 flex w-full justify-end md:mt-40">
          <Button
            onClick={() => navigate('/interview/pay')}
            variant="solid"
            className="w-full md:w-3xs"
          >
            Подтвердить
          </Button>
        </div>
      </div>
    </div>
  );
}
