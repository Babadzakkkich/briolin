# User Service

Сервис управления пользователями в системе Briolin. Хранит основную информацию о пользователях, их ролях и статусах, а также координирует изменения через SAGA-паттерн с auth-service.

## Описание сервиса

**Основные функции:**
- Хранение пользователей (username, email, keycloak_id)
- Управление ролями пользователей (admin, psychologist, user)
- Отслеживание статуса активности пользователя
- Отслеживание прохождения теста (is_test_passed)
- Синхронное создание пользователя (для auth-service)
- Асинхронное обновление через SAGA-паттерн
- Взаимодействие с auth-service через RabbitMQ
- Получение подтверждений от auth-service

**Технологии:**
- FastAPI
- PostgreSQL (хранение пользователей и ролей)
- Keycloak (чтение информации о пользователях)
- RabbitMQ (межсервисное взаимодействие)
- SAGA-паттерн (распределённые транзакции)

## API Endpoints

### Пользователи (`/api/v1/users`)
 GET  `/users/`  Список пользователей (админ)  
 GET  `/users/me`  Информация о текущем пользователе  
 GET  `/users/{keycloak_id}`  Получение пользователя по ID  
 GET  `/users/username/{username}`  Получение пользователя по username (админ)  
 GET  `/users/email/{email}`  Получение пользователя по email (админ)  
 GET  `/users/role/{role}`  Получение пользователей по роли (админ)  
 GET  `/users/{keycloak_id}/exists`  Проверка существования пользователя  
 PUT  `/users/{keycloak_id}`  Обновление пользователя  
 PUT  `/users/{keycloak_id}/roles`  Обновление ролей (админ)  
 PATCH  `/users/{keycloak_id}/toggle-status`  Переключение статуса (админ)  
 DELETE  `/users/{keycloak_id}`  Удаление пользователя (админ)  
 GET  `/users/saga/{saga_id}/status`  Статус SAGA операции  

### Примеры запросов

**Получение информации о себе:**

GET /api/v1/users/me  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "id": 1,  
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
  "username": "john_doe",  
  "email": "user@example.com",  
  "roles": ["user"],  
  "is_active": true,  
  "is_test_passed": true,  
  "created_at": "2026-01-15T10:30:00"  
}

---

**Получение пользователя по ID:**

GET /api/v1/users/550e8400-e29b-41d4-a716-446655440001  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "id": 2,  
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",  
  "username": "jane_smith",  
  "email": "jane@example.com",  
  "is_active": true,  
  "is_test_passed": false,  
  "roles": ["user"],  
  "created_at": "2026-01-15T10:35:00"  
}

---

**Обновление пользователя (асинхронно):**

PUT /api/v1/users/550e8400-e29b-41d4-a716-446655440000  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "username": "jonathan_doe",  
  "email": "jonathan@example.com"  
}

**Ответ:**

{  
  "status": "accepted",  
  "message": "User update initiated",  
  "saga_id": "saga_123e4567-e89b-12d3-a456-426614174000",  
  "check_status_url": "/api/v1/users/saga/saga_123e4567-e89b-12d3-a456-426614174000/status"  
}

---

**Обновление ролей (админ):**

PUT /api/v1/users/550e8400-e29b-41d4-a716-446655440001/roles  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "roles": ["admin", "psychologist"]  
}

**Ответ:**

{  
  "status": "accepted",  
  "message": "Roles update initiated",  
  "saga_id": "saga_234f5678-e89b-12d3-a456-426614174001",  
  "check_status_url": "/api/v1/users/saga/saga_234f5678-e89b-12d3-a456-426614174001/status"  
}

---

**Переключение статуса (админ):**

PATCH /api/v1/users/550e8400-e29b-41d4-a716-446655440001/toggle-status  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "status": "accepted",  
  "message": "Status change initiated",  
  "saga_id": "saga_345g6789-e89b-12d3-a456-426614174002",  
  "check_status_url": "/api/v1/users/saga/saga_345g6789-e89b-12d3-a456-426614174002/status"  
}

---

**Удаление пользователя (админ):**

