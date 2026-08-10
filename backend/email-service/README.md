# Email Service

Сервис для отправки email-уведомлений в системе Briolin. Получает задачи через RabbitMQ, поддерживает шаблоны писем и отправляет их через SMTP.

## Описание сервиса

**Основные функции:**
- Отправка email через SMTP
- Поддержка HTML-шаблонов писем
- Асинхронное получение задач через RabbitMQ
- Различные типы писем: приветствие, верификация, восстановление пароля, результаты теста
- Поддержка текстовой и HTML-версии писем

**Технологии:**
- FastAPI
- smtplib (SMTP клиент)
- RabbitMQ (получение задач)
- Jinja2-подобные шаблоны (простая замена переменных)

## API Endpoints

### Email (`/api/v1/email`)
 POST  `/email/send`  Отправка email (синхронно) 
 POST  `/email/send-template`  Отправка email с шаблоном 
 GET  `/email/templates`  Список доступных шаблонов 
 POST  `/email/test`  Тестовая отправка 

#### Примеры запросов

**Отправка email:**
POST /api/v1/email/send
Content-Type: application/json
{
  "to": "user@example.com",
  "subject": "Приветствие",
  "body": "Добро пожаловать в Briolin!",
  "html_body": "<h1>Добро пожаловать в Briolin!</h1><p>Мы рады видеть вас.</p>"
}
Ответ:
json
{
  "success": true,
  "message": "Email sent",
  "to": "user@example.com"
}

Отправка с шаблоном:
POST /api/v1/email/send-template
Content-Type: application/json
{
  "to": "user@example.com",
  "template": "welcome",
  "context": {
    "name": "John Doe",
    "code": "123456"
  }
}

Список шаблонов:
GET /api/v1/email/templates
Ответ:
json
{
  "templates": ["welcome", "login", "verification", "password_reset", "password_reset_confirmation", "test_results"]
}

Типы email-шаблонов
welcome	Приветственное письмо	name
login	Уведомление о входе	name, timestamp
verification	Код верификации email	name, code
password_reset	Код сброса пароля	name, code
password_reset_confirmation	Подтверждение сброса пароля	name, timestamp
test_results	Результаты психологического теста	name, test_name, score, total, percentage
Пример шаблона (verification.html)
html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Verification</title>
</head>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <h2>Подтверждение email</h2>
        <p>Здравствуйте, {{ name }}!</p>
        <p>Ваш код подтверждения:</p>
        <h1 style="background: #f0f0f0; padding: 20px; text-align: center; font-size: 32px;">
            {{ code }}
        </h1>
        <p>Код действителен в течение 15 минут.</p>
        <p>Если вы не запрашивали код, проигнорируйте это письмо.</p>
    </div>
</body>
</html>

RabbitMQ Consumer
Сервис автоматически подписывается на очередь email.notifications и обрабатывает входящие сообщения.
Формат сообщения
json
{
  "type": "verification",
  "to": "user@example.com",
  "name": "John Doe",
  "code": "123456"
}

Типы сообщений
welcome	Приветственное письмо	name
login	Уведомление о входе	name, timestamp
verification	Код верификации	name, code
password_reset	Код сброса пароля	name, code
password_reset_confirmation	Подтверждение сброса	name, timestamp
test_complete	Результаты теста	name, test_name, score, total, percentage

Переменные окружения
Email Service Config
EMAIL__DEBUG	Режим отладки	true
EMAIL__SERVICE_NAME	Имя сервиса	email-service
EMAIL__QUEUE_NAME	Название очереди RabbitMQ	email.notifications

SMTP Config
EMAIL__SMTP__HOST	SMTP сервер	smtp.gmail.com
EMAIL__SMTP__PORT	SMTP порт	587
EMAIL__SMTP__USER	SMTP пользователь	noreply@briolin.com
EMAIL__SMTP__PASSWORD	SMTP пароль	your-smtp-password
EMAIL__SMTP__FROM_EMAIL	Email отправителя	noreply@briolin.com
EMAIL__SMTP__USE_TLS	Использовать TLS	true

Shared Config
RABBITMQ__HOST	Хост RabbitMQ	rabbitmq
RABBITMQ__PORT	Порт RabbitMQ	5672
RABBITMQ__USER	Пользователь RabbitMQ	guest
RABBITMQ__PASSWORD	Пароль RabbitMQ	guest
RABBITMQ__VHOST	VHost RabbitMQ	/

Структура проекта
email-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── email.py              # Эндпоинты email
│   ├── core/
│   │   ├── config.py                 # Конфигурация сервиса
│   │   ├── logger.py                 # Настройка логирования
│   │   ├── exceptions.py             # Кастомные исключения
│   │   └── exception_handlers.py     # Обработчики исключений
│   ├── schemas/
│   │   └── email.py                  # Pydantic схемы
│   ├── services/
│   │   ├── email_service.py          # Основной сервис отправки email
│   │   └── consumer.py               # RabbitMQ consumer
│   ├── templates/                    # HTML-шаблоны писем
│   │   ├── welcome.html
│   │   ├── login.html
│   │   ├── verification.html
│   │   ├── password_reset.html
│   │   ├── password_reset_confirmation.html
│   │   └── test_results.html
│   ├── dependencies.py               # Зависимости FastAPI
│   └── main.py                       # Точка входа FastAPI
├── Dockerfile
├── requirements.txt
└── README.md

Пример шаблона (test_results.html)
html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Результаты теста</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #FF9800; color: white; padding: 20px; text-align: center; }
        .score { font-size: 48px; font-weight: bold; text-align: center; padding: 20px; }
        .score.passed { color: #4CAF50; }
        .score.failed { color: #f44336; }
        .footer { background: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Результаты теста</h1>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{{ name }}</strong>!</p>
            <p>Вы завершили тест <strong>"{{ test_name }}"</strong>.</p>
            <div class="score {{ 'passed' if percentage >= 70 else 'failed' }}">
                {{ percentage }}%
            </div>
            <p style="text-align: center;">
                Ваш результат: <strong>{{ score }} / {{ total }}</strong>
            </p>
            <p style="text-align: center; color: {{ '#4CAF50' if percentage >= 70 else '#f44336' }};">
                {{ 'Поздравляем! Вы прошли тест.' if percentage >= 70 else 'К сожалению, вы не прошли тест. Попробуйте снова.' }}
            </p>
        </div>
        <div class="footer">
            <p>&copy; 2026 Briolin. Все права защищены.</p>
        </div>
    </div>
</body>
</html>

Поток отправки email
Через HTTP API (синхронно)
Клиент отправляет запрос на /api/v1/email/send
Сервис подключается к SMTP
Отправляет email
Возвращает результат
Через RabbitMQ (асинхронно)
Другой сервис публикует сообщение в очередь email.notifications
Email Service получает сообщение
Выбирает шаблон на основе type
Рендерит HTML и текстовую версию
Отправляет email через SMTP
Подтверждает обработку сообщения

Запуск сервиса
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload

# Запуск через Docker
docker build -t briolin-email-service .
docker run -p 8008:8008 briolin-email-service