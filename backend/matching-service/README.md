# Matching Service

Сервис знакомств и рекомендаций в системе Briolin. Обрабатывает лайки, дизлайки, создание матчей, поиск профилей и рекомендации на основе эмбеддингов.

## Описание сервиса

**Основные функции:**
- Лайки и дизлайки профилей (с поддержкой ответов на вопросы)
- Создание матчей при взаимной симпатии
- Входящие лайки с ответами на вопросы
- Классический поиск профилей (фильтры: пол, возраст, город)
- Таргетированный поиск (с расширенными фильтрами)
- Рекомендации на основе эмбеддингов (семантический поиск)
- Тональный ре-ранкинг на основе sentiment-эмбеддингов
- Дневные лимиты на лайки и просмотры
- Блокировка при превышении лимита просмотров
- Red Flags фильтрация

**Технологии:**
- FastAPI
- PostgreSQL + pgvector (эмбеддинги)
- Redis (кэширование)
- Sentence Transformers (генерация эмбеддингов)
- RabbitMQ (межсервисное взаимодействие)

## API Endpoints

### Лайки и дизлайки (`/api/v1/matching`)

 POST  `/matching/like`  DEPRECATED: Обычный лайк
 POST  `/matching/like-with-answers`  Лайк с ответами на вопросы
 POST  `/matching/dislike`  Дизлайк профиля
 POST  `/matching/reverse-like`  Ответный лайк на входящий
 POST  `/matching/decline-like`  Отклонить входящий лайк
 GET  `/matching/pending-likes`  Входящие лайки с ответами
 GET  `/matching/like-usage`  Статистика использования лайков

#### Примеры запросов

**Лайк с ответами на вопросы:**
POST /api/v1/matching/like-with-answers
Authorization: Bearer <access_token>
Content-Type: application/json
{
  "target_user_id": "550e8400-e29b-41d4-a716-446655440001",
  "answers": {
    "question_1": "Активный отдых и путешествия",
    "question_2": "Да, я всегда иду на компромисс",
    "question_3": "Постоянно общаюсь с новыми людьми",
    "question_4": "Доверие и честность",
    "question_5": "Обсуждаем спокойно и ищем решение"
  }
}
Ответ (лайк отправлен):
json
{
  "status": "liked",
  "message": "Лайк с ответами отправлен. Ожидайте ответа.",
  "match_id": null,
  "show_answers": false
}
Ответ (взаимный матч):
json
{
  "status": "matched",
  "message": "Взаимный лайк! Матч создан.",
  "match_id": 42,
  "show_answers": true,
  "answers": {
    "my_answers": {
      "question_1": "Активный отдых и путешествия",
      "question_2": "Да, я всегда иду на компромисс"
    },
    "my_questions": {
      "question_1": "Как вы проводите свободное время?",
      "question_2": "Готовы ли вы к компромиссам?"
    },
    "partner_answers": {
      "question_1": "Чтение книг и прогулки",
      "question_2": "В большинстве случаев да"
    },
    "partner_questions": {
      "question_1": "Как вы обычно проводите свободное время?",
      "question_2": "Готовы ли вы к компромиссам в отношениях?"
    }
  }
}

Входящие лайки:
GET /api/v1/matching/pending-likes?page=1&limit=20
Authorization: Bearer <access_token>
Ответ:
json
[
  {
    "from_user_id": "550e8400-e29b-41d4-a716-446655440001",
    "from_user_display_name": "Jane Smith",
    "from_user_age": 28,
    "from_user_city": "Moscow",
    "from_user_avatar": "/media/avatar/550e8400.../thumbnail?avatar_id=...",
    "from_user_about_me": "Люблю путешествия и хорошую музыку",
    "from_user_hobbies": "Путешествия, музыка, спорт",
    "from_user_red_flags": ["Курение", "Лень"],
    "from_user_partner_preferences": "Активный, целеустремлённый",
    "answers": {
      "question_1": "Активный отдых",
      "question_2": "Да, ищу компромисс"
    },
    "questions": {
      "question_1": "Как вы проводите свободное время?",
      "question_2": "Готовы ли вы к компромиссам?"
    },
    "created_at": "2026-01-15T10:40:00"
  }
]

