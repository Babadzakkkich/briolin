# Entity: media

Загрузка медиафайлов (аватар пользователя) в media-service.

## Состав

```
media/
├── api/index.ts    # HTTP-методы для media-service
└── index.ts
```

## Использование

```ts
import { mediaApi } from '@/entities/media';

// Загрузить аватар
const formData = new FormData();
formData.append('file', file);
const { data } = await mediaApi.uploadAvatar(formData);
// → { avatar_url: string, thumbnail_url: string }

// После загрузки обновить стор профиля
useProfileStore.getState().setThumbnailUrl(data.thumbnail_url);
```

## Примечания

- UI для загрузки — `entities/profile/ui/AvatarUpload.tsx`.
- После успешной загрузки сервер возвращает два URL: оригинал (`avatar_url`) и миниатюру (`thumbnail_url`). Миниатюра кэшируется в `profileStore` для быстрого отображения в сайдбаре.
