import { useState } from "react";
import { Text } from "@/components/ui/Text";
import { ProfileTab } from "./tabs/ProfileTab";
import { MessagesTab } from "./tabs/MessagesTab";
import { ServicesTab } from "./tabs/ServicesTab";
import { ActivitiesTab } from "./tabs/ActivitiesTab";
import { SearchTab } from "./tabs/SearchTab";

type TabId = "profile" | "messages" | "services" | "activities" | "search";

interface TabDef {
    id: TabId;
    label: string;
}

const TABS: TabDef[] = [
    { id: "profile", label: "Профиль" },
    { id: "messages", label: "Сообщения" },
    { id: "services", label: "Услуги" },
    { id: "activities", label: "Активности" },
    { id: "search", label: "Поиск" },
];

export function DashboardPage() {
    const [activeTab, setActiveTab] = useState<TabId>("profile");

    return (
        <div className="mx-auto min-h-screen max-w-7xl px-6 py-6 md:px-10">
            <header className="mb-10 flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-2">
                    <Text size="md" variant="base" className="text-xl">
                        /бриолин
                    </Text>
                </div>

                <nav className="flex flex-wrap items-center gap-2 md:gap-6">
                    {TABS.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`font-involve cursor-pointer rounded-full px-4 py-2 text-base transition-colors ${activeTab === tab.id
                                    ? "bg-ash-blue text-white"
                                    : "text-brown hover:bg-ash-blue/10"
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </header>

            <main className="min-h-[70vh]">
                {activeTab === "profile" && <ProfileTab />}
                {activeTab === "messages" && <MessagesTab />}
                {activeTab === "services" && <ServicesTab />}
                {activeTab === "activities" && <ActivitiesTab />}
                {activeTab === "search" && <SearchTab />}
            </main>
        </div>
    );
}
