# Briolin — Frontend

Клиентское приложение платформы для знакомств с психологическим тестированием, умным мэтчингом и чатом в реальном времени.

---

## Статус проекта

| Область | Статус |
|---|---|
| Аутентификация (логин, регистрация, refresh) | Готово |
| Онбординг (психотест + создание профиля) | Готово |
| Профиль пользователя (базовый, расширенный, вопросы) | Готово |
| Поиск (классический и таргетированный) | Готово |
| Мэтчинг (лайки, матчи, pending likes) | Готово |
| Рекомендации (Купидон / Фортуна) | Готово |
| Мессенджер (список чатов + чат с WS) | Готово |
| Онлайн-статус в реальном времени | Готово |
| Загрузка аватара | Готово |

---

## Быстрый старт

```bash
# 1. Установить зависимости
npm install

# 2. Скопировать переменные окружения
cp .env.example .env

# 3. Запустить дев-сервер
npm run dev
# → http://localhost:5173
```

Другие команды:

```bash
npm run build    # production-сборка в dist/
npm run preview  # предпросмотр production-сборки локально
```

---

## Переменные окружения

| Переменная | Пример | Описание |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Базовый URL API-шлюза. WebSocket-соединение деривируется из него автоматически (`http` → `ws`, `https` → `wss`). |

---

## Стек

| Категория | Технология |
|---|---|
| Фреймворк | React 19 |
| Язык | TypeScript 5.9 |
| Сборщик | Vite 7 |
| Стили | Tailwind CSS v4 |
| UI-компоненты | Ark UI v5 |
| HTTP-клиент | Axios (с перехватчиком refresh) |
| Роутинг | React Router v7 |
| Состояние | Zustand v5 (с persist-middleware) |
| Формы | React Hook Form + Zod |
| Иконки | Lucide React |

---

## Архитектура папок

Проект следует **Feature-Sliced Design (FSD)**:

```
src/
├── app/
│   ├── router.tsx          # Маршруты приложения
│   └── layouts/
│       ├── AppLayout.tsx   # Корневой layout (toast-контейнер)
│       └── DashboardLayout.tsx  # Layout с сайдбаром
│
├── pages/                  # Страницы — тонкие, только компоновка
│   ├── auth/               # Login, Registration, ForgotPassword
│   ├── onboarding/         # Онбординг (тест + профиль)
│   └── dashboard/          # Все страницы после авторизации
│
├── features/               # Бизнес-фичи — содержат логику
│   ├── auth/               # AuthGuard, TestGuard, useAuth
│   ├── dashboard/          # Sidebar
│   ├── matching/           # LikeWithAnswersModal
│   ├── messaging/          # ChatList, ChatView, useChatSocket
│   ├── onboarding/         # Шаги онбординга
│   ├── profile/            # Секции редактирования профиля
│   └── search/             # Фильтры поиска
│
├── entities/               # Доменные сущности — модели, API, базовый UI
│   ├── account/            # Текущий аккаунт, роли, настройки
│   ├── admin/              # Администрирование пользователей
│   ├── session/            # Токены, store авторизации
│   ├── profile/            # Данные профиля, store
│   ├── chat/               # Чат, участники
│   ├── message/            # Сообщения, WS-события
│   ├── matching/           # Лайки, матчи, рекомендации
│   ├── search/             # Поиск профилей
│   ├── media/              # Загрузка медиа
│   └── test-session/       # Психологический тест
│
└── shared/
    ├── api/
    │   └── client.ts       # Axios-инстанс с refresh-логикой
    ├── uikit/              # Переиспользуемые UI-компоненты
    ├── toast/              # Глобальные уведомления
    ├── cards/              # Карточки
    └── icons/              # SVG-иконки
```

---

## Сценарии использования

### Регистрация и онбординг

```
Пользователь → /registration
  → POST /auth/register  (saga: создание в Keycloak + profile-service)
  → /login

Логин → POST /auth/login → access_token (память) + refresh_token (cookie)
  → GET /profiles/me
    ├── нет профиля → /onboarding (step: 0 — создание базового профиля)
    └── профиль есть → GET /tests/history
          ├── не сдан тест → /onboarding (step: 1 — прохождение теста)
          └── тест сдан   → /dashboard
```

### Авторизация и refresh токена

```
Каждый запрос:
  apiClient → добавляет Authorization: Bearer <access_token>

При 401-ответе:
  ├── если endpoint — /auth/* → не рефрешить, пробросить ошибку
  ├── если уже идёт refresh → поставить запрос в очередь
  └── иначе → POST /auth/refresh (cookie) → новый access_token
        ├── успех → повторить исходный запрос
        └── ошибка → очистить store → редирект на /login

WebSocket (useChatSocket):
  Подключается с token в query-параметре.
  При close code 1008 (auth error) → рефрешит токен → переподключается.
  При других ошибках → экспоненциальный backoff (1s → 30s).
```

### Мэтчинг и лайки

