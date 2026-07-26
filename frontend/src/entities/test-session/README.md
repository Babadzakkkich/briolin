# Entity: test-session

Психологический тест — обязательный этап онбординга. Результат теста определяет доступ к основным функциям платформы.

## Состав

```
test-session/
├── api/index.ts    # HTTP-методы для testing-service
├── model/
│   └── types.ts    # Question, TestStartResponse, TestResults и др.
└── index.ts
```

## Флоу прохождения теста

```
1. POST /test-sessions/start
   → session_id, список вопросов

2. Для каждого вопроса:
   POST /test-sessions/{session_id}/answer
   → { answer_saved, total_answered, total_questions }

3. POST /test-sessions/{session_id}/complete
   → { results: { passed, percentage, total_score } }

4. passed === true → useAuthStore.setTestPassed(true) → /dashboard
   passed === false → показать результат, предложить пересдать
```

## Использование

```ts
import { testSessionApi } from '@/entities/test-session';

// Начать тест
const { data } = await testSessionApi.startTest();
// → { session_id, questions: Question[], time_limit_minutes }

// Ответить на вопрос
await testSessionApi.submitAnswer(session_id, {
  question_id: 'q1',
  answer_id: 'a2',
});

// Завершить тест
const { data } = await testSessionApi.completeTest(session_id);
// → { results: { passed: true, percentage: 78 } }

// История прохождений (используется для проверки при логине)
const { data } = await testSessionApi.getHistory();
const hasPassed = data.history.some((item) => item.passed);
```

## Типы вопросов

| question_type | Описание |
|---|---|
| `multiple_choice` | Выбор одного из вариантов |
| `likert_scale` | Шкала согласия (мин/макс с labels) |
| `true_false` | Да / Нет |

## Примечания

- Флаг `isTestPassed` хранится в `entities/session/model/store.ts` (стор авторизации).
- `TestGuard` (`features/auth/TestGuard.tsx`) проверяет этот флаг и блокирует доступ к дашборду до прохождения теста.
- Тест можно пересдавать — в истории хранятся все попытки.
