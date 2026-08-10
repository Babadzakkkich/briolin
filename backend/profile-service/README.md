# Profile Service

Сервис управления профилями пользователей в системе Briolin. Отвечает за хранение базовой и детальной информации о пользователях, управление вопросами для знакомства, генерацию эмбеддингов для рекомендаций и синхронизацию данных с другими сервисами.

## Описание сервиса

**Основные функции:**
- Хранение базовой информации (имя, фамилия, пол, дата рождения, город)
- Хранение детальной информации (о себе, образование, хобби, предпочтения)
- Управление вопросами для знакомства (5 вопросов)
- Генерация и хранение эмбеддингов (semantic + sentiment)
- Поиск профилей по эмбеддингам (pgvector)
- Онлайн-статусы пользователей
- Асинхронное обновление через SAGA паттерн
- Интеграция с media-service (аватарки)
- Интеграция с auth-service (обновление имени в Keycloak)

**Технологии:**
- FastAPI
- PostgreSQL + pgvector (эмбеддинги)
- Sentence Transformers (генерация эмбеддингов)
- Transformers (анализ тональности)
- RabbitMQ (межсервисное взаимодействие)
- SAGA паттерн (распределённые транзакции)

## API Endpoints

### Профили (`/api/v1/profiles`)

 POST  `/profiles/basic`  Создание базового профиля (синхронно)  
 POST  `/profiles/detailed`  Создание детального профиля (синхронно)  
 GET  `/profiles/me`  Получение своего полного профиля  
 PUT  `/profiles/me`  Обновление профиля (асинхронно, SAGA)  
 DELETE  `/profiles/me`  Удаление профиля (асинхронно, SAGA)  
 GET  `/profiles/me/questions`  Получение своих вопросов  
 POST  `/profiles/me/questions`  Создание/обновление вопросов  
 PATCH  `/profiles/me/questions`  Частичное обновление вопросов  
 GET  `/profiles/{keycloak_id}`  Получение профиля пользователя (админ)  
 GET  `/profiles/{keycloak_id}/questions`  Получение вопросов пользователя  
 GET  `/profiles/saga/{saga_id}/status`  Статус SAGA операции  

### Примеры запросов  

**Создание базового профиля:**

POST /api/v1/profiles/basic  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "first_name": "John",  
  "last_name": "Doe",  
  "gender": "male",  
  "date_of_birth": "1995-05-15",  
  "city": "Moscow"  
}

**Ответ:**

{  
  "basic": {  
    "id": 1,  
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
    "first_name": "John",  
    "last_name": "Doe",  
    "gender": "male",  
    "date_of_birth": "1995-05-15",  
    "city": "Moscow",  
    "online": false,  
    "avatar_url": null,  
    "thumbnail_url": null,  
    "created_at": "2026-01-15T10:30:00",  
    "updated_at": "2026-01-15T10:30:00",  
    "last_login_at": null  
  },  
  "detailed": null,  
  "questions": null  
}

---

**Создание детального профиля:**

POST /api/v1/profiles/detailed  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "about_me": "Люблю путешествия, хорошую музыку и активный образ жизни",  
  "education": "Высшее, МГУ",  
  "hobbies": "Путешествия, музыка, спорт, фотография",  
  "partner_preferences": "Активный, целеустремлённый, с чувством юмора",  
  "red_flags": ["Курение", "Лень", "Неуважение к окружающим"]  
}

**Ответ:**

{  
  "basic": {  
    "id": 1,  
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
    "first_name": "John",  
    "last_name": "Doe",  
    "gender": "male",  
    "date_of_birth": "1995-05-15",  
    "city": "Moscow",  
    "online": false,  
    "avatar_url": null,  
    "created_at": "2026-01-15T10:30:00",  
    "updated_at": "2026-01-15T10:35:00",  
    "last_login_at": null  
  },  
  "detailed": {  
    "id": 1,  
    "about_me": "Люблю путешествия, хорошую музыку и активный образ жизни",  
    "education": "Высшее, МГУ",  
    "hobbies": "Путешествия, музыка, спорт, фотография",  
    "partner_preferences": "Активный, целеустремлённый, с чувством юмора",  
    "red_flags": ["Курение", "Лень", "Неуважение к окружающим"]  
  },  
  "questions": null  
}

---

**Создание вопросов:**

