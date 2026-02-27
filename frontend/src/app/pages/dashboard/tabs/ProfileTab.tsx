import { Text } from "@/components/ui/Text";
import { Button } from "@/components/ui/Button";

export function ProfileTab() {
    return (
        <div className="flex flex-col items-center gap-8 pt-8 md:pt-12">
            <div className="flex w-full max-w-2xl flex-col items-center gap-6 rounded-3xl bg-ash-blue/10 p-8 md:flex-row md:items-start md:gap-10 md:p-12">
                <div className="size-32 shrink-0 rounded-full border border-ash-blue bg-ash-blue/20 md:size-40" />
                <div className="flex w-full flex-col gap-4 text-center md:text-left">
                    <div className="flex flex-col gap-1">
                        <Text variant="base" className="text-3xl md:text-4xl">
                            Александр, 26
                        </Text>
                        <Text className="text-brown/70">Санкт-Петербург</Text>
                    </div>

                    <div className="h-[1px] w-full bg-brown/10" />

                    <div className="flex flex-col gap-2">
                        <Text className="font-medium">О себе</Text>
                        <Text className="text-brown/80 leading-relaxed max-w-md">
                            Люблю долгие прогулки по городу, хороший кофе и интересные разговоры. Ищу человека со схожими интересами для серьезных отношений.
                        </Text>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2 justify-center md:justify-start">
                        {["Фотография", "Спорт", "Путешествия"].map((tag) => (
                            <span key={tag} className="rounded-full border border-ash-blue/30 px-4 py-1.5 text-sm text-brown/80">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            <Button variant="solid" className="px-4">
                Редактировать профиль
            </Button>
        </div>
    );
}
