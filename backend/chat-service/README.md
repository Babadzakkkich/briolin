# Chat Service

Сервис для обмена сообщениями в реальном времени. Обеспечивает создание чатов, отправку сообщений, WebSocket соединения, онлайн-статусы пользователей и хранение истории сообщений.

## Описание сервиса

**Основные функции:**
- Создание личных и групповых чатов
- Отправка и получение сообщений в реальном времени (WebSocket)
- REST API для управления чатами и сообщениями
- Отслеживание статусов прочтения сообщений (Read Receipts)
- Онлайн-статусы пользователей
- Поиск сообщений по тексту (MongoDB)
- Поддержка редактирования и удаления сообщений
- Уведомления о наборе текста (Typing Indicators)

**Технологии:**
- FastAPI
- PostgreSQL (метаданные чатов и участников)
- MongoDB (хранение сообщений для поиска)
- Redis (онлайн-статусы, rate limiting)
- WebSocket (обмен сообщениями в реальном времени)
- RabbitMQ (межсервисное взаимодействие)

## API Endpoints

### Чаты (`/api/v1/chats`)

 GET  `/chats/`  Список чатов пользователя 
 POST  `/chats/`  Создание чата 
 GET  `/chats/{chat_id}`  Получение чата 
 PUT  `/chats/{chat_id}`  Обновление чата (групповой) 
 DELETE  `/chats/{chat_id}`  Удаление чата 
 GET  `/chats/search/messages`  Поиск сообщений 
 GET  `/chats/online/users`  Список онлайн пользователей 

### Примеры запросов

**Создание личного чата:**

POST /api/v1/chats/  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "type": "direct",  
  "participant_ids": ["550e8400-e29b-41d4-a716-446655440001"]  
}

**Ответ:**

{  
  "id": "123e4567-e89b-12d3-a456-426614174000",  
  "type": "direct",  
  "status": "active",  
  "name": "Jane Smith",  
  "description": null,  
  "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=...",  
  "participants": [  
    {  
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
      "display_name": "John Doe",  
      "username": "john_doe",  
      "is_admin": true,  
      "notifications_enabled": true,  
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=..."  
    },  
    {  
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",  
      "display_name": "Jane Smith",  
      "username": "jane_smith",  
      "is_admin": false,  
      "notifications_enabled": true,  
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=..."  
    }  
  ],  
  "created_at": "2026-01-15T10:40:00",  
  "updated_at": "2026-01-15T10:40:00",  
  "last_message": null,  
  "unread_count": 0,  
  "match_id": null  
}

---

**Создание группового чата:**

POST /api/v1/chats/  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "type": "group",  
  "participant_ids": [  
    "550e8400-e29b-41d4-a716-446655440001",  
    "550e8400-e29b-41d4-a716-446655440002"  
  ],  
  "name": "Команда проекта",  
  "description": "Обсуждение разработки Briolin"  
}

---

**Список чатов:**

GET /api/v1/chats/?skip=0&limit=50&chat_type=direct&status=active  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "chats": [  
    {  
      "id": "123e4567-e89b-12d3-a456-426614174000",  
      "type": "direct",  
      "status": "active",  
      "name": "Jane Smith",  
      "last_message": {  
        "id": "456e7890-f12a-34b5-c678-901234567890",  
        "content": "Привет! Как дела?",  
        "sender_id": "550e8400-e29b-41d4-a716-446655440001",  
        "sender_display_name": "Jane Smith",  
        "created_at": "2026-01-15T10:45:00"  
      },  
      "unread_count": 3,  
      "match_id": 42  
    }  
  ],  
  "total": 1,  
  "page": 1,  
  "size": 50  
}

---

### Сообщения (`/api/v1/chats`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/chats/{chat_id}/messages` | Отправка сообщения |
| GET | `/chats/{chat_id}/messages` | Получение сообщений |
| PUT | `/chats/messages/{message_id}` | Редактирование сообщения |
| DELETE | `/chats/messages/{message_id}` | Удаление сообщения |
| POST | `/chats/{chat_id}/read` | Отметка сообщений как прочитанных |
| GET | `/chats/messages/{message_id}/read-status` | Статус прочтения сообщения |
| GET | `/chats/{chat_id}/match-answers` | Ответы на вопросы матча |

#### Примеры запросов

**Отправка сообщения:**

POST /api/v1/chats/123e4567-e89b-12d3-a456-426614174000/messages  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "content": "Привет! Как дела?",  
  "message_type": "text"  
}

**Ответ:**

{  
  "id": "456e7890-f12a-34b5-c678-901234567890",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "sender_keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
  "sender_display_name": "John Doe",  
  "sender_username": "john_doe",  
  "content": "Привет! Как дела?",  
  "message_type": "text",  
  "status": "sent",  
  "is_edited": false,  
  "reply_to_id": null,  
  "media_url": null,  
  "media_type": null,  
  "file_size": null,  
  "created_at": "2026-01-15T10:45:00",  
  "updated_at": "2026-01-15T10:45:00",  
  "read_by": [],  
  "read_count": 0,  
  "is_read_by_me": true  
}

