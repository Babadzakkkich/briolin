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
│   ├── ChatAvatar.tsx       # Аватар чата (с онлайн-индикатором)
│   ├── ChatItem.tsx         # Строка чата в списке
│   └── ChatActionsMenu.tsx  # Мини-меню "..." (удалить чат / отметить прочитанным)
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

// Список онлайн-пользователей (id + count) — единственный источник статуса "онлайн"
const { online_users, count } = await chatApi.getOnlineUsers();

// Поиск по тексту сообщений (по всем чатам или конкретному)
const { messages, total } = await chatApi.searchMessages({ query: 'привет' });

// Удалить чат — хард-делит для обоих участников direct-чата
await chatApi.deleteChat(chat.id);

// Ответы на вопросы, если чат создан из мэтча (chat.match_id != null)
const answers = await chatApi.getMatchAnswers(chat.id);
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
  match_id: number | null;
  // ...
}
```

## Примечания

- WebSocket **не шлёт** `user_online`/`user_offline` клиенту (это внутренние RabbitMQ-события между сервисами) — статус "онлайн" получаем только через REST `chatApi.getOnlineUsers()`, см. поллинг в `features/messaging/model/useMessaging.ts`.
- `ChatItem` используется в `features/messaging/ui/ChatList.tsx`.
