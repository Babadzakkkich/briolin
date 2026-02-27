import { Link } from "react-router-dom";

import { Logo } from "@/components/icons/Logo";
import { Text } from "@/components/ui/Text";

export function Home() {
  return (
    <>
      <div className="relative mx-auto flex min-h-screen flex-col overflow-clip px-6 pt-8 md:px-10">
        <div className="mx-auto flex w-full max-w-7xl flex-row px-4 md:gap-0 md:px-10">
          <header className="flex w-full items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="shrink-0">
                <Logo />
              </div>
              <Text className="text-brown hidden max-w-lg text-base md:block">
                Знакомства для тех, кто всё ещё верит в настоящие чувства и
                хочет встретить настоящую любовь.
              </Text>
            </div>
            <div className="flex gap-4 text-base md:gap-8">
              <Link to="/login">Вход</Link>
              <Link to="/register">Регистрация</Link>
            </div>
          </header>
        </div>

        <div className="font-comediant text-accent pointer-events-none flex flex-grow -translate-y-24 items-center justify-center text-[100px] leading-none select-none text-shadow-[0px_4px_0px_rgb(0_0_0)] sm:text-[120px] md:text-[160px] md:text-shadow-[0px_6px_0px_rgb(0_0_0)] lg:text-[220px] lg:text-shadow-[0px_8px_0px_rgb(0_0_0)]">
          Бриолин
        </div>
      </div>
    </>
  );
}