POST /api/v1/profiles/me/questions  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "question_1": "Как вы обычно проводите свободное время?",  
  "question_2": "Готовы ли вы к компромиссам в отношениях?",  
  "question_3": "Как часто вы общаетесь с новыми людьми?",  
  "question_4": "Что для вас главное в отношениях?",  
  "question_5": "Как вы решаете конфликты?"  
}

**Ответ:** возвращает полный профиль с вопросами

---

**Получение своего профиля:**

GET /api/v1/profiles/me  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "basic": {  
    "id": 1,  
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
    "first_name": "John",  
    "last_name": "Doe",  
    "gender": "male",  
    "date_of_birth": "1995-05-15",  
    "city": "Moscow",  
    "online": true,  
    "avatar_url": "/media/avatar/550e8400...?avatar_id=123e4567...",  
    "thumbnail_url": "/media/avatar/550e8400.../thumbnail?avatar_id=123e4567...",  
    "created_at": "2026-01-15T10:30:00",  
    "updated_at": "2026-01-15T10:45:00",  
    "last_login_at": "2026-01-15T10:45:00"  
  },  
  "detailed": {  
    "id": 1,  
    "about_me": "Люблю путешествия, хорошую музыку и активный образ жизни",  
    "education": "Высшее, МГУ",  
    "hobbies": "Путешествия, музыка, спорт, фотография",  
    "partner_preferences": "Активный, целеустремлённый, с чувством юмора",  
    "red_flags": ["Курение", "Лень", "Неуважение к окружающим"]  
  },  
  "questions": {  
    "question_1": "Как вы обычно проводите свободное время?",  
    "question_2": "Готовы ли вы к компромиссам в отношениях?",  
    "question_3": "Как часто вы общаетесь с новыми людьми?",  
    "question_4": "Что для вас главное в отношениях?",  
    "question_5": "Как вы решаете конфликты?",  
    "created_at": "2026-01-15T10:40:00",  
    "updated_at": "2026-01-15T10:40:00"  
  }  
}

---

**Обновление профиля (асинхронно):**

PUT /api/v1/profiles/me  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "basic": {  
    "first_name": "Jonathan",  
    "city": "Saint Petersburg"  
  },  
  "detailed": {  
    "about_me": "Люблю путешествия, хорошую музыку и активный образ жизни. Также увлекаюсь кулинарией."  
  }  
}

**Ответ:**

{  
  "status": "accepted",  
  "message": "Profile update initiated",  
  "saga_id": "saga_123e4567-e89b-12d3-a456-426614174000",  
  "check_status_url": "/api/v1/profiles/saga/saga_123e4567-e89b-12d3-a456-426614174000/status"  
}

---

**Статус SAGA операции:**

GET /api/v1/profiles/saga/saga_123e4567-e89b-12d3-a456-426614174000/status  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "saga_id": "saga_123e4567-e89b-12d3-a456-426614174000",  
  "name": "profile_update",  
  "status": "completed",  
  "created_at": "2026-01-15T10:50:00",  
  "updated_at": "2026-01-15T10:50:05",  
  "completed_at": "2026-01-15T10:50:05",  
  "error": null,  
  "steps": [  
    {  
      "name": "update_basic_profile",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:00"  
    },  
    {  
      "name": "update_detailed_profile",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:02"  
    },  
    {  
      "name": "publish_profile_updated",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:04"  
    }  
  ],  
  "step_results": {  
    "update_basic_profile": {  
      "status": "success",  
      "basic_profile_id": 1,  
      "updated_fields": ["first_name", "city"]  
    },  
    "update_detailed_profile": {  
      "status": "success",  
      "detailed_profile_id": 1,  
      "updated_fields": ["about_me"]  
    },  
    "publish_profile_updated": {  
      "status": "success",  
      "event_published": true  
    }  
  },  
  "profile": {  
    "basic": { ... },  
    "detailed": { ... },  
    "questions": { ... }  
  }  
}

---

**Получение вопросов пользователя:**

GET /api/v1/profiles/550e8400-e29b-41d4-a716-446655440001/questions  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "question_1": "Как вы проводите свободное время?",  
  "question_2": "Готовы ли вы к компромиссам?",  
  "question_3": "Как часто общаетесь с новыми людьми?",  
  "question_4": "Что главное в отношениях?",  
  "question_5": "Как решаете конфликты?",  
  "created_at": "2026-01-15T10:40:00",  
  "updated_at": "2026-01-15T10:40:00"  
}