Матчи (/api/v1/matching)
Метод	Эндпоинт	Описание
GET	/matching/matches	Список матчей пользователя
GET	/matching/matches/{match_id}/answers	Матч с ответами на вопросы
Примеры запросов
Список матчей:
GET /api/v1/matching/matches?page=1&limit=20
Authorization: Bearer <access_token>
Ответ:
json
[
  {
    "match_id": 42,
    "partner": {
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "Jane Smith",
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=..."
    },
    "matched_at": "2026-01-15T10:45:00"
  }
]

Матч с ответами:
GET /api/v1/matching/matches/42/answers
Authorization: Bearer <access_token>
Ответ:
json
{
  "match_id": 42,
  "partner": {
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",
    "display_name": "Jane Smith",
    "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=..."
  },
  "matched_at": "2026-01-15T10:45:00",
  "my_answers": {
    "question_1": "Активный отдых и путешествия",
    "question_2": "Да, я всегда иду на компромисс"
  },
  "my_questions": {
    "question_1": "Как вы проводите свободное время?",
    "question_2": "Готовы ли вы к компромиссам?"
  },
  "partner_answers": {
    "question_1": "Чтение книг и прогулки",
    "question_2": "В большинстве случаев да"
  },
  "partner_questions": {
    "question_1": "Как вы обычно проводите свободное время?",
    "question_2": "Готовы ли вы к компромиссам в отношениях?"
  }
}

