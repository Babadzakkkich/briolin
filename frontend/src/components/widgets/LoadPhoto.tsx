import { useRef } from "react";
import { Text } from "@/components/ui/Text";

export function LoadPhoto() {
    const inputRef = useRef<HTMLInputElement>(null);

    return (
        <div className="size-50 flex flex-col items-center justify-center gap-2 rounded-full border border-ash-blue bg-ash-blue/10">
            <Text variant="base" className="text-sm! text-brown/40">
                Загрузить свое фото
            </Text>
            <input ref={inputRef} type="file" className="hidden" />
            <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="bg-ash-blue cursor-pointer rounded-full px-6 py-1 text-sm text-white transition-opacity hover:opacity-90"
            >
                Выбрать
            </button>
        </div>
    );
}