---

**Статус вопросов:**

GET /api/v1/profiles/me/questions/status  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "has_questions": true,  
  "questions_count": 5,  
  "total_required": 5,  
  "can_receive_likes": true  
}

---

### Внутренние эндпоинты (`/api/v1/internal`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/internal/profiles/{keycloak_id}` | Получение полного профиля |
| GET | `/internal/profiles/{keycloak_id}/basic` | Получение базового профиля |
| GET | `/internal/profiles/{keycloak_id}/questions` | Получение вопросов |
| GET | `/internal/profiles/{keycloak_id}/has-questions` | Проверка наличия вопросов |
| GET | `/internal/profiles/{keycloak_id}/embedding` | Получение эмбеддинга |
| GET | `/internal/profiles/{keycloak_id}/sentiment-embedding` | Получение тонального эмбеддинга |
| POST | `/internal/profiles/search` | Поиск профилей по фильтрам |
| POST | `/internal/profiles/search_by_embedding` | Поиск по эмбеддингу (pgvector) |
| POST | `/internal/profiles/batch` | Получение нескольких профилей |
| POST | `/internal/profiles/update_embedding` | Принудительное обновление эмбеддинга |

---

### Переменные окружения

#### Profile Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `PROFILE__DEBUG` | Режим отладки | `false` |
| `PROFILE__SERVICE_NAME` | Имя сервиса | `profile-service` |

#### Database Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `PROFILE__DB__USER` | Пользователь PostgreSQL | `profile_user` |
| `PROFILE__DB__PASSWORD` | Пароль PostgreSQL | `profile_password` |
| `PROFILE__DB__HOST` | Хост PostgreSQL | `profile-postgres` |
| `PROFILE__DB__PORT` | Порт PostgreSQL | `5432` |
| `PROFILE__DB__NAME` | Название БД | `profile_db` |
| `PROFILE__DB__ECHO` | Логирование SQL | `false` |
| `PROFILE__DB__POOL_SIZE` | Размер пула соединений | `50` |
| `PROFILE__DB__MAX_OVERFLOW` | Макс. переполнение пула | `10` |

#### Auth Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `PROFILE__AUTH_SERVICE__URL` | URL auth-service | `http://auth-service:8001` |

#### Shared Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `KEYCLOAK__SERVER_URL` | URL Keycloak сервера | `http://keycloak:8080` |
| `KEYCLOAK__REALM` | Realm в Keycloak | `briolin` |
| `RABBITMQ__HOST` | Хост RabbitMQ | `rabbitmq` |
| `RABBITMQ__PORT` | Порт RabbitMQ | `5672` |
| `RABBITMQ__USER` | Пользователь RabbitMQ | `guest` |
| `RABBITMQ__PASSWORD` | Пароль RabbitMQ | `guest` |
| `RABBITMQ__VHOST` | VHost RabbitMQ | `/` |

---

### Структура проекта

