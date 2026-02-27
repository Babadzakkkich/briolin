import { Text } from "@/components/ui/Text";

export function ActivitiesTab() {
  return (
    <div className="flex h-[50vh] flex-col items-center justify-center gap-4 text-center">
      <div className="bg-ash-blue/20 mb-4 flex size-20 items-center justify-center rounded-full">
        <div className="bg-ash-blue/50 size-8 rounded-full" />
      </div>
      <Text variant="base" className="text-3xl!">
        Пока пусто
      </Text>
      <Text className="text-brown/70 max-w-md">
        Здесь будут отображаться ваши активности, лайки профиля и приглашения на
        встречи.
      </Text>
    </div>
  );
}