```
Поиск (Classic / Targeted) → список профилей с пагинацией и лимитом просмотров
  └── клик "лайк" → POST /matching/like-with-answers { target_user_id, answers }
        ├── status: 'liked'   → уведомление, ждём reciprocal лайк
        └── status: 'matched' → показываем сравнение ответов

Pending Likes → список входящих лайков
  └── принять → POST /matching/reverse-like (ответные ответы на вопросы)
  └── отклонить → POST /matching/decline-like
```

---

## Роуты приложения

| Маршрут | Страница | Файл | Защита |
|---|---|---|---|
| `/` | Главная / редирект | [pages/index.tsx](./src/pages/index.tsx) | — |
| `/login` | Вход | [pages/auth/LoginPage.tsx](./src/pages/auth/LoginPage.tsx) | — |
| `/registration` | Регистрация | [pages/auth/RegistrationPage.tsx](./src/pages/auth/RegistrationPage.tsx) | — |
| `/forgot-password` | Сброс пароля | [pages/auth/ForgotPasswordPage.tsx](./src/pages/auth/ForgotPasswordPage.tsx) | — |
| `/check-email` | Подтверждение email | [pages/auth/CheckEmailPage.tsx](./src/pages/auth/CheckEmailPage.tsx) | — |
| `/onboarding` | Онбординг | [pages/onboarding/OnboardingPage.tsx](./src/pages/onboarding/OnboardingPage.tsx) | AuthGuard |
| `/dashboard` | Главная дашборда | [pages/dashboard/DashboardHomePage.tsx](./src/pages/dashboard/DashboardHomePage.tsx) | AuthGuard + TestGuard |
| `/dashboard/profile` | Профиль | [pages/dashboard/ProfilePage.tsx](./src/pages/dashboard/ProfilePage.tsx) | AuthGuard + TestGuard |
| `/dashboard/settings` | Настройки аккаунта | [pages/dashboard/SettingsPage.tsx](./src/pages/dashboard/SettingsPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/messages` | Сообщения | [pages/dashboard/MessagesPage.tsx](./src/pages/dashboard/MessagesPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/services` | Сервисы | [pages/dashboard/ServicesPage.tsx](./src/pages/dashboard/ServicesPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/search/classic` | Классический поиск | [pages/dashboard/ClassicSearchPage.tsx](./src/pages/dashboard/ClassicSearchPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/search/targeted` | Таргетированный поиск | [pages/dashboard/TargetedSearchPage.tsx](./src/pages/dashboard/TargetedSearchPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/users/:keycloakId` | Профиль другого юзера | [pages/dashboard/UserProfilePage.tsx](./src/pages/dashboard/UserProfilePage.tsx) | AuthGuard + TestGuard |
| `/dashboard/cupidon` | Рекомендации (Купидон) | [pages/dashboard/CupidonPage.tsx](./src/pages/dashboard/CupidonPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/fortune` | Случайный матч (Фортуна) | [pages/dashboard/FortunePage.tsx](./src/pages/dashboard/FortunePage.tsx) | AuthGuard + TestGuard |
| `/dashboard/likes` | Входящие лайки | [pages/dashboard/PendingLikesPage.tsx](./src/pages/dashboard/PendingLikesPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/matches` | Матчи | [pages/dashboard/MatchesPage.tsx](./src/pages/dashboard/MatchesPage.tsx) | AuthGuard + TestGuard |
| `/dashboard/admin` | Админка пользователей | [pages/dashboard/admin/AdminUsersPage.tsx](./src/pages/dashboard/admin/AdminUsersPage.tsx) | AuthGuard + TestGuard + RoleGuard(admin) |
| `/dashboard/admin/users/:keycloakId` | Детали пользователя | [pages/dashboard/admin/AdminUserDetailPage.tsx](./src/pages/dashboard/admin/AdminUserDetailPage.tsx) | AuthGuard + TestGuard + RoleGuard(admin) |

---

## Взаимодействие с беком

Всё общение идёт через **API Gateway** (`VITE_API_BASE_URL`), который маршрутизирует запросы по микросервисам:

| Префикс | Сервис | Что делает |
|---|---|---|
| `/auth/*` | auth-service | Логин, регистрация, refresh, logout, сброс пароля |
| `/profiles/*` | profile-service | CRUD профиля, вопросы профиля |
| `/matching/*` | matching-service | Лайки, матчи, рекомендации, поиск |
| `/chats/*` | chat-service | Список чатов, создание чата, онлайн-статус |
| `/messages/*` | chat-service | История сообщений |
| `/ws` | chat-service | WebSocket (сообщения, typing, read receipts) |
| `/media/*` | media-service | Загрузка аватара и других медиафайлов |
| `/tests/*` | testing-service | Старт теста, ответы, результаты, история |
| `/matching/search/*` | matching-service | Классический и таргетированный поиск профилей |

**HTTP:** Axios-инстанс `apiClient` автоматически добавляет `Authorization: Bearer <token>` и перехватывает 401 для рефреша.

**WebSocket:** Подключается к `ws[s]://<host>/ws?token=<access_token>`. При истечении токена (код 1008) автоматически рефрешит и переподключается.

**Cookies:** Refresh token хранится в HTTP-only cookie — фронтенд его не читает, он передаётся браузером автоматически при `POST /auth/refresh`.
