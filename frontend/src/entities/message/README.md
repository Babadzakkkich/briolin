# Entity: message

Модели данных сообщений и типов WebSocket-событий чата.

## Состав

```
message/
├── api/index.ts       # HTTP-методы для истории сообщений
├── model/
│   └── types.ts       # Message, WsMessage, WsEventType и др.
├── ui/
│   ├── MessageBubble.tsx   # Пузырёк сообщения
│   └── TypingIndicator.tsx # Индикатор набора текста
└── index.ts
```

## WebSocket-события (WsEventType)

| Тип события | Описание |
|---|---|
| `connection_established` | Соединение установлено |
| `message` | Новое входящее сообщение |
| `typing` | Пользователь печатает |
| `read_receipt` | Сообщение прочитано |
| `bulk_read_receipt` | Массовое прочтение |
| `message_updated` | Сообщение изменено |
| `message_deleted` | Сообщение удалено |
| `user_online` | Пользователь вышел онлайн |
| `user_offline` | Пользователь ушёл офлайн |
| `pong` | Ответ на ping (heartbeat) |
| `error` | Ошибка от сервера |

## Использование

```ts
import type { WsMessage, Message } from '@/entities/message';

// Обработка WS-события
function handleWsMessage(msg: WsMessage) {
  if (msg.type === 'message' && msg.message) {
    // добавить msg.message в список
  }
  if (msg.type === 'typing') {
    // msg.sender_id, msg.is_typing
  }
  if (msg.type === 'user_online') {
    // msg.user_id
  }
}
```

## Примечания

- `WsMessage` — унифицированный тип для всех событий; часть полей опциональна и зависит от `type`.
- Реальное управление WebSocket-соединением находится в `features/messaging/useChatSocket.ts`.
- HTTP-запросы истории сообщений идут через `entities/message/api`.
