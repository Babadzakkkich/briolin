# Auth Service

Сервис аутентификации и авторизации в системе Briolin. Управляет пользователями через Keycloak, обрабатывает регистрацию, вход, обновление токенов, верификацию email и восстановление пароля.

## Описание сервиса

**Основные функции:**
- Регистрация новых пользователей (синхронная)
- Аутентификация (логин) через Keycloak
- Обновление access/refresh токенов
- Выход из системы (logout)
- Верификация email через код подтверждения
- Восстановление пароля
- Управление пользователями в auth-db (связь keycloak_id ↔ user_id)
- Асинхронное обновление данных пользователя через SAGA паттерн

**Технологии:**
- FastAPI
- Keycloak (управление пользователями и аутентификация)
- PostgreSQL (хранение связей пользователей)
- Redis (хранение кодов верификации)
- RabbitMQ (асинхронное взаимодействие)
- SAGA паттерн (распределённые транзакции)

## API Endpoints

### Аутентификация (`/api/v1/auth`)

 POST  `/auth/register`  Регистрация нового пользователя 
 POST  `/auth/login`  Вход в систему 
 POST  `/auth/refresh`  Обновление токена 
 POST  `/auth/logout`  Выход из системы 
 POST  `/auth/validate`  Валидация токена 

### Аутентификация (`/api/v1/auth`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/auth/register` | Регистрация нового пользователя |
| POST | `/auth/login` | Вход в систему |
| POST | `/auth/refresh` | Обновление токена |
| POST | `/auth/logout` | Выход из системы |
| POST | `/auth/validate` | Валидация токена |

#### Примеры запросов

**Регистрация:**

POST /api/v1/auth/register  
Content-Type: application/json  

{  
  "email": "user@example.com",  
  "username": "john_doe",  
  "password": "SecurePass123!"  
}

**Ответ:**

{  
  "id": 1,  
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
  "email": "user@example.com",  
  "is_active": true  
}

---

**Логин:**

POST /api/v1/auth/login  
Content-Type: application/json  

{  
  "username": "john_doe",  
  "password": "SecurePass123!"  
}

**Ответ:**

{  
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC...",  
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC...",  
  "token_type": "Bearer",  
  "expires_in": 300,  
  "refresh_expires_in": 1800  
}

**Обновление токена:**

POST /api/v1/auth/refresh  
Content-Type: application/json  

{  
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC..."  
}

**Выход:**

POST /api/v1/auth/logout  
Content-Type: application/json  

{  
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6IC..."  
}

---

### Верификация email (`/api/v1/auth`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/auth/verify/request` | Запрос кода верификации |
| POST | `/auth/verify/confirm` | Подтверждение email по коду |

#### Примеры запросов

**Запрос кода верификации:**

POST /api/v1/auth/verify/request  
Authorization: Bearer <access_token>

**Ответ:**

{  
  "status": "success",  
  "message": "Verification code sent to user@example.com",  
  "expires_in_minutes": 15  
}

**Подтверждение email:**

POST /api/v1/auth/verify/confirm  
Authorization: Bearer <access_token>  
Content-Type: application/json  

{  
  "code": "123456"  
}

**Ответ:**

{  
  "status": "success",  
  "message": "Email verified successfully",  
  "email_verified": true  
}

---

### Восстановление пароля (`/api/v1/auth`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/auth/password-reset/request` | Запрос сброса пароля |
| POST | `/auth/password-reset/confirm` | Подтверждение сброса пароля |

#### Примеры запросов

**Запрос сброса пароля:**

POST /api/v1/auth/password-reset/request  
Content-Type: application/json  

{  
  "email": "user@example.com"  
}

**Ответ:**

{  
  "status": "success",  
  "message": "If an account exists with this email, you will receive a password reset code.",  
  "expires_in_minutes": 15  
}

**Подтверждение сброса пароля:**

POST /api/v1/auth/password-reset/confirm  
Content-Type: application/json  

{  
  "email": "user@example.com",  
  "code": "123456",  
  "new_password": "NewSecurePass123!"  
}

**Ответ:**

{  
  "status": "success",  
  "message": "Password has been reset successfully. You can now log in with your new password."  
}

---

### Внутренние эндпоинты (`/api/v1/internal`)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/internal/users/{keycloak_id}` | Получение информации о пользователе |
| GET | `/internal/users/{keycloak_id}/active` | Проверка активности пользователя |
| GET | `/internal/users/{keycloak_id}/exists` | Проверка существования пользователя |
| PATCH | `/internal/users/{keycloak_id}` | Обновление пользователя в auth-db |
| DELETE | `/internal/users/{keycloak_id}` | Удаление пользователя из auth-db |

#### Примеры запросов

**Получение информации о пользователе:**

