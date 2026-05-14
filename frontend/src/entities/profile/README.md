# Entity: profile

Данные профиля текущего пользователя и других пользователей: базовая информация, расширенные данные, вопросы профиля, аватар.

## Состав

```
profile/
├── api/index.ts       # HTTP-методы для работы с profile-service
├── model/
│   ├── store.ts       # Zustand-стор (persisted, ключ 'profile')
│   └── types.ts       # Типы BasicProfileData, ProfileBasic, ProfileDetailed и др.
├── ui/
│   └── AvatarUpload.tsx  # Компонент загрузки аватара
└── index.ts
```

## Что хранит стор

Краткие данные текущего пользователя для быстрого отображения в UI (sidebar, шапка):

| Поле | Описание |
|---|---|
| `firstName`, `lastName` | Имя и фамилия |
| `city` | Город |
| `gender` | Пол |
| `dateOfBirth` | Дата рождения |
| `thumbnailUrl` | Миниатюра аватара |

## Использование

```ts
import { profileApi, useProfileStore } from '@/entities/profile';

// Загрузить профиль текущего пользователя
const { data } = await profileApi.getMe();
// → { basic: ProfileBasic, detailed: ProfileDetailed | null, questions: ProfileQuestions | null }

// Сохранить в стор для UI
useProfileStore.getState().setProfile(data.basic);

// Получить профиль другого пользователя
const { data } = await profileApi.getByKeycloakId('uuid-...');

// Обновить профиль
await profileApi.updateMe({
  basic: { city: 'Москва' },
  detailed: { about_me: 'Люблю кофе' },
});

// Вопросы профиля (нужны для получения лайков)
const { data: questions } = await profileApi.getMyQuestions();
await profileApi.createOrUpdateQuestions({ question_1: '...', ... });
```

## Типы профиля

- **BasicProfileData** — данные при создании (имя, пол, дата рождения, город)
- **ProfileBasic** — полный объект из базы (+ `id`, `keycloak_id`, `online`, `avatar_url`, `thumbnail_url`)
- **ProfileDetailed** — расширенная информация (о себе, образование, хобби, предпочтения, red_flags)
- **ProfileQuestions** — 5 текстовых ответов на вопросы (используются при лайках)
- **QuestionsStatus** — проверяет, заполнены ли все вопросы перед тем, как пользователь сможет получать лайки

## Примечания

- Профиль создаётся в два шага на онбординге: сначала `basic`, потом `detailed`.
- Вопросы профиля обязательны для получения входящих лайков (`can_receive_likes` из `QuestionsStatus`).
- Стор хранит только поля, нужные для UI; полные данные запрашиваются напрямую через `profileApi`.