Поиск (/api/v1/matching)
GET	/matching/search/classic	Классический поиск (базовые фильтры)
GET	/matching/search/targeted	Таргетированный поиск (расширенные фильтры)
Примеры запросов
Классический поиск:
GET /api/v1/matching/search/classic?gender=female&min_age=25&max_age=35&city=Moscow&page=1&limit=10
Authorization: Bearer <access_token>
Ответ:
json
{
  "profiles": [
    {
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "Jane Smith",
      "age": 28,
      "city": "Moscow",
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=...",
      "education": "Высшее",
      "hobbies": "Путешествия, музыка, спорт"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_results": 47,
    "page_size": 10
  }
}

Таргетированный поиск:
GET /api/v1/matching/search/targeted?gender=female&min_age=25&max_age=35&city=Moscow&education=Высшее&hobbies_keywords=путешествия,спорт&online_only=true&page=1&limit=10
Authorization: Bearer <access_token>

Рекомендации (/api/v1/matching)
GET	/matching/recommendations/targeted	Таргетированные рекомендации (эмбеддинги)
GET	/matching/lock-status	Статус блокировки рекомендаций
GET	/matching/swipe/status/{user_id}	Статус свайпа к пользователю
Примеры запросов
Таргетированные рекомендации:
GET /api/v1/matching/recommendations/targeted?page=1&limit=10&city=Moscow
Authorization: Bearer <access_token>
Ответ:
json
{
  "profiles": [
    {
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "Jane Smith",
      "age": 28,
      "city": "Moscow",
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=...",
      "about_me": "Люблю путешествия и хорошую музыку",
      "hobbies": "Путешествия, музыка, спорт",
      "red_flags": ["Курение"],
      "partner_preferences": "Активный, целеустремлённый",
      "similarity": 0.8765,
      "combined_score": 0.8542
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_results": 10,
    "page_size": 10
  },
  "lock_info": {
    "is_locked": false,
    "profiles_viewed": 12,
    "daily_limit": 100,
    "locked_until": null,
    "time_until_unlock": null
  },
  "applied_filters": {
    "gender": "female",
    "city": "Moscow",
    "min_age": 23,
    "max_age": 33,
    "age_range": 5,
    "user_age": 28,
    "user_gender": "male",
    "user_city": "Moscow",
    "red_flag_filtered": 3,
    "user_red_flags": ["Курение", "Лень"],
    "sentiment_boost_applied": true
  },
  "sentiment_boost_applied": true
}
Блокировка (ошибка 429):
json
{
  "detail": {
    "message": "Таргетированные рекомендации заблокированы. Просмотрено 100/100 профилей. Разблокировка через 10 минут",
    "unlock_time": "2026-01-15T14:30:00",
    "time_until_unlock": 600,
    "profiles_viewed": 100,
    "daily_limit": 100
  }
}
Статус свайпа:
GET /api/v1/matching/swipe/status/550e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <access_token>
Ответ:
json
{
  "swiped": true,
  "type": "like"
}
Admin (/api/v1/matching)
DELETE	/matching/admin/reset/{user_id}	Сброс данных пользователя (лайки, свайпы, блокировки)

Переменные окружения
Matching Service Config
MATCHING__DEBUG	Режим отладки	false
MATCHING__SERVICE_NAME	Имя сервиса	matching-service
MATCHING__HOST	Хост для запуска	0.0.0.0
MATCHING__PORT	Порт для запуска	8006

Database Config
MATCHING__DB__USER	Пользователь PostgreSQL	matching_user
MATCHING__DB__PASSWORD	Пароль PostgreSQL	matching_password
MATCHING__DB__HOST	Хост PostgreSQL	matching-postgres
MATCHING__DB__PORT	Порт PostgreSQL	5432
MATCHING__DB__NAME	Название БД	matching_db
MATCHING__DB__ECHO	Логирование SQL	false
MATCHING__DB__POOL_SIZE	Размер пула соединений	20
MATCHING__DB__MAX_OVERFLOW	Макс. переполнение пула	10

Redis Config
MATCHING__REDIS__URL	URL Redis	redis://redis:6379/2

Limits Config
MATCHING__TARGETED_DAILY_VIEW_LIMIT	Дневной лимит просмотров (эмбеддинги)	100
MATCHING__TARGETED_LOCK_HOURS	Время блокировки (часы)	12
MATCHING__DAILY_LIKE_LIMIT	Дневной лимит лайков	10

External Services
MATCHING__PROFILE_SERVICE_URL	URL profile-service	http://profile-service:8003
MATCHING__CHAT_SERVICE_URL	URL chat-service	http://chat-service:8005

Shared Config
KEYCLOAK__SERVER_URL	URL Keycloak сервера	http://keycloak:8080
KEYCLOAK__REALM	Realm в Keycloak	briolin
RABBITMQ__HOST	Хост RabbitMQ	rabbitmq
RABBITMQ__PORT	Порт RabbitMQ	5672
RABBITMQ__USER	Пользователь RabbitMQ	guest
RABBITMQ__PASSWORD	Пароль RabbitMQ	guest
RABBITMQ__VHOST	VHost RabbitMQ	/

Структура проекта
matching-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── matching.py           # Основные эндпоинты
│   │       └── internal.py           # Внутренние эндпоинты
│   ├── core/
│   │   ├── config.py                 # Конфигурация сервиса
│   │   ├── logger.py                 # Настройка логирования
│   │   ├── exceptions.py             # Кастомные исключения
│   │   └── exception_handlers.py     # Обработчики исключений
│   ├── database/
│   │   ├── models.py                 # Модели PostgreSQL
│   │   └── session.py                # Настройка сессии БД
│   ├── schemas/
│   │   ├── swipe.py                  # Схемы лайков/дизлайков
│   │   ├── match.py                  # Схемы матчей
│   │   ├── search.py                 # Схемы поиска
│   │   ├── recommendation.py         # Схемы рекомендаций
│   │   ├── like_with_answers.py      # Схемы лайков с ответами
│   │   ├── lock.py                   # Схемы блокировки
│   │   └── pagination.py             # Схемы пагинации
│   ├── services/
│   │   ├── matching_service.py       # Основной сервис матчинга
│   │   ├── profile_client.py         # Клиент для profile-service
│   │   ├── redis_cache.py            # Кэширование в Redis
│   │   ├── red_flag_checker.py       # Проверка Red Flags
│   │   ├── event_service.py          # Публикация событий
│   │   └── rabbitmq.py               # Настройка RabbitMQ
│   ├── consumers/
│   │   └── profile_consumers.py      # Обработчики событий от profile-service
│   ├── dependencies.py               # Зависимости FastAPI
│   └── main.py                       # Точка входа FastAPI
├── Dockerfile
├── requirements.txt
└── README.md

Модели данных
Swipe (Свайп)
sql
- id (BIGINT)
- from_user_id (VARCHAR) — кто совершил свайп
- to_user_id (VARCHAR) — на кого совершили свайп
- swipe_type (VARCHAR) — 'like' или 'dislike'
- created_at, updated_at (TIMESTAMP)
- UNIQUE(from_user_id, to_user_id)
Match (Матч)
sql
- id (BIGINT)
- user1_id (VARCHAR)
- user2_id (VARCHAR)
- matched_at (TIMESTAMP)
- is_active (BOOLEAN)
- UNIQUE(user1_id, user2_id)
LikeWithAnswers (Лайк с ответами)
sql
- id (BIGINT)
- from_user_id (VARCHAR)
- to_user_id (VARCHAR)
- status (VARCHAR) — 'pending', 'matched', 'declined'
- answers (JSON) — ответы на 5 вопросов
- created_at, updated_at (TIMESTAMP)
- UNIQUE(from_user_id, to_user_id)
MatchWithAnswers (Матч с ответами)
sql
- id (BIGINT)
- user1_id (VARCHAR)
- user2_id (VARCHAR)
- user1_answers (JSON)
- user2_answers (JSON)
- user1_questions (JSON)
- user2_questions (JSON)
- matched_at (TIMESTAMP)
- is_active (BOOLEAN)
- UNIQUE(user1_id, user2_id)
TargetedSearchLock (Блокировка рекомендаций)
sql
- id (INTEGER)
- keycloak_id (VARCHAR) — UNIQUE
- is_locked (BOOLEAN)
- locked_until (TIMESTAMP)
- profiles_viewed (INTEGER)
- period_start (TIMESTAMP)
- created_at, updated_at (TIMESTAMP)
DailyLikeUsage (Дневной учёт лайков)
sql
- id (BIGINT)
- keycloak_id (VARCHAR)
- usage_date (DATE)
- likes_used (INTEGER)
- created_at, updated_at (TIMESTAMP)
- UNIQUE(keycloak_id, usage_date)

События RabbitMQ
Отправляемые события
MATCH_CREATED	Создан новый матч (для chat-service)

Получаемые события
USER_PROFILE_UPDATED	profile-service	Инвалидация кэша эмбеддинга

Потоки работы
Лайк с ответами
1. Пользователь A отправляет лайк с ответами пользователю B
2. Проверка: есть ли у B вопросы
3. Валидация ответов
4. Проверка дневного лимита лайков
5. Проверка: не отправлял ли A уже лайк B
6. Проверка: есть ли взаимный лайк от B к A
   - Если есть → создаётся матч с ответами
   - Если нет → сохраняется лайк с ответами (статус pending)
7. Отправка события MATCH_CREATED в chat-service (при матче)
Таргетированные рекомендации
text
1. Получение профиля пользователя (возраст, пол, город)
2. Определение автоматических фильтров:
   - Пол: противоположный полу пользователя
   - Возраст: ±5 лет (расширяется до ±15 при недостатке результатов)
   - Город: из фильтра или город пользователя
3. Проверка блокировки (лимит просмотров 100/день)
4. Поиск по эмбеддингу через pgvector
5. Фильтрация по Red Flags
6. Тональный ре-ранкинг (sentiment-эмбеддинги)
7. Инкремент счётчика просмотров
8. Блокировка при достижении лимита

Запуск сервиса
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload

# Запуск через Docker
docker build -t briolin-matching-service .
docker run -p 8006:8006 briolin-matching-service
