# Entity: session

Управляет состоянием аутентификации пользователя: access-токен, данные из JWT и флаг прохождения теста.

## Состав

```
session/
├── api/index.ts       # HTTP-методы: login, register, refresh, logout
├── model/
│   ├── store.ts       # Zustand-стор (persisted в localStorage под ключом 'auth')
│   └── types.ts       # Типы запросов/ответов и JWT-payload
└── index.ts           # Публичный API сущности
```

## Что хранит стор

| Поле | Тип | Описание |
|---|---|---|
| `accessToken` | `string \| null` | JWT access token (хранится в памяти + localStorage) |
| `username` | `string \| null` | Имя пользователя из JWT (`preferred_username`) |
| `keycloakId` | `string \| null` | UUID пользователя из JWT (`sub`) |
| `isAuthenticated` | `boolean` | `true`, если accessToken не null |
| `isTestPassed` | `boolean` | `true`, если пользователь прошёл психологический тест |

## Использование

```ts
// Чтение состояния
const { accessToken, isAuthenticated, username } = useAuthStore();
const isTestPassed = useAuthStore((s) => s.isTestPassed);

// Сохранение токена (автоматически парсит JWT и заполняет username/keycloakId)
useAuthStore.getState().setAccessToken(data.access_token);

// Сброс при logout
useAuthStore.getState().clear();
```

```ts
// API-вызовы
import { sessionApi } from '@/entities/session';

await sessionApi.login({ username: 'ivan', password: 'secret' });
await sessionApi.refresh();   // читает refresh token из HTTP-only cookie
await sessionApi.logout();
```

## Примечания

- Access token **персистируется в localStorage** через Zustand `persist`. При перезагрузке страницы токен берётся из хранилища; `AuthGuard` дополнительно рефрешит его на случай истечения.
- Refresh token — HTTP-only cookie, фронтенд его не видит.
- При вызове `setAccessToken` JWT автоматически декодируется (base64 → JSON), чтобы извлечь `sub` и `preferred_username`.