DELETE /api/v1/users/550e8400-e29b-41d4-a716-446655440001  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "status": "accepted",  
  "message": "User deletion initiated",  
  "saga_id": "saga_456h7890-e89b-12d3-a456-426614174003",  
  "check_status_url": "/api/v1/users/saga/saga_456h7890-e89b-12d3-a456-426614174003/status"  
}

---

**Список пользователей (админ):**

GET /api/v1/users/?skip=0&limit=100  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "users": [  
    {  
      "id": 1,  
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
      "username": "john_doe",  
      "email": "user@example.com",  
      "is_active": true,  
      "is_test_passed": true,  
      "roles": ["user"],  
      "created_at": "2026-01-15T10:30:00"  
    }  
  ],  
  "total": 1,  
  "page": 1,  
  "size": 100  
}

---

**Статус SAGA операции:**

GET /api/v1/users/saga/saga_123e4567-e89b-12d3-a456-426614174000/status  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "saga_id": "saga_123e4567-e89b-12d3-a456-426614174000",  
  "name": "user_profile_update",  
  "status": "completed",  
  "created_at": "2026-01-15T10:50:00",  
  "updated_at": "2026-01-15T10:50:05",  
  "completed_at": "2026-01-15T10:50:05",  
  "error": null,  
  "steps": [  
    {  
      "name": "publish_user_profile_update_requested",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:00"  
    },  
    {  
      "name": "update_user_profile",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:02"  
    },  
    {  
      "name": "publish_user_updated",  
      "status": "completed",  
      "attempts": 1,  
      "error": null,  
      "created_at": "2026-01-15T10:50:04"  
    }  
  ],  
  "step_results": {  
    "publish_user_profile_update_requested": {  
      "status": "success",  
      "event_published": true  
    },  
    "update_user_profile": {  
      "status": "success",  
      "user_id": 1,  
      "updated_fields": ["username", "email"]  
    },  
    "publish_user_updated": {  
      "status": "success",  
      "event_published": true  
    }  
  },  
  "user": {  
    "id": 1,  
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
    "username": "jonathan_doe",  
    "email": "jonathan@example.com",  
    "roles": ["user"],  
    "is_active": true,  
    "is_test_passed": true  
  }  
}

---

### Внутренние эндпоинты (`/api/v1/internal`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/internal/users` | Создание пользователя (синхронно) |
| GET | `/internal/users/{keycloak_id}` | Получение пользователя |

---

### Переменные окружения

#### User Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `USER__DEBUG` | Режим отладки | `false` |
| `USER__SERVICE_NAME` | Имя сервиса | `user-service` |
| `USER__AUTH_SERVICE_URL` | URL auth-service | `http://auth-service:8001` |

#### Database Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `USER__DB__USER` | Пользователь PostgreSQL | `user_user` |
| `USER__DB__PASSWORD` | Пароль PostgreSQL | `user_password` |
| `USER__DB__HOST` | Хост PostgreSQL | `user-postgres` |
| `USER__DB__PORT` | Порт PostgreSQL | `5432` |
| `USER__DB__NAME` | Название БД | `user_db` |
| `USER__DB__ECHO` | Логирование SQL | `false` |
| `USER__DB__POOL_SIZE` | Размер пула соединений | `50` |
| `USER__DB__MAX_OVERFLOW` | Макс. переполнение пула | `10` |

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