---

**Получение сообщений:**

GET /api/v1/chats/123e4567-e89b-12d3-a456-426614174000/messages?skip=0&limit=50  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "messages": [  
    {  
      "id": "456e7890-f12a-34b5-c678-901234567890",  
      "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
      "sender_keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
      "sender_display_name": "John Doe",  
      "content": "Привет! Как дела?",  
      "message_type": "text",  
      "status": "delivered",  
      "created_at": "2026-01-15T10:45:00",  
      "read_by": ["550e8400-e29b-41d4-a716-446655440001"],  
      "read_count": 1,  
      "is_read_by_me": true  
    }  
  ],  
  "total": 1,  
  "page": 1,  
  "size": 50  
}

---

**Редактирование сообщения:**

PUT /api/v1/chats/messages/456e7890-f12a-34b5-c678-901234567890  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "content": "Привет! Как твои дела?"  
}

---

**Отметка сообщений как прочитанных:**

POST /api/v1/chats/123e4567-e89b-12d3-a456-426614174000/read  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "message_ids": [  
    "456e7890-f12a-34b5-c678-901234567890",  
    "567f8901-23b4-45c6-d789-012345678901"  
  ]  
}

---

**Статус прочтения сообщения:**

GET /api/v1/chats/messages/456e7890-f12a-34b5-c678-901234567890/read-status?chat_id=123e4567-e89b-12d3-a456-426614174000  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "message_id": "456e7890-f12a-34b5-c678-901234567890",  
  "read_by_users": [  
    {  
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",  
      "display_name": "Jane Smith",  
      "avatar_url": "/media/avatar/550e8400.../thumbnail?avatar_id=...",  
      "read_at": "2026-01-15T10:46:00"  
    }  
  ],  
  "total_read_count": 1  
}

---

### Участники (`/api/v1/chats`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/chats/{chat_id}/participants/{user_id}` | Добавление участника (группа) |
| DELETE | `/chats/{chat_id}/participants/{user_id}` | Удаление участника (группа) |

---

### WebSocket API

**Подключение:**

ws://localhost:8005/ws?token=<internal_token>

**Альтернатива (через API Gateway):**

ws://localhost:8000/ws?token=<keycloak_token>

#### Сообщения WebSocket

**Подписка на чат:**

{  
  "type": "subscribe",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000"  
}

**Отписка от чата:**

{  
  "type": "unsubscribe",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000"  
}

**Индикатор набора текста:**

{  
  "type": "typing",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "is_typing": true  
}

**Подтверждение прочтения:**

{  
  "type": "read_receipt",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "message_id": "456e7890-f12a-34b5-c678-901234567890"  
}

**Ping (heartbeat):**

{  
  "type": "ping"  
}

#### Входящие сообщения от сервера

**Новое сообщение:**

{  
  "type": "message",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "message": {  
    "id": "456e7890-f12a-34b5-c678-901234567890",  
    "content": "Привет!",  
    "sender_id": "550e8400-e29b-41d4-a716-446655440001",  
    "sender_display_name": "Jane Smith",  
    "created_at": "2026-01-15T10:45:00"  
  },  
  "sender_id": "550e8400-e29b-41d4-a716-446655440001",  
  "timestamp": "2026-01-15T10:45:00"  
}

**Подтверждение прочтения:**

{  
  "type": "read_receipt",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "user_id": "550e8400-e29b-41d4-a716-446655440001",  
  "message_id": "456e7890-f12a-34b5-c678-901234567890",  
  "read_at": "2026-01-15T10:46:00"  
}

---

### Переменные окружения

#### Chat Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__DEBUG` | Режим отладки | `true` |
| `CHAT__SERVICE_NAME` | Имя сервиса | `chat-service` |

#### PostgreSQL Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__POSTGRES__USER` | Пользователь PostgreSQL | `chat_user` |
| `CHAT__POSTGRES__PASSWORD` | Пароль PostgreSQL | `chat_password` |
| `CHAT__POSTGRES__HOST` | Хост PostgreSQL | `chat-postgres` |
| `CHAT__POSTGRES__PORT` | Порт PostgreSQL | `5432` |
| `CHAT__POSTGRES__NAME` | Название БД | `chat_db` |
| `CHAT__POSTGRES__ECHO` | Логирование SQL | `false` |
| `CHAT__POSTGRES__POOL_SIZE` | Размер пула соединений | `20` |
| `CHAT__POSTGRES__MAX_OVERFLOW` | Макс. переполнение пула | `10` |

#### MongoDB Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__MONGO__HOST` | Хост MongoDB | `chat-mongo` |
| `CHAT__MONGO__PORT` | Порт MongoDB | `27017` |
| `CHAT__MONGO__DATABASE` | Название БД | `chat` |

