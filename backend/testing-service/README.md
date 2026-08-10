# Testing Service

Сервис для проведения психологического тестирования пользователей в системе Briolin. Управляет тестовыми сессиями, вопросами, ответами и результатами.

## Описание сервиса

**Основные функции:**
- Проведение психологического теста на готовность к отношениям
- Управление тестовыми сессиями (старт, завершение, продолжение)
- Хранение ответов пользователей
- Подсчёт результатов и определение прохождения теста
- Отправка результатов на email
- История пройденных тестов
- Дневной лимит попыток
- Поддержка разных типов вопросов (multiple_choice, likert_scale, true_false)

**Технологии:**
- FastAPI
- PostgreSQL (сессии, результаты)
- MongoDB (вопросы и шаблоны тестов)
- RabbitMQ (межсервисное взаимодействие)

## API Endpoints

### Тесты (`/api/v1/tests`)
 GET  `/tests/current`  Получение текущего активного теста  
 POST  `/tests/start`  Начало нового теста  
 POST  `/tests/{session_id}/answers/{question_id}`  Сохранение ответа  
 POST  `/tests/{session_id}/complete`  Завершение теста и получение результатов  
 GET  `/tests/{session_id}/results`  Получение результатов теста  
 GET  `/tests/history`  История пройденных тестов  
 GET  `/tests/statistics`  Статистика пользователя  
 GET  `/tests/questions/{question_id}`  Получение вопроса по ID (админ)  

### Примеры запросов

**Начало нового теста:**

POST /api/v1/tests/start  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{}  

**Ответ:**

{  
  "session_id": "123e4567-e89b-12d3-a456-426614174000",  
  "test_name": "Тест на готовность к знакомству",  
  "description": "Пройдите тест, чтобы показать свою готовность к серьезным отношениям",  
  "time_limit_minutes": 30,  
  "questions": [  
    {  
      "id": "q1",  
      "text": "Как вы обычно проводите свободное время?",  
      "question_type": "multiple_choice",  
      "difficulty": "easy",  
      "category": "lifestyle",  
      "tags": ["hobbies", "free_time"],  
      "options": [  
        {"id": "a1", "text": "Активно: спорт, походы, встречи с друзьями"},  
        {"id": "a2", "text": "Смешанно: иногда активно, иногда дома"},  
        {"id": "a3", "text": "В основном дома: чтение, фильмы, хобби"},  
        {"id": "a4", "text": "Предпочитаю одиночество"}  
      ],  
      "answered": false  
    },  
    {  
      "id": "q3",  
      "text": "Как часто вы общаетесь с новыми людьми?",  
      "question_type": "likert_scale",  
      "difficulty": "easy",  
      "category": "social",  
      "tags": ["social", "communication"],  
      "min_value": 1,  
      "max_value": 5,  
      "labels": {  
        "1": "Очень редко",  
        "2": "Редко",  
        "3": "Иногда",  
        "4": "Часто",  
        "5": "Постоянно"  
      },  
      "answered": false  
    }  
  ],  
  "started_at": "2026-01-15T10:30:00",  
  "expires_at": "2026-01-15T11:00:00",  
  "time_left_seconds": 1800  
}

---

**Сохранение ответа:**

POST /api/v1/tests/123e4567-e89b-12d3-a456-426614174000/answers/q1  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "answer": "a1"  
}

**Ответ:**

{  
  "session_id": "123e4567-e89b-12d3-a456-426614174000",  
  "question_id": "q1",  
  "answer_saved": true,  
  "total_answered": 1,  
  "total_questions": 10  
}

---

**Получение текущего теста (продолжение после перерыва):**