**profile-service/** — сервис профилей

- **app/** — основной код приложения
  - **api/v1/** — версионированные API эндпоинты
    - `profiles.py` — основные эндпоинты
    - `internal.py` — внутренние эндпоинты
  - **core/** — ядро сервиса
    - `config.py` — конфигурация сервиса
    - `logger.py` — настройка логирования
    - `exceptions.py` — кастомные исключения
    - `exception_handlers.py` — обработчики исключений
  - **database/** — работа с базой данных
    - `models.py` — модели PostgreSQL
    - `session.py` — настройка сессии БД
  - **schemas/** — Pydantic схемы
    - `profile.py` — схемы профилей
    - `questions.py` — схемы вопросов
    - `internal.py` — внутренние схемы
  - **services/** — бизнес-логика и внешние сервисы
    - `profile_service.py` — основной сервис профилей
    - `keycloak_client.py` — клиент для Keycloak
    - `embedding_service.py` — генерация эмбеддингов
    - `sentiment_service.py` — анализ тональности
    - `embedding_updater.py` — обновление эмбеддингов
    - `event_service.py` — публикация событий
    - `rabbitmq.py` — настройка RabbitMQ
    - `saga_handlers.py` — обработчики SAGA шагов
    - `saga_worker.py` — SAGA воркер
  - **consumers/** — обработчики сообщений
    - `auth_consumers.py` — обработчики от auth-service
    - `media_consumers.py` — обработчики от media-service
    - `status_consumers.py` — обработчики онлайн-статуса
  - `dependencies.py` — зависимости FastAPI
  - `main.py` — точка входа FastAPI

- **Dockerfile** — инструкция для сборки Docker образа
- **requirements.txt** — зависимости Python
- **README.md** — документация сервиса

---

### Модели данных

**BasicProfile (базовая информация)**

- `id` (INTEGER)
- `keycloak_id` (VARCHAR) — UNIQUE
- `first_name` (VARCHAR)
- `last_name` (VARCHAR)
- `gender` (VARCHAR) — 'male', 'female', 'other'
- `date_of_birth` (DATE)
- `city` (VARCHAR)
- `online` (BOOLEAN)
- `avatar_url` (VARCHAR)
- `thumbnail_url` (VARCHAR)
- `embedding` (VECTOR(384)) — семантический эмбеддинг
- `sentiment_embedding` (VECTOR(3)) — тональный эмбеддинг
- `created_at`, `updated_at` (TIMESTAMP)
- `last_login_at` (TIMESTAMP)

**DetailedProfile (детальная информация)**

- `id` (INTEGER)
- `basic_profile_id` (INTEGER) — FK, UNIQUE
- `about_me` (TEXT)
- `education` (VARCHAR)
- `hobbies` (TEXT)
- `partner_preferences` (TEXT)
- `red_flags` (ARRAY(VARCHAR)) — список вещей, которые пользователь не приемлет

**ProfileQuestions (вопросы)**

- `id` (INTEGER)
- `basic_profile_id` (INTEGER) — FK, UNIQUE
- `question_1` (VARCHAR(500))
- `question_2` (VARCHAR(500))
- `question_3` (VARCHAR(500))
- `question_4` (VARCHAR(500))
- `question_5` (VARCHAR(500))
- `created_at`, `updated_at` (TIMESTAMP)

---

### Генерация эмбеддингов

#### Семантический эмбеддинг

- **Модель:** `paraphrase-multilingual-MiniLM-L12-v2`
- **Поля для генерации:**
  - `about_me`
  - `hobbies`
  - `partner_preferences`
- **Размерность:** 384

#### Тональный эмбеддинг (Sentiment)

- **Модель:** `yangheng/deberta-v3-base-absa-v1.1`
- **Поля для генерации:**
  - `about_me`
- **Размерность:** 3 (POSITIVE, NEGATIVE, NEUTRAL)

**Пример вектора:**

[0.15, 0.05, 0.80]

---

### События RabbitMQ

#### Отправляемые события

| Событие | Описание |
|---------|----------|
| `USER_PROFILE_UPDATE_REQUESTED` | Запрос на обновление имени в Keycloak (для auth-service) |
| `USER_PROFILE_UPDATED` | Подтверждение обновления профиля (для chat-service, matching-service) |

#### Получаемые события

| Событие | Источник | Действие |
|---------|----------|----------|
| `USER_ONLINE` | chat-service | Обновление онлайн-статуса |
| `USER_OFFLINE` | chat-service | Обновление онлайн-статуса |
| `USER_DELETED` | auth-service | Удаление всех профилей пользователя |
| `AVATAR_UPLOADED` | media-service | Обновление avatar_url, thumbnail_url |
| `AVATAR_UPDATED` | media-service | Обновление avatar_url, thumbnail_url |
| `AVATAR_DELETED` | media-service | Очистка avatar_url, thumbnail_url |

---

### SAGA паттерн

Profile Service использует SAGA паттерн для асинхронных операций:

#### Обновление профиля

1. Шаг 1: `update_basic_profile` (если есть изменения)
2. Шаг 2: `update_detailed_profile` (если есть изменения, зависит от шага 1)
3. Шаг 3: `publish_profile_updated` (зависит от шагов 1-2)

#### Удаление профиля

1. Шаг 1: `delete_basic_profile`
2. Шаг 2: `publish_profile_deleted` (зависит от шага 1)

#### Компенсации

В случае ошибки на любом шаге выполняется компенсация (откат предыдущих изменений).

---

### Запуск сервиса

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# Запуск через Docker
docker build -t briolin-profile-service .
docker run -p 8003:8003 briolin-profile-service
