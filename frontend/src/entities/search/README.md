# Entity: search

Поиск профилей пользователей через search-service (полнотекстовый + фильтры).

## Состав

```
search/
├── api/index.ts       # HTTP-методы для search-service
├── model/
│   └── types.ts       # ProfilePreview, SearchRequest, SearchResponse и др.
├── ui/
│   ├── ProfileCard.tsx    # Карточка профиля в результатах поиска
│   ├── LockBanner.tsx     # Баннер при достижении лимита просмотров
│   └── SearchSkeleton.tsx # Скелетон загрузки
└── index.ts
```

## Использование

```ts
import { searchApi } from '@/entities/search';

// Классический поиск
const { data } = await searchApi.searchClassic({
  gender: 'M',
  min_age: 25,
  max_age: 35,
  city: 'Москва',
  page: 1,
  limit: 10,
});

// Таргетированный поиск
const { data } = await searchApi.searchTargeted({
  hobbies_keywords: ['музыка'],
  online_only: true,
});
```

## Тип ответа

```ts
interface SearchResponse {
  profiles: ProfilePreview[];
  pagination: SearchPagination;
  lock_info?: SearchLockInfo;     // есть, если достигнут лимит просмотров
  sentiment_boost_applied?: boolean;
}
```

## Отличие от matching

- `entities/search` обращается к **search-service** (Elasticsearch / full-text).
- `entities/matching` обращается к **matching-service** (алгоритм совместимости + рекомендации).
- В UI страницы используют оба API — например, `ClassicSearchPage` может использовать либо один, либо другой.

## Примечания

- `LockBanner` отображается, когда `lock_info.is_locked === true`.
- `ProfileCard` показывает аватар, возраст, город, онлайн-статус и краткую информацию.
