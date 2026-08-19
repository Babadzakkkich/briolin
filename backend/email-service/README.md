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

### Примеры запросов

**Отправка email:**

POST /api/v1/email/send  
Content-Type: application/json  

{  
  "to": "user@example.com",  
  "subject": "Приветствие",  
  "body": "Добро пожаловать в Briolin!",  
  "html_body": "<h1>Добро пожаловать в Briolin!</h1><p>Мы рады видеть вас.</p>"  
}

**Ответ:**

{  
  "success": true,  
  "message": "Email sent",  
  "to": "user@example.com"  
}

---

**Отправка с шаблоном:**

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

---

**Список шаблонов:**

GET /api/v1/email/templates

**Ответ:**

{  
  "templates": ["welcome", "login", "verification", "password_reset", "password_reset_confirmation", "test_results"]  
}

---

### Типы email-шаблонов

| Шаблон | Описание | Переменные |
|--------|----------|------------|
| `welcome` | Приветственное письмо | `name` |
| `login` | Уведомление о входе | `name`, `timestamp` |
| `verification` | Код верификации email | `name`, `code` |
| `password_reset` | Код сброса пароля | `name`, `code` |
| `password_reset_confirmation` | Подтверждение сброса пароля | `name`, `timestamp` |
| `test_results` | Результаты психологического теста | `name`, `test_name`, `score`, `total`, `percentage` |

---

### Пример шаблона (verification.html)

```html
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
