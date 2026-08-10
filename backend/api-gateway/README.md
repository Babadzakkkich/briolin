# API Gateway Service

API Gateway — это единая точка входа для всех клиентских запросов в системе Briolin. Он проксирует REST запросы к соответствующим микросервисам, обрабатывает WebSocket соединения для чатов и выполняет аутентификацию через JWT токены.

## Описание сервиса

**Основные функции:**
- Проксирование HTTP запросов к бэкенд-сервисам
- Аутентификация и авторизация через Keycloak (JWT)
- Управление внутренними JWT токенами для межсервисного взаимодействия
- WebSocket прокси для чатов
- Кэширование токенов в Redis
- Маршрутизация запросов на основе пути

**Технологии:**
- FastAPI
- HTTPX (асинхронный HTTP клиент)
- Keycloak (аутентификация)
- Redis (кэширование токенов)
- WebSockets (чат в реальном времени)

## API Endpoints

### Аутентификация (`/api/v1/auth`)

 POST  `/auth/register` Регистрация нового пользователя
 POST  `/auth/login` Вход в систему
 POST  `/auth/refresh` Обновление access токена
 POST  `/auth/logout` Выход из системы
 POST  `/auth/validate` Валидация токена
 POST  `/auth/verify/request` Запрос кода верификации email
 POST  `/auth/verify/confirm` Подтверждение email по коду
 POST  `/auth/password-reset/request` Запрос сброса пароля
 POST `/auth/password-reset/confirm` Подтверждение сброса пароля

#### Примеры запросов

**Регистрация:**
POST /api/v1/auth/register
Content-Type: application/json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!"
}
ответ 
{
  "id": 1,
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true
}

Логин:
POST /api/v1/auth/login
Content-Type: application/json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
Ответ:
json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC...",
  "token_type": "Bearer",
  "expires_in": 300,
  "refresh_expires_in": 1800
}

Пользователи (/api/v1/users)
GET	/users/me	Получение информации о текущем пользователе
GET	/users/{keycloak_id}	Получение пользователя по ID
GET	/users/	Список пользователей (админ)
PUT	/users/{keycloak_id}	Обновление пользователя
DELETE	/users/{keycloak_id}	Удаление пользователя (админ)
Примеры запросов
Получение своего профиля:
GET /api/v1/users/me
Authorization: Bearer <access_token>
json
{
  "id": 1,
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "user@example.com",
  "roles": ["user"],
  "is_active": true,
  "is_test_passed": false,
  "created_at": "2026-01-15T10:30:00"
}

Профили (/api/v1/profiles)
Метод	Эндпоинт	Описание
POST	/profiles/basic	Создание базового профиля
POST	/profiles/detailed	Создание детального профиля
GET	/profiles/me	Получение своего профиля
PUT	/profiles/me	Обновление профиля
DELETE	/profiles/me	Удаление профиля
POST	/profiles/me/questions	Создание вопросов
GET	/profiles/me/questions	Получение своих вопросов
Примеры запросов
Создание базового профиля:
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
Ответ:
json
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
    "created_at": "2026-01-15T10:35:00",
    "updated_at": "2026-01-15T10:35:00"
  },
  "detailed": null,
  "questions": null
}

Чаты (/api/v1/chats)
Метод	Эндпоинт	Описание
GET	/chats/	Список чатов пользователя
POST	/chats/	Создание чата
GET	/chats/{chat_id}	Получение чата
POST	/chats/{chat_id}/messages	Отправка сообщения
GET	/chats/{chat_id}/messages	Получение сообщений
Примеры запросов
Создание личного чата:
POST /api/v1/chats/
Authorization: Bearer <access_token>
Content-Type: application/json
{
  "type": "direct",
  "participant_ids": ["550e8400-e29b-41d4-a716-446655440001"]
}
Ответ:
json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "type": "direct",
  "status": "active",
  "name": "Jane Smith",
  "participants": [
    {
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
      "display_name": "John Doe",
      "is_admin": true
    },
    {
      "keycloak_id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "Jane Smith",
      "is_admin": false
    }
  ],
  "created_at": "2026-01-15T10:40:00",
  "unread_count": 0
}

Matching (/api/v1/matching)
Метод	Эндпоинт	Описание
POST	/matching/like	Лайк профиля (deprecated)
POST	/matching/like-with-answers	Лайк с ответами на вопросы
POST	/matching/dislike	Дизлайк профиля
GET	/matching/matches	Список матчей
GET	/matching/search/classic	Классический поиск
GET	/matching/recommendations/targeted	Таргетированные рекомендации
Примеры запросов
Лайк с ответами:
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
Ответ при матче:
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
    "partner_answers": {
      "question_1": "Чтение книг и прогулки",
      "question_2": "В большинстве случаев да"
    }
  }
}

