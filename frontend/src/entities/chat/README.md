# Entity: chat

Доменная сущность чата: модели данных, API-методы и базовые UI-компоненты для отображения чатов.

## Состав

```
chat/
├── api/index.ts       # HTTP-методы для chat-service
├── model/
│   ├── types.ts       # Chat, ChatParticipant, ChatListResponse
│   └── helpers.ts     # Утилиты для работы с чатами
├── ui/
│   ├── ChatAvatar.tsx # Аватар чата (с онлайн-индикатором)
│   └── ChatItem.tsx   # Строка чата в списке
└── index.ts
```

## Использование

```ts
import { chatApi } from '@/entities/chat';

// Список чатов текущего пользователя
const chats = await chatApi.getChats({ limit: 20 });
// → { chats: Chat[], total: number, page: number, size: number }

// Создать личный чат с пользователем
const chat = await chatApi.createDirectChat('keycloak-uuid');

// Проверить онлайн-статус пользователя
const { online } = await chatApi.getOnlineStatus('keycloak-uuid');
```

## Тип Chat

```ts
interface Chat {
  id: string;
  type: 'DIRECT' | 'GROUP';
  status: 'ACTIVE' | 'ARCHIVED' | 'BLOCKED';
  participants: ChatParticipant[];
  last_message?: Message;
  unread_count: number;
  // ...
}
```

## Примечания

- Онлайн-статус можно получить через REST, но в реальном времени он приходит через WebSocket (`user_online` / `user_offline` события) — см. `entities/message` и `features/messaging/useChatSocket`.
- `ChatItem` используется в `features/messaging/ui/ChatList.tsx`.
