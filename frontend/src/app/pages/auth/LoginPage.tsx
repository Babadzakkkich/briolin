import { MoveLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Text } from "@/components/ui/Text";
import { useMutation } from "@tanstack/react-query";
import { login } from "@/api/auth";

export function LoginPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const mutation = useMutation({
    mutationFn: () => login({ username, password }),
    onSuccess: () => {
      navigate("/registration-complete");
    },
    onError: (error: any) => {
      console.error(`Ошибка входа: ${error.detail}`);
    },
  });

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div className="flex items-center gap-2">
          <Link className="flex items-center gap-2" to="/">
            <MoveLeft />
            Назад
          </Link>
        </div>
        <div className="hidden items-center gap-4 md:flex md:gap-8">
          <Link to="/register">Регистрация</Link>
          <Link to="/reset-password">Забыли пароль?</Link>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-6 pt-10 text-center md:gap-8 md:pt-20">
          <Text variant="heading" size="xl">
            Добро пожаловать!
          </Text>
          <Text variant="base" className="mx-auto max-w-md">
            Введи свои данные, открой дверь в мир романтики и новых знакомстов.
          </Text>
        </div>
        <div className="flex w-full max-w-md flex-col gap-4 px-4">
          <Input
            placeholder="Логин/Почта"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button
          variant="solid"
          onClick={() => mutation.mutate()}
          className="w-full sm:w-3xs"
        >
          Войти
        </Button>
      </div>
    </div>
  );
}