GET /api/v1/tests/current  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "session_id": "123e4567-e89b-12d3-a456-426614174000",  
  "test_name": "Тест на готовность к знакомству",  
  "description": "Пройдите тест, чтобы показать свою готовность к серьезным отношениям",  
  "status": "in_progress",  
  "started_at": "2026-01-15T10:30:00",  
  "expires_at": "2026-01-15T11:00:00",  
  "time_left_seconds": 1200,  
  "time_limit_minutes": 30,  
  "total_questions": 10,  
  "answered_questions": 5,  
  "questions": [  
    {  
      "id": "q1",  
      "text": "Как вы обычно проводите свободное время?",  
      "question_type": "multiple_choice",  
      "difficulty": "easy",  
      "category": "lifestyle",  
      "tags": ["hobbies", "free_time"],  
      "options": [  
        {"id": "a1", "text": "Активно: спорт, походы, встречи с друзьями"},  
        {"id": "a2", "text": "Смешанно: иногда активно, иногда дома"},  
        {"id": "a3", "text": "В основном дома: чтение, фильмы, хобби"},  
        {"id": "a4", "text": "Предпочитаю одиночество"}  
      ],  
      "answered": true,  
      "saved_answer": "a1"  
    },  
    {  
      "id": "q2",  
      "text": "Готовы ли вы к компромиссам в отношениях?",  
      "question_type": "multiple_choice",  
      "difficulty": "medium",  
      "category": "relationships",  
      "tags": ["compromise", "readiness"],  
      "options": [  
        {"id": "a1", "text": "Да, это ключ к здоровым отношениям"},  
        {"id": "a2", "text": "В большинстве случаев да"},  
        {"id": "a3", "text": "Только в очень важных для меня вопросах"},  
        {"id": "a4", "text": "Нет, я привык всегда быть правым"}  
      ],  
      "answered": false  
    }  
  ]  
}

---

**Завершение теста:**

POST /api/v1/tests/123e4567-e89b-12d3-a456-426614174000/complete  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{}  

**Ответ:**

{  
  "session_id": "123e4567-e89b-12d3-a456-426614174000",  
  "status": "completed",  
  "completed_at": "2026-01-15T10:45:00",  
  "time_spent_minutes": 15.5,  
  "results": {  
    "total_score": 85.5,  
    "max_possible_score": 100.0,  
    "percentage": 85.5,  
    "passed": true  
  },  
  "summary": {  
    "questions_total": 10,  
    "questions_answered": 10,  
    "completion_rate": 100.0  
  }  
}

---

**Получение результатов:**

GET /api/v1/tests/123e4567-e89b-12d3-a456-426614174000/results  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "session_id": "123e4567-e89b-12d3-a456-426614174000",  
  "status": "completed",  
  "completed_at": "2026-01-15T10:45:00",  
  "results": {  
    "total_score": 85.5,  
    "max_possible_score": 100.0,  
    "percentage": 85.5,  
    "passed": true  
  }  
}

---

**История тестов:**

GET /api/v1/tests/history?skip=0&limit=10  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "history": [  
    {  
      "session_id": "123e4567-e89b-12d3-a456-426614174000",  
      "test_name": "Тест на готовность к знакомству",  
      "completed_at": "2026-01-15T10:45:00",  
      "total_score": 85.5,  
      "percentage": 85.5,  
      "passed": true  
    }  
  ],  
  "total": 1,  
  "skip": 0,  
  "limit": 10  
}

---

**Статистика пользователя:**

GET /api/v1/tests/statistics  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "total_tests_taken": 3,  
  "total_tests_completed": 3,  
  "average_score": 78.3,  
  "last_test_date": "2026-01-15T10:45:00"  
}

---

### Структура вопросов

**Multiple Choice (множественный выбор):**

{  
  "id": "q1",  
  "text": "Как вы обычно проводите свободное время?",  
  "question_type": "multiple_choice",  
  "difficulty": "easy",  
  "category": "lifestyle",  
  "tags": ["hobbies", "free_time"],  
  "options": [  
    {"id": "a1", "text": "Активно: спорт, походы, встречи с друзьями", "score": 10, "is_correct": true},  
    {"id": "a2", "text": "Смешанно: иногда активно, иногда дома", "score": 8, "is_correct": true},  
    {"id": "a3", "text": "В основном дома: чтение, фильмы, хобби", "score": 6, "is_correct": false},  
    {"id": "a4", "text": "Предпочитаю одиночество", "score": 4, "is_correct": false}  
  ]  
}

**Likert Scale (шкала Лайкерта):**

