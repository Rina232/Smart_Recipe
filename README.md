# Smart_Recipe
**Smart Recipe - RAG-система интеллектуального подбора рецептов.**

[Макет интерфейса в Figma](https://www.figma.com/design/MY90cdgJdofAJO2hpBHhNA/LLM-Cookbook?node-id=0-1&t=dcSLjXRxq8BOpxOk-1)

## Состав команды

* **Кострыкина Екатерина Геннадьевна** - BM25 и RAG.
* **Яхутль Милена Алексеевна** - интеграция компонентов.
* **Бурматов Степан Максимович** - продукт и пользовательский интерфейс.

## О проекте

Smart Recipe - веб-приложение, которое помогает пользователю подобрать рецепт на основе имеющихся ингредиентов.

Система использует алгоритм BM25 для поиска подходящих рецептов в коллекции документов и большую языковую модель (LLM) для формирования ответа на основе найденной информации.

## Технологии

* **Backend:** Python, FastAPI.
* **Frontend:** Vue.js, Vite.
* **Поиск:** собственная реализация BM25.
* **Обработка текста:** токенизация и лемматизация.
* **Генерация ответов:** LLM API.
* **Тестирование:** pytest.
* **Контроль версий:** Git.

## Запуск

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

## Тестовые аккаунты

| Роль           | Логин   | Пароль      |
| -------------- | ------- | ----------- |
| Администратор  | `admin` | `admin123`  |
| Пользователь   | `user`  | `user12345` |

## Структура репозитория

```text
Smart_Recipe/
├── README.md
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── docs/
│   └── product/
│       ├── index.md
│       ├── interface.md
│       ├── product.md
│       ├── user-flow.md
│       └── ui/
│           ├── colors.md
│           ├── components.md
│           └── typography.md
├── public/
│   └── icons/
│       ├── deco/
│       └── ui/
└── src/
    ├── main.js
    ├── App.vue
    ├── router/
    ├── layouts/
    ├── views/
    ├── components/
    ├── stores/
    ├── data/
    ├── utils/
    └── styles/
```

## Назначение основных компонентов
* **[`docs/product/`](docs/product/)** - документация продукта и пользовательского интерфейса.
* **[`public/`](public/)** - статические ресурсы приложения, включая иконки и графические элементы интерфейса.
* **[`index.html`](index.html)** - точка входа Vite, подключает шрифты Alegreya Sans и Golos Text.
* **[`package.json`](package.json)** и **[`vite.config.js`](vite.config.js)** - зависимости, скрипты запуска и сборки, настройка Vite.
* **[`src/main.js`](src/main.js)** и **[`src/App.vue`](src/App.vue)** - инициализация приложения и корневой компонент.
* **[`src/router/`](src/router/)** - маршруты и правила доступа из `user-flow.md`.
* **[`src/layouts/`](src/layouts/)** - `AppLayout.vue`: сайдбар, область контента и диалог удаления чата.
* **[`src/views/`](src/views/)** - экраны: вход, регистрация, новый чат, активный чат, дашборд и карточка пользователя в панели администратора.
* **[`src/components/`](src/components/)** - UI-компоненты из `components.md`: кнопка, поле ввода, подсказка, сайдбар, карточка рецепта, индикатор надёжности пароля, KPI-карточки, нижняя панель таблицы и др.; также вспомогательные (`BaseIcon`, `ConfirmDialog`, `AuthShell`, `DeltaBadge`, `StatusBadge`, `PeriodSwitch`).
* **[`src/stores/`](src/stores/)** - `auth.js` (вход, регистрация, гость, сессия) и `chats.js` (чаты и сообщения). Заглушки вместо API, данные хранятся в `localStorage`.
* **[`src/data/`](src/data/)** - моковые данные: `recipes.js` (рецепты и «ответы ИИ»), `admin.js` (пользователи, KPI, чаты и активность для панели администратора).
* **[`src/utils/`](src/utils/)** - `format.js` (даты, числа, склонения) и `validation.js` (проверка полей регистрации, оценка надёжности пароля).
* **[`src/styles/`](src/styles/)** - `tokens.css` (цвета, шрифты и стили текста из `colors.md` и `typography.md`) и `base.css` (сброс и общие стили).


*Структура репозитория предварительная и может изменяться в процессе разработки.*
