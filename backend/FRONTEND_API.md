# Контракт backend ↔ frontend (для Степана)

**Base URL:** `http://127.0.0.1:8000` (локально).

HTTP API принимает и возвращает JSON. На защищённых маршрутах необходим заголовок:

```http
Authorization: Bearer <access_token>
```

Токен выдаётся при регистрации, входе или создании гостевой сессии. В самой HTML-странице он не зашит. При выходе серверный токен аннулируется, а frontend должен удалить свою сохранённую копию.

## 1. Регистрация и вход

| Метод | URL | Тело запроса | Результат |
|---|---|---|---|
| POST | `/auth/register` | `{ "username": "user123", "display_name": "Пользователь", "password": "password123" }` | `access_token`, `expires_at`, `user` |
| POST | `/auth/login` | `{ "username": "user123", "password": "password123" }` | `access_token`, `expires_at`, `user` |
| POST | `/auth/guest` | нет | `access_token`, `expires_at`, `user` (гость) |
| GET | `/auth/me` | нет | текущий `user` |
| POST | `/auth/logout` | нет | HTTP 204 |

Поля `user`: `id`, `username`, `display_name`, `role`, `is_guest`, `created_at`, `last_active_at`.

**Правила ввода:** логин 3–30 ASCII-букв/цифр/`_`/`-` (приводится к нижнему регистру); отображаемое имя 3–30 символов, буквы/пробел/дефис/апостроф; пароль 8–128 символов. Валидацию пароля на фронте можно отображать отдельным индикатором. Публичной регистрации администратора нет.

**Гость:** после `POST /auth/guest` сервер автоматически создаёт один гостевой чат. Для сохранения его при перезагрузке frontend должен сохранить `access_token` и снова запросить `/chats`. **Не** вызывайте `/auth/guest` после каждого обновления страницы — это новая гостевая учётная запись и новый чат.

## 2. Чаты

| Метод | URL | Тело запроса | Результат |
|---|---|---|---|
| GET | `/chats` | нет | список чатов только текущего пользователя |
| POST | `/chats` | нет | новый чат (201; гостю запрещено) |
| GET | `/chats/{chat_id}` | нет | `{ "chat": {...}, "messages": [...] }` |
| DELETE | `/chats/{chat_id}` | нет | 204, скрывает чат из списка |
| POST | `/chats/{chat_id}/messages` | `{ "content": "Что приготовить из курицы?" }` | `{ "user_message": {...}, "assistant_message": {...} }` |

`chat`: `id`, `title`, `is_deleted`, `created_at`, `updated_at`.

`message`: `id`, `role` (`user` или `assistant`), `content`, `sources` (список ID рецептов), `recipe` (объект карточки или `null`), `created_at`.

`recipe` при наличии: `title`, `image_url`, `calories_kcal`, `protein_g`, `fat_g`, `carbs_g`, `cooking_time_minutes`, `ingredients` (массив строк). Если RAG не вернул карточку, фронтенд отображает только текст `content`. Данные не нужно извлекать из текста ответа регулярными выражениями.

Первое сообщение автоматически устанавливает название нового чата по началу запроса. Гостю нельзя создать второй чат или удалить единственный. Для пользователя чужие чаты недоступны (404).

**Рекомендуемый сценарий:**

1. Вход/регистрация/гостевой вход → сохранить токен.
2. GET `/chats` → построить сайдбар.
3. POST `/chats` при нажатии «Новый чат» (кроме гостя).
4. GET `/chats/{id}` → показать историю сообщений.
5. POST `/chats/{id}/messages` → показать оба новых сообщения; обновить список чатов.
6. DELETE `/chats/{id}` → после подтверждения удаления на frontend.

## 3. Прямой запрос по лекции

POST `/ask`:

```json
{"question":"Что приготовить из курицы и грибов?"}
```

Ответ:

```json
{"answer":"[ЗАГЛУШКА RAG] ...", "sources":[]}
```

`/ask` **не сохраняет** сообщения. Для чат-интерфейса использовать `/chats/{id}/messages`.

## 4. Админка (роль `admin`)

| Метод | URL | Назначение |
|---|---|---|
| GET | `/admin/summary?period=7d` | KPI и изменения по сравнению с прошлым периодом |
| GET | `/admin/users?search=&message_period=7d&sort_by=display_name&order=asc&page=1&page_size=5` | поиск, сортировка, пагинация |
| GET | `/admin/users/{id}` | информация и показатели пользователя |
| GET | `/admin/users/{id}/chats?page=1&page_size=5` | чаты, включая удалённые |
| GET | `/admin/users/{id}/activities?page=1&page_size=5` | последние действия пользователя |

`period` и `message_period` — `1d`, `3d`, `7d`, `1m` (условно 30 дней). Список возвращается как `{ "items": [...], "total": N, "page": 1, "page_size": 5, "total_pages": M }`.

`/admin/summary` возвращает: `total_users`, `active_users`, `new_chats`, `messages` и поля `*_change_percent`; рост общего числа пользователей — `total_users_growth_percent`. Если прошлый показатель равен нулю, процент роста может быть `null`.

`/admin/users` строки включают: `total_chats`, `active_chats`, `total_messages`, `messages_in_period`, `last_active_at` и публичные поля пользователя.

Для обычного пользователя админские маршруты возвращают HTTP 403.

## 5. Ошибки и особенности

- 401 — отсутствует, истёк или отозван токен;
- 403 — нет прав (например, пользователь пытается открыть админку);
- 404 — чат чужой, удалённый или не найден;
- 409 — логин уже занят;
- 422 — неверные поля/тело запроса;
- 502 — RAG вернул неправильную структуру;
- 503 — RAG не смог ответить.

Все timestamps — целые Unix-секунды UTC. Пример конвертации в JavaScript: `new Date(created_at * 1000)`.

## 6. Fetch-пример

```js
const API = 'http://127.0.0.1:8000';
const token = 'PASTE_ACCESS_TOKEN_HERE'; // замените на реальный токен

const response = await fetch(`${API}/chats/1/messages`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({ content: 'Что приготовить из курицы и грибов?' }),
});
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const { user_message, assistant_message } = await response.json();
```

Маршруты страниц Vue `/login`, `/register`, `/chat/new`, `/chat/:id` и `/admin` — это **frontend-роуты**, а не адреса backend API.

**Безопасность:** избегайте долгого хранения токена в `localStorage` в публичном веб-приложении; для учебного локального прототипа важнее обеспечить сохранение токена гостя между перезагрузками и очищать его при выходе. Для публичного запуска потребуются HTTPS и согласованная более строгая политика сессий.