{  
  "id": "q3",  
  "text": "Как часто вы общаетесь с новыми людьми?",  
  "question_type": "likert_scale",  
  "difficulty": "easy",  
  "category": "social",  
  "tags": ["social", "communication"],  
  "min_value": 1,  
  "max_value": 5,  
  "labels": {  
    "1": "Очень редко",  
    "2": "Редко",  
    "3": "Иногда",  
    "4": "Часто",  
    "5": "Постоянно"  
  }  
}

**True/False (правда/ложь):**

{  
  "id": "q8",  
  "text": "Важна ли вам личная гигиена партнера?",  
  "question_type": "true_false",  
  "difficulty": "easy",  
  "category": "values",  
  "tags": ["hygiene", "standards"],  
  "options": [  
    {"id": "a1", "text": "Да, очень важна", "score": 10, "is_correct": true},  
    {"id": "a2", "text": "Нет, не важна", "score": 0, "is_correct": false}  
  ]  
}

---

### Переменные окружения

#### Testing Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TESTING__DEBUG` | Режим отладки | `true` |
| `TESTING__SERVICE_NAME` | Имя сервиса | `testing-service` |

#### Database Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TESTING__DB__USER` | Пользователь PostgreSQL | `testing_user` |
| `TESTING__DB__PASSWORD` | Пароль PostgreSQL | `testing_password` |
| `TESTING__DB__HOST` | Хост PostgreSQL | `testing-postgres` |
| `TESTING__DB__PORT` | Порт PostgreSQL | `5432` |
| `TESTING__DB__NAME` | Название БД | `testing_db` |
| `TESTING__DB__ECHO` | Логирование SQL | `false` |
| `TESTING__DB__POOL_SIZE` | Размер пула соединений | `50` |
| `TESTING__DB__MAX_OVERFLOW` | Макс. переполнение пула | `10` |

#### MongoDB Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TESTING__MONGO__HOST` | Хост MongoDB | `testing-mongo` |
| `TESTING__MONGO__PORT` | Порт MongoDB | `27017` |
| `TESTING__MONGO__USERNAME` | Пользователь MongoDB | `` |
| `TESTING__MONGO__PASSWORD` | Пароль MongoDB | `` |
| `TESTING__MONGO__DATABASE` | Название БД | `testing` |

#### Test Config (дефолтные значения)

| Параметр | Описание | Значение по умолчанию |
|----------|----------|----------------------|
| `default_test_size` | Количество вопросов в тесте | `10` |
| `question_pool_size` | Размер пула вопросов | `15` |
| `max_attempts_per_day` | Макс. попыток в день | `30` |
| `test_time_limit_minutes` | Лимит времени (минуты) | `30` |

#### Shared Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `RABBITMQ__HOST` | Хост RabbitMQ | `rabbitmq` |
| `RABBITMQ__PORT` | Порт RabbitMQ | `5672` |
| `RABBITMQ__USER` | Пользователь RabbitMQ | `guest` |
| `RABBITMQ__PASSWORD` | Пароль RabbitMQ | `guest` |
| `RABBITMQ__VHOST` | VHost RabbitMQ | `/` |

---

### Структура проекта

