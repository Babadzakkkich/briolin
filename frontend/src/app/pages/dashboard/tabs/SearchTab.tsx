import { useState } from "react";
import { Text } from "@/components/ui/Text";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Heart } from "lucide-react";

interface PeopleCard {
  id: string;
  name: string;
  age: number;
  city: string;
  image: string;
  match: number;
}

const PEOPLE: PeopleCard[] = [
  { id: "1", name: "Анна", age: 24, city: "Москва", image: "", match: 98 },
  {
    id: "2",
    name: "Елизавета",
    age: 27,
    city: "Санкт-Петербург",
    image: "",
    match: 95,
  },
  { id: "3", name: "Мария", age: 25, city: "Казань", image: "", match: 89 },
  { id: "4", name: "Екатерина", age: 26, city: "Сочи", image: "", match: 88 },
  { id: "5", name: "София", age: 23, city: "Москва", image: "", match: 85 },
  {
    id: "6",
    name: "Анастасия",
    age: 28,
    city: "Новосибирск",
    image: "",
    match: 81,
  },
];

export function SearchTab() {
  const [showFilters, setShowFilters] = useState(false);
  const [nameFilter, setNameFilter] = useState("");
  const [ageFrom, setAgeFrom] = useState("");
  const [ageTo, setAgeTo] = useState("");
  const [gender, setGender] = useState("");
  const [city, setCity] = useState("");

  const [purposes, setPurposes] = useState({
    communication: false,
    serious: false,
    travel: false,
  });

  const [onlineStatus, setOnlineStatus] = useState("all");

  const togglePurpose = (key: keyof typeof purposes) => {
    setPurposes((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="flex flex-col gap-8 pt-6 md:pt-10">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div className="flex flex-col gap-2 text-left">
          <Text variant="base" className="text-brown text-3xl md:text-4xl">
            Подходящие кандидаты
          </Text>
          <Text className="text-brown/70 mt-2">
            Мы подобрали людей, с которыми у вас может быть много общего.
          </Text>
        </div>
        <Button
          variant={showFilters ? "outline" : "solid"}
          className="px-4"
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? "Скрыть фильтры" : "Настроить фильтры"}
        </Button>
      </div>

      {showFilters && (
        <div className="border-ash-blue/20 bg-ash-blue/5 rounded-3xl border p-6 md:p-8">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Text className="text-brown text-sm font-medium">Имя</Text>
                <Input
                  placeholder="Искать по имени"
                  value={nameFilter}
                  onChange={(e) => setNameFilter(e.target.value)}
                  variant="solid"
                  className="bg-white/50"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Text className="text-brown text-sm font-medium">Город</Text>
                <Input
                  placeholder="Введите город"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  variant="solid"
                  className="bg-white/50"
                />
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Text className="text-brown text-sm font-medium">Пол</Text>
                <Select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  options={[
                    { label: "Любой", value: "" },
                    { label: "Мужской", value: "male" },
                    { label: "Женский", value: "female" },
                  ]}
                  className="rounded-full border-transparent bg-white/50 px-4 py-3"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Text className="text-brown text-sm font-medium">Возраст</Text>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="От"
                    type="number"
                    value={ageFrom}
                    onChange={(e) => setAgeFrom(e.target.value)}
                    variant="solid"
                    className="bg-white/50 text-center"
                  />
                  <Text className="text-brown/50">-</Text>
                  <Input
                    placeholder="До"
                    type="number"
                    value={ageTo}
                    onChange={(e) => setAgeTo(e.target.value)}
                    variant="solid"
                    className="bg-white/50 text-center"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-2">
                <Text className="text-brown mb-1 text-sm font-medium">
                  Цель знакомства
                </Text>
                <label className="group flex cursor-pointer items-center gap-3">
                  <div
                    className={`flex size-5 items-center justify-center rounded border transition-colors ${purposes.communication ? "bg-ash-blue border-ash-blue" : "border-brown/30 group-hover:border-brown/50 bg-white/50"}`}
                  >
                    {purposes.communication && (
                      <span className="text-xs text-white">✓</span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={purposes.communication}
                    onChange={() => togglePurpose("communication")}
                  />
                  <Text className="text-sm">Общение</Text>
                </label>
                <label className="group flex cursor-pointer items-center gap-3">
                  <div
                    className={`flex size-5 items-center justify-center rounded border transition-colors ${purposes.serious ? "bg-ash-blue border-ash-blue" : "border-brown/30 group-hover:border-brown/50 bg-white/50"}`}
                  >
                    {purposes.serious && (
                      <span className="text-xs text-white">✓</span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={purposes.serious}
                    onChange={() => togglePurpose("serious")}
                  />
                  <Text className="text-sm">Серьезные отношения</Text>
                </label>
                <label className="group flex cursor-pointer items-center gap-3">
                  <div
                    className={`flex size-5 items-center justify-center rounded border transition-colors ${purposes.travel ? "bg-ash-blue border-ash-blue" : "border-brown/30 group-hover:border-brown/50 bg-white/50"}`}
                  >
                    {purposes.travel && (
                      <span className="text-xs text-white">✓</span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={purposes.travel}
                    onChange={() => togglePurpose("travel")}
                  />
                  <Text className="text-sm">Путешествия</Text>
                </label>
              </div>

              <div className="border-brown/10 flex flex-col gap-2 border-t pt-2">
                <Text className="text-brown mb-1 text-sm font-medium">
                  Статус
                </Text>
                <div className="flex items-center gap-4">
                  <label className="group flex cursor-pointer items-center gap-2">
                    <div
                      className={`flex size-4 items-center justify-center rounded-full border transition-colors ${onlineStatus === "all" ? "border-ash-blue" : "border-brown/30 group-hover:border-brown/50"}`}
                    >
                      {onlineStatus === "all" && (
                        <div className="bg-ash-blue size-2 rounded-full" />
                      )}
                    </div>
                    <input
                      type="radio"
                      className="hidden"
                      name="status"
                      checked={onlineStatus === "all"}
                      onChange={() => setOnlineStatus("all")}
                    />
                    <Text className="text-sm">Все</Text>
                  </label>
                  <label className="group flex cursor-pointer items-center gap-2">
                    <div
                      className={`flex size-4 items-center justify-center rounded-full border transition-colors ${onlineStatus === "online" ? "border-ash-blue" : "border-brown/30 group-hover:border-brown/50"}`}
                    >
                      {onlineStatus === "online" && (
                        <div className="bg-ash-blue size-2 rounded-full" />
                      )}
                    </div>
                    <input
                      type="radio"
                      className="hidden"
                      name="status"
                      checked={onlineStatus === "online"}
                      onChange={() => setOnlineStatus("online")}
                    />
                    <Text className="text-sm">Только онлайн</Text>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-end gap-4">
            <Button
              variant="outline"
              className="text-brown hover:bg-brown/5 w-full border-transparent bg-transparent md:w-auto"
              onClick={() => {
                setNameFilter("");
                setAgeFrom("");
                setAgeTo("");
                setGender("");
                setCity("");
                setPurposes({
                  communication: false,
                  serious: false,
                  travel: false,
                });
                setOnlineStatus("all");
              }}
            >
              Сбросить
            </Button>
            <Button variant="solid" className="w-full px-8 md:w-auto">
              Применить фильтры
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {PEOPLE.map((person) => (
          <div
            key={person.id}
            className="group bg-ash-blue/5 hover:bg-ash-blue/10 relative flex flex-col overflow-hidden rounded-3xl transition-all"
          >
            <div className="bg-ash-blue/20 relative aspect-[4/5] w-full">
              <div className="absolute inset-0 flex items-center justify-center">
                <Text
                  variant="base"
                  className="text-ash-blue/40 font-comediant text-5xl opacity-20"
                >
                  Фото
                </Text>
              </div>
              <div className="absolute top-4 right-4 rounded-full bg-white/60 px-3 py-1 backdrop-blur-sm">
                <Text className="text-accent text-sm font-semibold">
                  {person.match}% совпадение
                </Text>
              </div>
            </div>

            <div className="flex flex-col gap-2 p-6">
              <div className="flex items-center justify-between">
                <Text variant="base" className="text-brown text-2xl">
                  {person.name}, {person.age}
                </Text>
              </div>
              <Text className="text-brown/60 text-sm">{person.city}</Text>

              <div className="mt-4 flex gap-2">
                <button className="bg-ash-blue hover:bg-ash-blue/90 flex-1 rounded-full py-2.5 text-center text-white transition-colors">
                  Написать
                </button>
                <button className="bg-brown/10 text-brown hover:bg-brown flex aspect-square items-center justify-center rounded-full p-2.5 transition-colors hover:text-white">
                  <Heart scale={0.7} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-center pb-12">
        <Button variant="solid" className="w-max px-8">
          Показать еще
        </Button>
      </div>
    </div>
  );
}
