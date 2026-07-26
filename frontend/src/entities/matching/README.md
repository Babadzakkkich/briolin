# Entity: matching

Вся логика мэтчинга: поиск профилей, лайки с ответами на вопросы, матчи, входящие лайки, рекомендации.

## Состав

```
matching/
├── api/index.ts    # HTTP-методы для matching-service
├── model/
│   └── types.ts    # MatchingProfilePreview, LikeAnswers, Match, PendingLike и др.
└── index.ts
```

## API-методы

```ts
import { matchingApi } from '@/entities/matching';

// Классический поиск (по полу, возрасту, городу)
const { data } = await matchingApi.searchClassic({ gender: 'F', min_age: 20, max_age: 30 });

// Таргетированный поиск (+ образование, хобби, онлайн-фильтр)
const { data } = await matchingApi.searchTargeted({ hobbies_keywords: ['кино', 'спорт'] });

// Рекомендации на основе теста и предпочтений
const { data } = await matchingApi.getRecommendations({ page: 1, limit: 10 });
// → { profiles, pagination, lock_info, sentiment_boost_applied }

// Лайк с ответами на вопросы профиля
const { data } = await matchingApi.likeWithAnswers('target-uuid', {
  question_1: 'Ответ 1',
  question_2: 'Ответ 2',
  // ...
});
// → { status: 'liked' | 'matched', match_id, answers? }

// Ответный лайк (принять входящий лайк)
await matchingApi.reverseLike('from-uuid', myAnswers);

// Отклонить входящий лайк
await matchingApi.declineLike('from-uuid');

// Дизлайк
await matchingApi.dislike('target-uuid');

// Входящие лайки (ждут ответа)
const { data } = await matchingApi.getPendingLikes();

// Все матчи
const { data } = await matchingApi.getMatches();

// Ответы на вопросы в конкретном матче
const { data } = await matchingApi.getMatchAnswers(matchId);

// Лимит лайков на сегодня
const { data } = await matchingApi.getLikeUsage();
// → { likes_used_today, daily_like_limit, likes_remaining }
```

## Ключевые типы

- **MatchingProfilePreview** — карточка профиля в результатах поиска (с `similarity` и `combined_score`)
- **LikeAnswers** — 5 ответов на вопросы профиля, передаются при лайке
- **LikeWithAnswersResponse** — результат лайка: `'liked'` (ждём) или `'matched'` (матч!)
- **PendingLike** — входящий лайк с данными профиля отправителя и его ответами
- **MatchingLockInfo** — информация о лимите просмотров (`is_locked`, `locked_until`)

## Примечания

- Для отправки лайка нужно заполнить вопросы профиля (`entities/profile` → `createOrUpdateQuestions`).
- `serializeParams` в api/index.ts нужен для корректной передачи массивов (`hobbies_keywords[]`) в query-строку.
- `lock_info` показывает, достиг ли пользователь дневного лимита просмотров профилей.
