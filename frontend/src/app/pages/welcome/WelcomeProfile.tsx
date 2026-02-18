import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Text } from "@/components/ui/Text";
import { LoadPhoto } from "@/components/widgets/LoadPhoto";

export function WelcomeProfile() {
	const navigate = useNavigate();

	return <div className="max-w-7xl mx-auto px-6 py-9 min-h-screen md:px-10">
		<header className="flex items-center justify-between">
			<div className="flex gap-2 items-center">
				<Text size="md" variant="base">/профиль</Text>
			</div>
		</header>
		<div className="flex flex-col items-center gap-12 pt-10 max-w-3xl mx-auto md:gap-20 md:pt-20">
			<div className="text-center pt-10 flex flex-col gap-2 md:pt-20">
				<Text variant="base" size="lg">Краткое заполнение профиля!</Text>
				<Text variant="base">
					Немного информации о себе — и мы сможем лучше понять тебя.
				</Text>
			</div>
			<div className="flex flex-col items-center gap-8 w-full md:flex-row md:justify-between md:gap-16">
				<div className="shrink-0">
					<LoadPhoto />
				</div>
				<div className="flex flex-col gap-2 w-full grow">
					<Input placeholder="Фамилия Имя" />
					<Input placeholder="Пол" />
					<Input placeholder="Возраст" />
					<Input placeholder="Город" />
				</div>
			</div>
			<Button variant="solid" onClick={() => navigate('/welcome/test')} className="w-full md:w-3xs">Далее</Button>
		</div>
	</div>
}
