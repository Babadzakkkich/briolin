import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { DateInput } from "@/components/ui/DateInput";
import { Text } from "@/components/ui/Text";
import { LoadPhoto } from "@/components/widgets/LoadPhoto";
import { useMutation } from "@tanstack/react-query";
import { createProfile } from "@/api/profile";
import { useState } from "react";
import type { GenderType } from "@/types/profile";

export function WelcomeProfile() {
  const navigate = useNavigate();

  const [firstName, setFirstName] = useState<string>("");
  const [lastName, setLastName] = useState<string>("");
  const [gender, setGender] = useState<GenderType>("male");
  const [birthDate, setBirthDate] = useState<string>("");
  const [city, setCity] = useState<string>("");

  const mutation = useMutation({
    mutationFn: () =>
      createProfile({
        basic: {
          first_name: firstName,
          last_name: lastName,
          gender,
          date_of_birth: birthDate,
          city,
        },
        detailed: {
          about_me: "",
          education: "",
          hobbies: "",
          partner_preferences: "",
        },
      }),
    onSuccess: () => {
      navigate("/welcome/test");
    },
  });

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-6 py-9 md:px-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Text size="md" variant="base">
            /профиль
          </Text>
        </div>
      </header>
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-12 pt-10 md:gap-20 md:pt-20">
        <div className="flex flex-col gap-2 pt-10 text-center md:pt-20">
          <Text variant="base" size="lg">
            Краткое заполнение профиля!
          </Text>
          <Text variant="base">
            Немного информации о себе — и мы сможем лучше понять тебя.
          </Text>
        </div>
        <div className="flex w-full flex-col items-center gap-8 md:flex-row md:justify-between md:gap-16">
          <div className="shrink-0">
            <LoadPhoto />
          </div>
          <div className="flex w-full grow flex-col gap-2">
            <Input
              placeholder="Имя"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <Input
              placeholder="Фамилия"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
            <Select
              value={gender}
              onChange={(e) => setGender(e.target.value as GenderType)}
              options={[
                { label: "Мужской", value: "male" },
                { label: "Женский", value: "female" },
              ]}
            />
            <DateInput
              placeholder="Дата рождения"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
            />
            <Input
              placeholder="Город"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
        </div>
        <Button
          variant="solid"
          onClick={() => mutation.mutate()}
          className="w-full md:w-3xs"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Загрузка..." : "Далее"}
        </Button>
      </div>
    </div>
  );
}
