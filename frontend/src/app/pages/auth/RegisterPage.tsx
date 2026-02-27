import { MoveLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Text } from "@/components/ui/Text";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useState } from "react";
import { register } from "@/api/auth";
import { useMutation } from "@tanstack/react-query";

export function RegisterPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const mutation = useMutation({
    mutationFn: () => register({ username, email, password, role: ["user"] }),
    onSuccess: () => {
      navigate("/login");
    },
    onError: (error: any) => {
      console.error("Ошибка регистрации:", error.detail);
    },
  });

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between gap-4">
        <Link className="flex items-center gap-2" to="/">
          <MoveLeft />
          Назад
        </Link>
        <div className="hidden items-center gap-4 sm:flex md:gap-8">
          <Link to="/login">Авторизация</Link>
          <Link to="/reset-password">Забыли пароль?</Link>
        </div>
      </header>
      <div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-6 pt-10 text-center md:gap-8 md:pt-20">
          <Text variant="heading" size="xl">
            Регистрация
          </Text>
          <Text variant="base" className="mx-auto max-w-md">
            Заполни полностью профиль, чтобы мы помогли тебе найти идеального
            партнера.
          </Text>
        </div>
        <div className="flex w-full max-w-md flex-col gap-4 px-4">
          <Input
            placeholder="Почта"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            placeholder="Логин"
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
          className="w-full md:w-3xs"
        >
          Далее
        </Button>
      </div>
    </div>
  );
}
