# Media Service

Сервис для загрузки, хранения и обработки медиафайлов в системе Briolin. Отвечает за управление аватарками пользователей, их обработку и хранение в MinIO.

## Описание сервиса

**Основные функции:**
- Загрузка аватарок пользователей
- Обработка изображений (конвертация в WebP, ресайз)
- Создание thumbnail (уменьшенных копий)
- Управление текущей аватаркой пользователя
- Хранение файлов в MinIO (S3-совместимое хранилище)
- Поддержка форматов: JPEG, PNG, WebP, GIF
- Максимальный размер файла: 5MB
- Максимум 10 аватарок на пользователя
- Soft delete с возможностью восстановления

**Технологии:**
- FastAPI
- MinIO (S3-совместимое хранилище)
- Pillow (обработка изображений)
- PostgreSQL (метаданные аватарок)
- RabbitMQ (публикация событий об изменениях)

## API Endpoints

### Аватарки (`/api/v1/media`)
 POST  `/media/avatar`  Загрузка новой аватарки 
 GET  `/media/my-avatar`  Получение текущей аватарки (изображение) 
 GET  `/media/my-thumbnail`  Получение thumbnail текущей аватарки 
 GET  `/media/avatars`  Список всех аватарок пользователя 
 PUT  `/media/avatar/{id}/set-current`  Установка текущей аватарки 
 GET  `/media/avatar/{keycloak_id}`  Получение аватарки пользователя 
 GET  `/media/avatar/{keycloak_id}/thumbnail`  Получение thumbnail 
 DELETE  `/media/my-avatar`  Удаление текущей аватарки 
 DELETE  `/media/avatar`  Удаление аватарки по ID 
 DELETE  `/media/avatar/{id}/permanent`  Полное удаление (админ) 

#### Примеры запросов

**Загрузка аватарки:**
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

Получение текущей аватарки:
GET /api/v1/media/my-avatar
Authorization: Bearer <access_token>
Ответ: возвращает изображение (image/webp)
Список аватарок:
GET /api/v1/media/avatars?include_deleted=false&limit=20&offset=0
Authorization: Bearer <access_token>
Ответ:
json
[
  {
    "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
    "url": "/media/avatar/550e8400-e29b-41d4-a716-446655440000?avatar_id=123e4567-e89b-12d3-a456-426614174000",
    "thumbnail_url": "/media/avatar/550e8400-e29b-41d4-a716-446655440000/thumbnail?avatar_id=123e4567-e89b-12d3-a456-426614174000",
    "width": 1024,
    "height": 1024,
    "file_size": 245760,
    "is_current": true,
    "created_at": "2026-01-15T10:30:00",
    "file_name": "avatar.jpg"
  }
]

Установка текущей аватарки:
PUT /api/v1/media/avatar/123e4567-e89b-12d3-a456-426614174000/set-current
Authorization: Bearer <access_token>
Ответ:
json
{
  "message": "Current avatar updated"
}

Удаление текущей аватарки:
DELETE /api/v1/media/my-avatar
Authorization: Bearer <access_token>
Ответ:
json
{
  "deleted": true,
  "avatar_id": "123e4567-e89b-12d3-a456-426614174000"
}

Получение аватарки другого пользователя:
GET /api/v1/media/avatar/550e8400-e29b-41d4-a716-446655440001?avatar_id=123e4567-e89b-12d3-a456-426614174001
Authorization: Bearer <access_token>
Ответ: возвращает изображение (image/webp)

Полное удаление аватарки (админ):
DELETE /api/v1/media/avatar/123e4567-e89b-12d3-a456-426614174000/permanent
Authorization: Bearer <access_token>
Ответ:
json
{
  "message": "Avatar permanently deleted"
}

Внутренние эндпоинты (/api/v1/internal)
GET	/internal/avatars/{keycloak_id}	Получение информации об аватарке (для других сервисов)

Переменные окружения
Media Service Config
MEDIA__DEBUG	Режим отладки	false
MEDIA__SERVICE_NAME	Имя сервиса	media-service
MEDIA__HOST	Хост для запуска	0.0.0.0
MEDIA__PORT	Порт для запуска	8007
MEDIA__MAX_FILE_SIZE	Максимальный размер файла (байт)	5242880 (5MB)
MEDIA__ALLOWED_MIME_TYPES	Разрешённые MIME-типы	image/jpeg,image/png,image/webp,image/gif
MEDIA__AVATAR_SIZE	Размер аватарки (пиксели)	1024
MEDIA__THUMBNAIL_SIZE	Размер thumbnail (пиксели)	200
MEDIA__MAX_AVATARS_PER_USER	Максимум аватарок на пользователя	10

Database Config
MEDIA__DB__USER	Пользователь PostgreSQL	media_user
MEDIA__DB__PASSWORD	Пароль PostgreSQL	media_password
MEDIA__DB__HOST	Хост PostgreSQL	media-postgres
MEDIA__DB__PORT	Порт PostgreSQL	5432
MEDIA__DB__NAME	Название БД	media_db
MEDIA__DB__ECHO	Логирование SQL	false
MEDIA__DB__POOL_SIZE	Размер пула соединений	20
MEDIA__DB__MAX_OVERFLOW	Макс. переполнение пула	10