**testing-service/** — сервис тестирования

- **app/** — основной код приложения
  - **api/v1/** — версионированные API эндпоинты
    - `tests.py` — эндпоинты тестов
  - **core/** — ядро сервиса
    - `config.py` — конфигурация сервиса
    - `logger.py` — настройка логирования
    - `exceptions.py` — кастомные исключения
    - `exception_handlers.py` — обработчики исключений
  - **database/** — работа с базами данных
    - `models.py` — модели PostgreSQL (сессии, результаты)
    - `mongo_models.py` — модели MongoDB (вопросы, шаблоны)
    - `session.py` — настройка сессий БД
  - **schemas/** — Pydantic схемы
    - `test.py` — схемы тестов
  - **services/** — бизнес-логика и внешние сервисы
    - `testing_service.py` — основной сервис тестирования
    - `test_generator.py` — генератор тестов
    - `scoring_service.py` — подсчёт результатов
    - `event_service.py` — публикация событий
    - `rabbitmq.py` — настройка RabbitMQ
  - `dependencies.py` — зависимости FastAPI
  - `main.py` — точка входа FastAPI

- **Dockerfile** — инструкция для сборки Docker образа
- **requirements.txt** — зависимости Python
- **README.md** — документация сервиса

---

### Модели данных

#### PostgreSQL

**TestSession (сессия теста):**

- `id` (UUID)
- `keycloak_id` (VARCHAR) — INDEX
- `test_template_id` (VARCHAR)
- `status` (VARCHAR) — 'created', 'in_progress', 'completed', 'expired', 'cancelled'
- `started_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP)
- `time_limit_minutes` (INTEGER)
- `questions_order` (JSON) — порядок вопросов
- `user_answers` (JSON) — ответы пользователя
- `UNIQUE(keycloak_id, status) WHERE status = 'in_progress'`

**TestResult (результат теста):**

- `id` (UUID)
- `session_id` (UUID) — FK
- `keycloak_id` (VARCHAR) — INDEX
- `total_score` (FLOAT)
- `max_possible_score` (FLOAT)
- `percentage` (FLOAT)
- `passed` (BOOLEAN)
- `created_at` (TIMESTAMP)

#### MongoDB

**TestTemplate (шаблон теста):**

{  
  "id": "dating_readiness_test_v1",  
  "name": "Тест на готовность к знакомству",  
  "description": "Пройдите тест, чтобы показать свою готовность к серьезным отношениям",  
  "version": "1.0.0",  
  "question_count": 10,  
  "time_limit_minutes": 30,  
  "pass_threshold": 70.0,  
  "question_pool": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11", "q12", "q13", "q14", "q15"],  
  "sampling_strategy": "random",  
  "is_active": true,  
  "created_at": "2026-01-01T00:00:00",  
  "updated_at": "2026-01-01T00:00:00"  
}

**Question (вопрос):**

{  
  "id": "q1",  
  "text": "Как вы обычно проводите свободное время?",  
  "question_type": "multiple_choice",  
  "difficulty": "easy",  
  "category": "lifestyle",  
  "tags": ["hobbies", "free_time"],  
  "options": [  
    {"id": "a1", "text": "Активно: спорт, походы, встречи с друзьями", "score": 10, "is_correct": true},  
    {"id": "a2", "text": "Смешанно: иногда активно, иногда дома", "score": 8, "is_correct": true},  
    {"id": "a3", "text": "В основном дома: чтение, фильмы, хобби", "score": 6, "is_correct": false},  
    {"id": "a4", "text": "Предпочитаю одиночество", "score": 4, "is_correct": false}  
  ],  
  "explanation": "Активный образ жизни способствует здоровым отношениям",  
  "created_at": "2026-01-01T00:00:00",  
  "updated_at": "2026-01-01T00:00:00"  
}

---

### События RabbitMQ

#### Отправляемые события

| Событие | Описание |
|---------|----------|
| `TEST_STARTED` | Тест начат |
| `TEST_COMPLETED` | Тест завершён (с результатами) |

#### Формат события TEST_COMPLETED

{  
  "event_type": "test.completed",  
  "event_id": "evt_123e4567-e89b-12d3-a456-426614174000",  
  "source_service": "testing-service",  
  "correlation_id": "saga_123e4567-e89b-12d3-a456-426614174000",  
  "user_data": {  
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
    "session_id": "123e4567-e89b-12d3-a456-426614174000",  
    "results": {  
      "total_score": 85.5,  
      "percentage": 85.5,  
      "passed": true  
    }  
  }  
}

---

### Подсчёт результатов

#### Алгоритм

1. Для каждого вопроса определяется максимальный балл
2. Ответ пользователя сравнивается с правильным ответом
3. Начисляются баллы за каждый вопрос
4. Суммируется общий балл
5. Нормализуется к 100-балльной шкале
6. Определяется прохождение (порог: 70%)

#### Типы вопросов и их оценка

| Тип | Макс. балл | Оценка |
|-----|-----------|--------|
| `multiple_choice` | 10 | Балл выбранного варианта |
| `likert_scale` | 10 | Нормализованное значение (1→1, 5→10) |
| `true_false` | 10 | 10 за правильный, 0 за неправильный |

---

### Запуск сервиса  

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

# Запуск через Docker
docker build -t briolin-testing-service .
docker run -p 8004:8004 briolin-testing-service

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

# Запуск через Docker
docker build -t briolin-testing-service .
docker run -p 8004:8004 briolin-testing-service
