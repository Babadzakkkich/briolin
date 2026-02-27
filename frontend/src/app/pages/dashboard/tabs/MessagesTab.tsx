import { useState } from "react";
import { Text } from "@/components/ui/Text";
import { Input } from "@/components/ui/Input";

interface ChatPreview {
  id: string;
  name: string;
  lastMessage: string;
  time: string;
  unread: number;
  active: boolean;
}

interface Message {
  id: string;
  text: string;
  time: string;
  isMine: boolean;
}

const CHATS: ChatPreview[] = [
  { id: "1", name: "Анна", lastMessage: "Давай встретимся завтра вечером?", time: "14:20", unread: 2, active: true },
  { id: "2", name: "Елизавета", lastMessage: "Спасибо за приятный вечер!", time: "Вчера", unread: 0, active: false },
  { id: "3", name: "Мария", lastMessage: "Хаха, это очень смешно 😂", time: "Вчера", unread: 0, active: false },
  { id: "4", name: "Екатерина", lastMessage: "Я тоже люблю этот фильм", time: "Пн", unread: 0, active: false },
  { id: "5", name: "Служба поддержки", lastMessage: "Добро пожаловать в Бриолин!", time: "23 мая", unread: 0, active: false },
];

const MESSAGES: Message[] = [
  { id: "m1", text: "Привет! Как прошел твой день?", time: "18:00", isMine: true },
  { id: "m2", text: "Привет! Отлично, только закончила работу. А твой?", time: "18:05", isMine: false },
  { id: "m3", text: "Тоже хорошо. Был на встрече с друзьями.", time: "18:10", isMine: true },
  { id: "m4", text: "Здорово! Кстати, мы обсуждали тот новый ресторан в центре...", time: "18:12", isMine: false },
  { id: "m5", text: "Я как раз хотел предложить туда сходить!", time: "18:15", isMine: true },
  { id: "m6", text: "Правда? Отличная идея!", time: "18:16", isMine: false },
  { id: "m7", text: "Давай встретимся завтра вечером?", time: "14:20", isMine: false }, // Today
];

export function MessagesTab() {
  const [activeChat, setActiveChat] = useState<string>("1");
  const [messageText, setMessageText] = useState("");

  const currentChat = CHATS.find((c) => c.id === activeChat);

  return (
    <div className="flex h-[calc(100vh-200px)] min-h-[600px] w-full flex-col overflow-hidden rounded-3xl border border-ash-blue/20 bg-white/50 md:flex-row mt-6">

      <div className="flex h-1/3 w-full flex-col border-b border-ash-blue/20 bg-beige/30 md:h-full md:w-80 md:border-b-0 md:border-r lg:w-96 shrink-0">
        <div className="p-4 border-b border-ash-blue/20">
          <Input
            placeholder="Поиск диалогов..."
            className="rounded-full bg-white/50 px-4 py-2 text-sm backdrop-blur-sm border-none placeholder:text-brown/40"
            variant="solid"
          />
        </div>

        <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 hide-scrollbar">
          {CHATS.map((chat) => (
            <button
              key={chat.id}
              onClick={() => setActiveChat(chat.id)}
              className={`flex w-full cursor-pointer items-center gap-4 rounded-2xl p-3 text-left transition-colors ${activeChat === chat.id
                ? "bg-ash-blue text-white"
                : "hover:bg-ash-blue/10 text-brown"
                }`}
            >
              <div className="relative size-12 shrink-0 rounded-full bg-ash-blue/20 border border-ash-blue/30">
                {chat.active && (
                  <div className="absolute bottom-0 right-0 size-3 rounded-full border-2 border-beige bg-accent"></div>
                )}
              </div>
              <div className="flex flex-1 flex-col overflow-hidden">
                <div className="flex items-center justify-between">
                  <Text className={`font-medium truncate ${activeChat === chat.id ? 'text-white' : 'text-brown'}`}>
                    {chat.name}
                  </Text>
                  <span className={`text-xs ml-2 shrink-0 ${activeChat === chat.id ? 'text-white/70' : 'text-brown/50'}`}>
                    {chat.time}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <Text className={`truncate text-sm ${activeChat === chat.id ? 'text-white/80' : 'text-brown/60'}`}>
                    {chat.lastMessage}
                  </Text>
                  {chat.unread > 0 && (
                    <span className="ml-2 flex size-5 shrink-0 items-center justify-center rounded-full bg-brown text-[10px] font-bold text-white">
                      {chat.unread}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {currentChat ? (
        <div className="flex h-2/3 flex-1 flex-col md:h-full bg-white/30 backdrop-blur-sm relative">
          <div className="flex items-center justify-between border-b border-ash-blue/20 p-4 shrink-0 bg-white/50">
            <div className="flex items-center gap-4">
              <div className="size-10 rounded-full bg-ash-blue/20"></div>
              <div className="flex flex-col">
                <Text className="font-medium">{currentChat.name}</Text>
                <Text className="text-xs text-brown/50">В сети</Text>
              </div>
            </div>
            <button className="text-xl text-brown/50 hover:text-brown transition-colors px-2">
              ⋮
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 md:p-6 flex flex-col gap-4">
            <div className="text-center my-4">
              <span className="text-xs font-medium text-brown/40 bg-brown/5 px-3 py-1 rounded-full">
                Сегодня
              </span>
            </div>

            {MESSAGES.map((msg) => (
              <div
                key={msg.id}
                className={`flex max-w-[80%] flex-col gap-1 md:max-w-[70%] ${msg.isMine ? "self-end" : "self-start"
                  }`}
              >
                <div
                  className={`rounded-2xl px-4 py-2.5 ${msg.isMine
                    ? "rounded-tr-sm bg-ash-blue text-white shadow-sm"
                    : "rounded-tl-sm bg-brown text-beige shadow-sm"
                    }`}
                >
                  <Text className={`text-[15px] ${msg.isMine ? 'text-white' : 'text-beige!'}`}>
                    {msg.text}
                  </Text>
                </div>
                <span
                  className={`text-[11px] text-brown/40 ${msg.isMine ? "text-right pr-1" : "text-left pl-1"
                    }`}
                >
                  {msg.time} {msg.isMine && "✓✓"}
                </span>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-ash-blue/20 bg-white/50 shrink-0">
            <div className="flex items-end gap-2 bg-ash-blue/10 rounded-3xl p-1 pr-2">
              <button className="flex size-10 items-center justify-center text-brown/50 hover:text-brown transition-colors shrink-0">
                +
              </button>
              <textarea
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                placeholder="Сообщение..."
                className="max-h-32 min-h-10 w-full resize-none bg-transparent py-2.5 outline-none font-involve placeholder:text-brown/40 text-[15px]"
                rows={1}
              />
              <button
                className="flex size-10 items-center justify-center bg-ash-blue text-white rounded-full transition-transform hover:scale-105 active:scale-95 shrink-0"
                disabled={!messageText.trim()}
              >
                ➤
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center">
          <Text className="text-brown/40">Выберите чат для общения</Text>
        </div>
      )}
    </div>
  );
}