**user-service/** — сервис пользователей

- **app/** — основной код приложения
  - **api/v1/** — версионированные API эндпоинты
    - `users.py` — основные эндпоинты
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
    - `user.py` — схемы пользователей
    - `internal.py` — внутренние схемы
  - **services/** — бизнес-логика и внешние сервисы
    - `user_service.py` — основной сервис пользователей
    - `keycloak_client.py` — клиент для Keycloak
    - `event_service.py` — публикация событий
    - `rabbitmq.py` — настройка RabbitMQ
    - `saga_handlers.py` — обработчики SAGA шагов
    - `saga_worker.py` — SAGA воркер
  - **consumers/** — обработчики сообщений
    - `auth_consumers.py` — обработчики от auth-service
    - `testing_consumers.py` — обработчики от testing-service
  - `dependencies.py` — зависимости FastAPI
  - `main.py` — точка входа FastAPI

- **Dockerfile** — инструкция для сборки Docker образа
- **requirements.txt** — зависимости Python
- **README.md** — документация сервиса

---

### Модели данных

**User (пользователь)**

- `id` (INTEGER)
- `keycloak_id` (VARCHAR) — UNIQUE, INDEX
- `username` (VARCHAR) — UNIQUE, INDEX
- `email` (VARCHAR) — UNIQUE, INDEX
- `is_active` (BOOLEAN)
- `is_test_passed` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**UserRoleAssignment (назначение ролей)**

- `id` (INTEGER)
- `user_id` (INTEGER) — FK, CASCADE
- `role` (ENUM) — 'admin', 'psychologist', 'user'
- `assigned_at` (TIMESTAMP)
- `UNIQUE(user_id, role)`

---

### SAGA-паттерн

User Service использует SAGA-паттерн для всех изменений, которые требуют синхронизации с Keycloak через auth-service.

#### Поток обновления пользователя

1. Пользователь отправляет запрос на обновление
2. User Service создаёт SAGA-сессию
3. Шаг 1: `publish_user_profile_update_requested` → публикация события в RabbitMQ
4. Шаг 2: `update_user_profile` → обновление в user-db
5. Шаг 3: `publish_user_updated` → публикация подтверждения
6. Auth Service получает событие, обновляет Keycloak и auth-db
7. Auth Service публикует `USER_PROFILE_UPDATED`
8. User Service получает подтверждение, завершает SAGA

#### Поток обновления ролей

1. Администратор отправляет запрос на обновление ролей
2. User Service создаёт SAGA-сессию
3. Шаг 1: `publish_user_roles_update_requested` → публикация события
4. Шаг 2: `update_user_roles` → обновление ролей в user-db
5. Шаг 3: `publish_user_roles_updated` → публикация подтверждения
6. Auth Service получает событие, обновляет роли в Keycloak
7. Auth Service публикует `USER_ROLES_UPDATED`
8. User Service получает подтверждение

#### Поток удаления пользователя

1. Администратор отправляет запрос на удаление
2. User Service создаёт SAGA-сессию
3. Шаг 1: `publish_user_deletion_requested` → публикация события
4. Шаг 2: `delete_user_profile` → удаление из user-db
5. Шаг 3: `publish_user_deleted` → публикация подтверждения
6. Auth Service получает событие, удаляет из Keycloak и auth-db
7. Auth Service публикует `USER_DELETED`
8. User Service получает подтверждение

---

### События RabbitMQ

#### Отправляемые события (запросы к auth-service)

| Событие | Описание |
|---------|----------|
| `USER_PROFILE_UPDATE_REQUESTED` | Запрос на обновление профиля |
| `USER_STATUS_CHANGE_REQUESTED` | Запрос на изменение статуса |
| `USER_ROLES_UPDATE_REQUESTED` | Запрос на обновление ролей |
| `USER_DELETION_REQUESTED` | Запрос на удаление пользователя |

#### Отправляемые события (подтверждения для других сервисов)

| Событие | Описание |
|---------|----------|
| `USER_PROFILE_CREATED` | Пользователь создан (после регистрации) |
| `USER_PROFILE_UPDATED` | Профиль обновлён (подтверждение) |
| `USER_STATUS_CHANGED` | Статус изменён (подтверждение) |
| `USER_ROLES_UPDATED` | Роли обновлены (подтверждение) |
| `USER_DELETED` | Пользователь удалён (подтверждение) |

#### Получаемые события

| Событие | Источник | Действие |
|---------|----------|----------|
| `USER_PROFILE_UPDATED` | auth-service | Обновление локальных данных |
| `USER_STATUS_CHANGED` | auth-service | Обновление локального статуса |
| `USER_ROLES_UPDATED` | auth-service | Обновление локальных ролей |
| `USER_DELETED` | auth-service | Удаление локального пользователя |
| `TEST_COMPLETED` | testing-service | Обновление is_test_passed |

---

### Запуск сервиса

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Запуск через Docker
docker build -t briolin-user-service .
docker run -p 8002:8002 briolin-user-service

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Запуск через Docker
docker build -t briolin-user-service .
docker run -p 8002:8002 briolin-user-service