#### Redis Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__REDIS__URL` | URL Redis | `redis://redis:6379/1` |

#### WebSocket Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__WEBSOCKET__TIMEOUT` | Таймаут WebSocket (сек) | `300` |
| `CHAT__WEBSOCKET__MESSAGE_RATE_LIMIT` | Rate limit сообщений | `10` |
| `CHAT__WEBSOCKET__MESSAGE_RATE_WINDOW` | Окно rate limit (сек) | `60` |

#### External Services

| Переменная | Описание | Пример |
|------------|----------|--------|
| `CHAT__USER_SERVICE_URL` | URL user-service | `http://user-service:8002` |
| `CHAT__PROFILE_SERVICE_URL` | URL profile-service | `http://profile-service:8003` |

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

**chat-service/** — сервис чатов

- **app/** — основной код приложения
  - **api/v1/** — версионированные API эндпоинты
    - `chats.py` — эндпоинты чатов и сообщений
  - **core/** — ядро сервиса
    - `config.py` — конфигурация сервиса
    - `logger.py` — настройка логирования
    - `exceptions.py` — кастомные исключения
    - `exception_handlers.py` — обработчики исключений
  - **database/** — работа с базами данных
    - **postgres/** — PostgreSQL
      - `models.py` — модели PostgreSQL (Chat, Message, Participant)
      - `session.py` — настройка сессии БД
    - **mongo/** — MongoDB
      - `session.py` — настройка MongoDB
  - **schemas/** — Pydantic схемы
    - `chat.py` — схемы чатов
  - **services/** — бизнес-логика и внешние сервисы
    - `chat_service.py` — основной сервис чатов
    - `websocket_manager.py` — управление WebSocket соединениями
    - `user_service_client.py` — клиент для user-service
    - `profile_service_client.py` — клиент для profile-service
    - `matching_service_client.py` — клиент для matching-service
    - `event_service.py` — публикация событий
    - `rabbitmq.py` — настройка RabbitMQ
  - **consumers/** — обработчики сообщений
    - `match_consumers.py` — обработчики событий от matching-service
    - `profile_consumers.py` — обработчики событий от profile-service
    - `user_consumers.py` — обработчики событий от user-service
  - **websocket/** — WebSocket обработка
    - `routes.py` — WebSocket эндпоинты
  - `dependencies.py` — зависимости FastAPI
  - `main.py` — точка входа FastAPI

- **Dockerfile** — инструкция для сборки Docker образа
- **requirements.txt** — зависимости Python
- **README.md** — документация сервиса

---

### Модели данных

#### PostgreSQL (метаданные)

**Chat:**
- `id` (UUID) — идентификатор чата
- `type` (direct/group) — тип чата
- `status` (active/archived/blocked) — статус
- `name`, `description`, `avatar_url`
- `match_id` — связь с матчем (опционально)

**ChatParticipant:**
- `chat_id`, `keycloak_id`
- `display_name`, `username`
- `joined_at`, `left_at`
- `is_admin`, `notifications_enabled`
- `avatar_url`

**Message:**
- `id`, `chat_id`, `sender_keycloak_id`
- `content`, `message_type`, `status`
- `is_edited`, `reply_to_id`
- `media_url`, `media_type`, `file_size`
- `created_at`, `updated_at`

**MessageReadStatus:**
- `message_id`, `keycloak_id`
- `read_at`

#### MongoDB (сообщения для поиска)

{  
  "message_id": "456e7890-f12a-34b5-c678-901234567890",  
  "chat_id": "123e4567-e89b-12d3-a456-426614174000",  
  "sender_id": "550e8400-e29b-41d4-a716-446655440000",  
  "sender_display_name": "John Doe",  
  "sender_username": "john_doe",  
  "content": "Привет! Как дела?",  
  "message_type": "text",  
  "created_at": "2026-01-15T10:45:00",  
  "updated_at": "2026-01-15T10:45:00",  
  "is_edited": false  
}

---

### События RabbitMQ

#### Отправляемые события

| Событие | Описание |
|---------|----------|
| `USER_ONLINE` | Пользователь стал онлайн |
| `USER_OFFLINE` | Пользователь стал офлайн |
| `USER_HEARTBEAT` | Heartbeat пользователя |

#### Получаемые события

| Событие | Источник | Действие |
|---------|----------|----------|
| `MATCH_CREATED` | matching-service | Создание личного чата для матча |
| `USER_PROFILE_UPDATED` | profile-service | Обновление display_name |
| `AVATAR_UPLOADED` | media-service | Обновление avatar_url |
| `AVATAR_UPDATED` | media-service | Смена текущей аватарки |
| `AVATAR_DELETED` | media-service | Удаление аватарки |
| `USER_DELETED` | user-service | Удаление пользователя из чатов |

---

### Запуск сервиса

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# Запуск через Docker
docker build -t briolin-chat-service .
docker run -p 8005:8005 briolin-chat-service