GET /api/v1/internal/users/550e8400-e29b-41d4-a716-446655440000  
X-Internal-Request: true

**Ответ:**

{  
  "id": 1,  
  "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",  
  "email": "user@example.com",  
  "is_active": true,  
  "created_at": "2026-01-15T10:30:00"  
}

---

### Переменные окружения

#### Auth Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `AUTH__DEBUG` | Режим отладки | `true` |
| `AUTH__SERVICE_NAME` | Имя сервиса | `auth-service` |

#### Database Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `AUTH__DB__USER` | Пользователь PostgreSQL | `auth_user` |
| `AUTH__DB__PASSWORD` | Пароль PostgreSQL | `auth_password` |
| `AUTH__DB__HOST` | Хост PostgreSQL | `auth-postgres` |
| `AUTH__DB__PORT` | Порт PostgreSQL | `5432` |
| `AUTH__DB__NAME` | Название БД | `auth_db` |
| `AUTH__DB__ECHO` | Логирование SQL | `false` |
| `AUTH__DB__POOL_SIZE` | Размер пула соединений | `50` |
| `AUTH__DB__MAX_OVERFLOW` | Макс. переполнение пула | `10` |

#### Keycloak Client Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `AUTH__KEYCLOAK__CLIENT_ID` | Client ID в Keycloak | `briolin-auth` |
| `AUTH__KEYCLOAK__CLIENT_SECRET` | Client Secret в Keycloak | `your-client-secret` |
| `AUTH__KEYCLOAK__DEFAULT_ROLE` | Роль по умолчанию | `user` |

#### User Service Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `AUTH__USER_SERVICE__URL` | URL user-service | `http://user-service:8002` |

#### Redis Config

| Переменная | Описание | Пример |
|------------|----------|--------|
| `REDIS__HOST` | Хост Redis | `redis` |
| `REDIS__PORT` | Порт Redis | `6379` |
| `REDIS__DB` | Номер БД Redis | `0` |
| `REDIS__PASSWORD` | Пароль Redis | `` |

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

**auth-service/** — сервис аутентификации

- **app/** — основной код приложения
  - **api/v1/** — версионированные API эндпоинты
    - `auth.py` — эндпоинты аутентификации
    - `internal.py` — внутренние эндпоинты
    - `verification.py` — эндпоинты верификации
  - **core/** — ядро сервиса
    - `config.py` — конфигурация сервиса
    - `logger.py` — настройка логирования
    - `exceptions.py` — кастомные исключения
    - `exception_handlers.py` — обработчики исключений
  - **database/** — работа с базой данных
    - `models.py` — модели PostgreSQL (User)
    - `session.py` — настройка сессии БД
  - **schemas/** — Pydantic схемы
    - `auth.py` — схемы аутентификации
    - `verify.py` — схемы верификации
  - **services/** — бизнес-логика и внешние сервисы
    - `auth_service.py` — основной сервис аутентификации
    - `keycloak_client.py` — клиент для Keycloak
    - `verification_service.py` — сервис верификации (Redis)
    - `user_service_client.py` — клиент для user-service
    - `event_service.py` — публикация событий
    - `rabbitmq.py` — настройка RabbitMQ
    - `saga_handlers.py` — обработчики SAGA шагов
    - `saga_worker.py` — SAGA воркер
  - **consumers/** — обработчики сообщений
    - `user_consumers.py` — обработчики событий от user-service
  - `dependencies.py` — зависимости FastAPI
  - `main.py` — точка входа FastAPI

- **Dockerfile** — инструкция для сборки Docker образа
- **requirements.txt** — зависимости Python
- **README.md** — документация сервиса

---

### Поток регистрации

1. **Валидация данных** — проверка email и username на уникальность
2. **Создание в Keycloak** — создание пользователя с ролью `user`
3. **Создание в auth-db** — сохранение связи `keycloak_id` ↔ `user_id`
4. **Создание в user-service** — синхронный вызов для создания профиля пользователя
5. **Отправка кода верификации** — генерация и отправка 6-значного кода на email

В случае ошибки на любом шаге выполняется компенсация (откат изменений).

---

### Поток обновления пользователя (SAGA)

При обновлении пользователя из user-service используется SAGA паттерн:

1. **user-service** публикует `USER_PROFILE_UPDATE_REQUESTED`
2. **auth-service** получает событие и выполняет шаги:
   - Обновление пользователя в Keycloak
   - Обновление пользователя в auth-db
   - Публикация `USER_PROFILE_UPDATED` (подтверждение)
3. В случае ошибки выполняется компенсация (откат)

Запуск сервиса  

Установка зависимостей  
pip install -r requirements.txt  

Запуск в режиме разработки  
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload  

Запуск через Docker  
docker build -t briolin-auth-service .  
docker run -p 8001:8001 briolin-auth-service  
