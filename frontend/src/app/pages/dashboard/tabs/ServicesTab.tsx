import { Button } from "@/components/ui/Button";
import { Text } from "@/components/ui/Text";

export function ServicesTab() {
  return (
    <div className="flex flex-col gap-16 pt-8">
      <div className="flex flex-col gap-2 text-center md:text-left">
        <Text variant="base" className="text-3xl md:text-4xl">
          История консультаций
        </Text>
        <Text className="text-brown/70 mt-2">
          В этом разделе вы сможете просмотреть результаты первичного
          тестирования и ознакомиться с рекомендациями психолога,
          подготовленными специально для вас, чтобы помочь в построении
          гармоничных знакомств и отношений.
        </Text>
      </div>

      <div className="grid grid-cols-1 gap-16 md:grid-cols-2">
        <div className="bg-accent/50 flex flex-col gap-24 rounded-lg p-7">
          <Text variant="base" className="text-2xl text-white">
            Результаты вашего первичного тестирования
          </Text>
          <Button variant="solid" className="w-full">
            Подробнее о результатах
          </Button>
        </div>
        <div className="bg-accent/50 flex flex-col gap-24 rounded-lg p-7">
          <Text variant="base" className="text-2xl text-white">
            Индивидуальные рекомендации психолога
          </Text>
          <Button variant="solid" className="w-full">
            Подробнее о результатах
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-2 text-center md:text-left">
        <Text variant="base" className="text-3xl md:text-4xl">
          Консультация с психологом
        </Text>
        <Text className="text-brown/70 mt-2">
          Запишитесь на удобное время и получите профессиональную консультацию
          по интересующим вас вопросам.
        </Text>
      </div>
    </div>
  );
}