MinIO Config
MINIO__ENDPOINT	MinIO эндпоинт	minio:9000
MINIO__ACCESS_KEY	Access Key MinIO	minioadmin
MINIO__SECRET_KEY	Secret Key MinIO	minioadmin
MINIO__BUCKET_AVATARS	Название bucket для аватарок	avatars
MINIO__SECURE	Использовать HTTPS	false
MINIO__REGION	Регион MinIO	us-east-1

Структура проекта
media-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── media.py              # Основные эндпоинты
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
│   │   └── media.py                  # Pydantic схемы
│   ├── services/
│   │   ├── media_service.py          # Основной сервис медиа
│   │   ├── minio_client.py           # Клиент для MinIO
│   │   ├── image_processor.py        # Обработка изображений
│   │   ├── event_service.py          # Публикация событий
│   │   └── rabbitmq.py               # Настройка RabbitMQ
│   ├── dependencies.py               # Зависимости FastAPI
│   └── main.py                       # Точка входа FastAPI
├── Dockerfile
├── requirements.txt
└── README.md

Модели данных
Avatar (PostgreSQL)
sql
- id (VARCHAR(36)) — UUID аватарки
- keycloak_id (VARCHAR(255)) — ID пользователя (индекс)
- file_name (VARCHAR(255)) — оригинальное имя файла
- file_size (INTEGER) — размер в байтах
- width (INTEGER) — ширина изображения
- height (INTEGER) — высота изображения
- original_path (VARCHAR(500)) — путь в MinIO
- thumbnail_path (VARCHAR(500)) — путь к thumbnail в MinIO
- is_current (BOOLEAN) — является ли текущей (индекс)
- is_deleted (BOOLEAN) — мягкое удаление (индекс)
- created_at (TIMESTAMP) — дата загрузки (индекс)

Обработка изображений
Процесс обработки аватарки
Загрузка файла — проверка размера и MIME-типа
Открытие изображения — через Pillow
Создание квадратного изображения:
Сохранение пропорций
Добавление размытого фона для неквадратных изображений
Размер: 1024x1024 пикселя
Конвертация в WebP — качество 85%, оптимизация
Сохранение в MinIO — путь: avatars/{keycloak_id}/{avatar_id}/original.webp
Создание thumbnail — ресайз до 200x200 пикселей, WebP, качество 75%
Сохранение thumbnail — путь: avatars/{keycloak_id}/{avatar_id}/thumbnail.webp
Сохранение метаданных в PostgreSQL
Публикация события в RabbitMQ (для chat-service, profile-service)
Поддерживаемые форматы
JPEG, PNG, WebP, GIF	

События RabbitMQ
Отправляемые события
AVATAR_UPLOADED	Загружена новая аватарка (is_current=true)	profile-service, chat-service
AVATAR_UPDATED	Смена текущей аватарки	profile-service, chat-service
AVATAR_DELETED	Удаление аватарки (soft delete)	profile-service, chat-service

Формат событий
AVATAR_UPLOADED:
json
{
  "event_type": "avatar.uploaded",
  "user_data": {
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
    "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
    "url": "/media/avatar/550e8400...",
    "thumbnail_url": "/media/avatar/550e8400.../thumbnail",
    "width": 1024,
    "height": 1024,
    "file_size": 245760,
    "is_current": true
  }
}

AVATAR_UPDATED:
json
{
  "event_type": "avatar.updated",
  "user_data": {
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
    "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
    "is_current": true
  }
}

AVATAR_DELETED:
json
{
  "event_type": "avatar.deleted",
  "user_data": {
    "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
    "avatar_id": "123e4567-e89b-12d3-a456-426614174000",
    "is_current": true
  }
}

Потоки работы
Загрузка аватарки
1. Валидация файла (размер, MIME-тип)
2. Проверка лимита аватарок (макс. 10)
3. Обработка изображения (конвертация в WebP, ресайз)
4. Загрузка оригинального изображения в MinIO
5. Создание thumbnail
6. Загрузка thumbnail в MinIO
7. Сброс флага is_current у всех аватарок пользователя
8. Сохранение метаданных в PostgreSQL
9. Публикация события AVATAR_UPLOADED

Удаление аватарки
1. Поиск аватарки в БД
2. Soft delete (is_deleted = True, is_current = False)
3. Если удаляется текущая аватарка → выбор следующей по дате загрузки
4. Публикация события AVATAR_DELETED

Смена текущей аватарки
1. Сброс флага is_current у всех аватарок пользователя
2. Установка флага is_current = True для выбранной аватарки
3. Публикация события AVATAR_UPDATED

Запуск сервиса
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload

# Запуск через Docker
docker build -t briolin-media-service .
docker run -p 8007:8007 briolin-media-service