import { MoveLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Text } from "@/components/ui/Text";

export function LoginPage() {
	const navigate = useNavigate();

	return <div className="max-w-7xl mx-auto px-6 py-9 min-h-screen md:px-10">
		<header className="flex flex-col gap-4 justify-between md:flex-row md:items-center">
			<div className="flex gap-2 items-center">
				<Link className="flex items-center gap-2" to="/"><MoveLeft />Назад</Link>
			</div>
			<div className="items-center gap-4 md:gap-8 hidden md:flex">
				<Link to="/register">Регистрация</Link>
				<Link to="/reset-password">Забыли пароль?</Link>
			</div>
		</header>
		<div className="flex flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
			<div className="text-center pt-10 flex flex-col gap-6 md:pt-20 md:gap-8">
				<Text variant="heading" size="xl">Добро пожаловать!</Text>
				<Text variant="base" className="max-w-md mx-auto">Введи свои данные, открой дверь в мир романтики и новых знакомстов.</Text>
			</div>
			<div className="flex flex-col gap-4 w-full max-w-md px-4">
				<Input placeholder="Почта" />
				<Input type="password" placeholder="Пароль" />
			</div>
			<Button variant="solid" onClick={() => navigate('/welcome/profile')} className="w-full sm:w-3xs">Войти</Button>
		</div>
	</div>
}