Media (/api/v1/media)
Метод	Эндпоинт	Описание
POST	/media/avatar	Загрузка аватарки
GET	/media/my-avatar	Получение своей аватарки
GET	/media/avatars	Список своих аватарок
PUT	/media/avatar/{id}/set-current	Установка текущей аватарки
DELETE	/media/my-avatar	Удаление текущей аватарки
Примеры запросов
Загрузка аватарки:
POST /api/v1/media/avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
file: @avatar.jpg
Ответ:
json
{
  "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
  "url": "/media/avatar/550e8400-e29b-41d4-a716-446655440000?avatar_id=123e4567-e89b-12d3-a456-426614174000",
  "thumbnail_url": "/media/avatar/550e8400-e29b-41d4-a716-446655440000/thumbnail?avatar_id=123e4567-e89b-12d3-a456-426614174000",
  "width": 1024,
  "height": 1024,
  "file_size": 245760
}

Переменные окружения
Gateway Config
GATEWAY__HOST	Хост для запуска сервиса	0.0.0.0
GATEWAY__PORT	Порт для запуска сервиса	8000
GATEWAY__DEBUG	Режим отладки	true
GATEWAY__SERVICE_NAME	Имя сервиса	api-gateway

Gateway Keycloak Client
GATEWAY__KEYCLOAK__CLIENT_ID	Client ID в Keycloak	briolin-gateway
GATEWAY__KEYCLOAK__CLIENT_SECRET	Client Secret в Keycloak	your-client-secret

Services URLs
SERVICES__AUTH	URL auth-service	http://auth-service:8001
SERVICES__USER	URL user-service	http://user-service:8002
SERVICES__PROFILE	URL profile-service	http://profile-service:8003
SERVICES__TESTING	URL testing-service	http://testing-service:8004
SERVICES__CHAT	URL chat-service	http://chat-service:8005
SERVICES__CHAT_WS	WebSocket URL chat-service	ws://chat-service:8005
SERVICES__MEDIA	URL media-service	http://media-service:8007
SERVICES__MATCHING	URL matching-service	http://matching-service:8006

Cache Config
CACHE__REDIS_URL	URL для подключения к Redis	redis://redis:6379/0
CACHE__USER_CACHE_TTL	TTL кэша пользователя (сек)	60
CACHE__TOKEN_CACHE_TTL_BUFFER	Буфер TTL токена (сек)	30

Shared Config
KEYCLOAK__SERVER_URL	URL Keycloak сервера	http://keycloak:8080
KEYCLOAK__REALM	Realm в Keycloak	briolin
RABBITMQ__HOST	Хост RabbitMQ	rabbitmq
RABBITMQ__PORT	Порт RabbitMQ	5672
RABBITMQ__USER	Пользователь RabbitMQ	guest
RABBITMQ__PASSWORD	Пароль RabbitMQ	guest
RABBITMQ__VHOST	VHost RabbitMQ	/
SHARED__JWT_SECRET	Секрет для JWT	your-jwt-secret
SHARED__JWT_ALGORITHM	Алгоритм JWT	HS256
SHARED__JWT_ISSUER	Issuer JWT	briolin
SHARED__JWT_AUDIENCE	Audience JWT	briolin-api
SHARED__JWT_EXPIRE_MINUTES	Время жизни JWT (мин)	5

Структура проекта
api-gateway/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Эндпоинты аутентификации
│   │       ├── users.py         # Эндпоинты пользователей
│   │       ├── profiles.py      # Эндпоинты профилей
│   │       ├── chats.py         # Эндпоинты чатов
│   │       ├── matching.py      # Эндпоинты матчинга
│   │       ├── media.py         # Эндпоинты медиа
│   │       ├── tests.py         # Эндпоинты тестов
│   │       └── endpoints.py     # Регистрация всех роутов
│   ├── core/
│   │   ├── config.py            # Конфигурация сервиса
│   │   ├── logger.py            # Настройка логирования
│   │   ├── exceptions.py        # Кастомные исключения
│   │   └── exception_handlers.py # Обработчики исключений
│   ├── middleware/
│   │   └── auth_middleware.py   # JWT аутентификация
│   ├── services/
│   │   ├── http_client.py       # HTTP клиент для проксирования
│   │   ├── keycloak_client.py   # Клиент для Keycloak
│   │   ├── auth_service_client.py # Клиент для auth-service
│   │   └── token_cache.py       # Кэширование токенов в Redis
│   ├── schemas/
│   │   ├── auth.py              # Схемы аутентификации
│   │   ├── user.py              # Схемы пользователей
│   │   ├── profile.py           # Схемы профилей
│   │   ├── chat.py              # Схемы чатов
│   │   ├── matching.py          # Схемы матчинга
│   │   ├── media.py             # Схемы медиа
│   │   └── test.py              # Схемы тестов
│   ├── websocket/
│   │   ├── proxy.py             # WebSocket прокси
│   │   └── routes.py            # WebSocket эндпоинты
│   └── main.py                  # Точка входа FastAPI
├── Dockerfile
├── requirements.txt
└── README.md

Запуск сервиса

# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Запуск через Docker
docker build -t briolin-api-gateway .
docker run -p 8000:8000 briolin-api-gateway