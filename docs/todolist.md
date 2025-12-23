# EVENT_BOT_DEVELOPMENT_PLAN

## META
- project_name: telegram_event_bot
- stack: python3.11, aiogram3, postgresql, apscheduler
- estimated_total_hours: 32-40
- task_max_hours: 4

## PROJECT_STRUCTURE
```
event_bot/
├── main.py
├── config.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   └── queries.py
├── handlers/
│   ├── __init__.py
│   ├── user.py
│   └── admin.py
├── keyboards/
│   ├── __init__.py
│   ├── reply.py
│   └── inline.py
├── scheduler/
│   ├── __init__.py
│   └── reminders.py
├── utils/
│   ├── __init__.py
│   ├── calendar_links.py
│   └── formatters.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## DATABASE_SCHEMA
```sql
TABLE users:
  telegram_id BIGINT PRIMARY KEY
  username VARCHAR(255) NULL
  first_name VARCHAR(255)
  notify_it BOOLEAN DEFAULT TRUE
  notify_sport BOOLEAN DEFAULT TRUE
  notify_books BOOLEAN DEFAULT TRUE
  created_at TIMESTAMP DEFAULT NOW()

TABLE events:
  id SERIAL PRIMARY KEY
  title VARCHAR(255) NOT NULL
  category VARCHAR(50) NOT NULL CHECK (category IN ('IT', 'Спорт', 'Книги'))
  format VARCHAR(50) NOT NULL CHECK (format IN ('онлайн', 'оффлайн'))
  event_datetime TIMESTAMP NOT NULL
  location TEXT NOT NULL
  description TEXT
  organizer_contact VARCHAR(255) NOT NULL
  is_cancelled BOOLEAN DEFAULT FALSE
  created_at TIMESTAMP DEFAULT NOW()

TABLE registrations:
  id SERIAL PRIMARY KEY
  user_id BIGINT REFERENCES users(telegram_id)
  event_id INTEGER REFERENCES events(id)
  status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'cancelled'))
  created_at TIMESTAMP DEFAULT NOW()
  UNIQUE(user_id, event_id)

TABLE scheduled_reminders:
  id SERIAL PRIMARY KEY
  registration_id INTEGER REFERENCES registrations(id)
  remind_at TIMESTAMP NOT NULL
  reminder_type VARCHAR(10) NOT NULL CHECK (reminder_type IN ('24h', '15min'))
  sent BOOLEAN DEFAULT FALSE
  INDEX idx_remind_at_sent ON scheduled_reminders(remind_at, sent)
```

---

## TASKS

### TASK_001
- id: TASK_001
- title: project_init_and_config
- hours: 2
- dependencies: none
- description: |
    Создать структуру проекта, настроить конфигурацию и зависимости.
    Инициализировать aiogram Bot и Dispatcher.
    Настроить загрузку переменных окружения.
- files_to_create:
    - main.py
    - config.py
    - requirements.txt
    - .env.example
    - docker-compose.yml
    - Dockerfile
- context_files_required:
    - EVENT_BOT_DEVELOPMENT_PLAN.md (this file)
- success_criteria:
    - requirements.txt содержит: aiogram>=3.0.0, asyncpg, apscheduler, python-dotenv
    - config.py загружает BOT_TOKEN, DATABASE_URL, ADMIN_IDS из .env
    - main.py запускается без ошибок и бот отвечает на /start текстом "Bot is running"
    - docker-compose.yml поднимает postgres и bot контейнеры
- output_validation: |
    python main.py запускается
    /start в Telegram возвращает ответ
    docker-compose up создает работающие контейнеры

### TASK_002
- id: TASK_002
- title: database_setup
- hours: 3
- dependencies: TASK_001
- description: |
    Создать модели SQLAlchemy или asyncpg запросы.
    Реализовать функции для всех CRUD операций.
    Написать скрипт миграции/инициализации таблиц.
- files_to_create:
    - database/__init__.py
    - database/models.py
    - database/queries.py
- context_files_required:
    - config.py
    - EVENT_BOT_DEVELOPMENT_PLAN.md (секция DATABASE_SCHEMA)
- success_criteria:
    - Все 4 таблицы создаются при первом запуске
    - Функции: create_user, get_user, update_user_notifications
    - Функции: create_event, get_event, get_upcoming_events, cancel_event
    - Функции: create_registration, cancel_registration, get_event_registrations
    - Функции: create_reminders, get_pending_reminders, mark_reminder_sent
- output_validation: |
    Импорт database работает без ошибок
    Тестовый вызов create_user создает запись в БД
    get_upcoming_events возвращает список

### TASK_003
- id: TASK_003
- title: keyboards_module
- hours: 2
- dependencies: TASK_001
- description: |
    Создать все reply и inline клавиатуры.
    Реализовать callback_data фабрики для inline кнопок.
- files_to_create:
    - keyboards/__init__.py
    - keyboards/reply.py
    - keyboards/inline.py
- context_files_required:
    - EVENT_BOT_DEVELOPMENT_PLAN.md (секция TASKS с репликами)
- success_criteria:
    - reply.py: main_menu_kb() возвращает ReplyKeyboardMarkup с кнопками "🗓 Мероприятия", "⚙️ Настройки"
    - inline.py: event_list_kb(events) генерирует кнопки "Подробнее" для каждого события
    - inline.py: event_detail_kb(event_id, is_registered) с кнопками записи/отмены
    - inline.py: settings_kb(user) с toggle-кнопками категорий
    - inline.py: calendar_kb(event) с кнопками Google/Яндекс
    - inline.py: admin_menu_kb(), create_event_category_kb(), create_event_format_kb()
    - CallbackData классы: EventCallback, RegistrationCallback, SettingsCallback, AdminCallback
- output_validation: |
    Все функции возвращают корректные Markup объекты
    CallbackData парсится и упаковывается без ошибок

### TASK_004
- id: TASK_004
- title: utils_module
- hours: 2
- dependencies: TASK_001
- description: |
    Создать утилиты для генерации календарных ссылок и форматирования сообщений.
- files_to_create:
    - utils/__init__.py
    - utils/calendar_links.py
    - utils/formatters.py
- context_files_required:
    - EVENT_BOT_DEVELOPMENT_PLAN.md
- success_criteria:
    - calendar_links.py: google_calendar_url(event) возвращает валидный URL
    - calendar_links.py: yandex_calendar_url(event) возвращает валидный URL
    - formatters.py: format_event_card(event) возвращает строку для списка
    - formatters.py: format_event_detail(event) возвращает полное описание
    - formatters.py: format_share_message(event, bot_username) для пересылки
    - formatters.py: format_datetime(dt) возвращает "27 января, пн, 19:00"
- output_validation: |
    google_calendar_url генерирует открываемую ссылку
    format_event_detail содержит все поля события

### TASK_005
- id: TASK_005
- title: user_handlers_start_and_events
- hours: 4
- dependencies: TASK_002, TASK_003, TASK_004
- description: |
    Реализовать пользовательские хендлеры: /start, просмотр мероприятий, детали события.
- files_to_create:
    - handlers/__init__.py
    - handlers/user.py
- context_files_required:
    - config.py
    - database/queries.py
    - keyboards/reply.py
    - keyboards/inline.py
    - utils/formatters.py
- success_criteria:
    - /start создает пользователя в БД если не существует
    - /start отправляет приветствие и main_menu_kb
    - Кнопка "🗓 Мероприятия" показывает список ближайших событий
    - Кнопка "Подробнее" показывает детали с кнопками действий
    - Кнопка "👤 Связаться с организатором" открывает ссылку
- output_validation: |
    Новый пользователь создается в таблице users
    Список мероприятий отображается корректно
    Детали события содержат все поля

### TASK_006
- id: TASK_006
- title: user_handlers_registration
- hours: 3
- dependencies: TASK_005
- description: |
    Реализовать регистрацию на мероприятие, отмену регистрации, добавление в календарь, шаринг.
- files_to_create: none (редактирование handlers/user.py)
- files_to_modify:
    - handlers/user.py
- context_files_required:
    - handlers/user.py
    - database/queries.py
    - keyboards/inline.py
    - utils/calendar_links.py
    - utils/formatters.py
- success_criteria:
    - Кнопка "✅ Записаться" создает registration и 2 scheduled_reminders
    - После записи показывается подтверждение с кнопкой календаря
    - Кнопка "❌ Отменить запись" меняет status на cancelled
    - Кнопка "📅 В календарь" показывает выбор Google/Яндекс
    - Кнопка "📤 Поделиться" отправляет share-сообщение
    - При повторном просмотре события кнопка меняется на "Отменить"
- output_validation: |
    Запись создается в registrations
    2 записи создаются в scheduled_reminders с корректными remind_at
    Отмена меняет статус и удаляет напоминания

### TASK_007
- id: TASK_007
- title: user_handlers_settings
- hours: 2
- dependencies: TASK_005
- description: |
    Реализовать настройки уведомлений пользователя.
- files_to_modify:
    - handlers/user.py
- context_files_required:
    - handlers/user.py
    - database/queries.py
    - keyboards/inline.py
- success_criteria:
    - Кнопка "⚙️ Настройки" показывает текущие настройки с toggle-кнопками
    - Нажатие на категорию переключает ✅ ↔ ❌
    - Изменения сохраняются в БД (notify_it, notify_sport, notify_books)
    - Клавиатура обновляется после каждого нажатия
- output_validation: |
    Toggle работает и обновляет БД
    UI отражает актуальное состояние

### TASK_008
- id: TASK_008
- title: admin_handlers_menu_and_list
- hours: 3
- dependencies: TASK_005
- description: |
    Реализовать админ-панель: проверка доступа, меню, список мероприятий админа.
- files_to_create:
    - handlers/admin.py
- files_to_modify:
    - handlers/__init__.py
- context_files_required:
    - config.py (ADMIN_IDS)
    - database/queries.py
    - keyboards/inline.py
    - utils/formatters.py
- success_criteria:
    - /admin доступна только пользователям из ADMIN_IDS
    - Не-админ получает сообщение "У тебя нет доступа"
    - Админ видит меню с кнопками: Создать, Мои мероприятия, Рассылка
    - "Мои мероприятия" показывает список с количеством записей
    - Каждое мероприятие имеет кнопки: Участники, Рассылка, Редактировать, Отменить
- output_validation: |
    /admin от не-админа отклоняется
    /admin от админа показывает меню
    Список мероприятий загружается из БД

### TASK_009
- id: TASK_009
- title: admin_handlers_create_event
- hours: 4
- dependencies: TASK_008
- description: |
    Реализовать пошаговое создание мероприятия через FSM (Finite State Machine).
- files_to_modify:
    - handlers/admin.py
- context_files_required:
    - handlers/admin.py
    - database/queries.py
    - keyboards/inline.py
    - utils/formatters.py
- success_criteria:
    - FSM состояния: title, category, format, datetime, location, description, preview
    - Шаг 1: ввод названия текстом
    - Шаг 2: выбор категории inline-кнопками (IT/Спорт/Книги)
    - Шаг 3: выбор формата inline-кнопками (Онлайн/Оффлайн)
    - Шаг 4: ввод даты текстом с валидацией формата "DD.MM.YYYY HH:MM"
    - Шаг 5: ввод ссылки/адреса текстом
    - Шаг 6: ввод описания текстом
    - Превью с кнопками: Опубликовать, Редактировать, Отмена
    - "Опубликовать" сохраняет в БД и запускает рассылку
- output_validation: |
    Полный цикл создания проходит без ошибок
    Событие появляется в БД
    Рассылка отправляется подписчикам категории

### TASK_010
- id: TASK_010
- title: admin_handlers_participants_and_broadcast
- hours: 3
- dependencies: TASK_008
- description: |
    Реализовать просмотр участников и рассылку по участникам мероприятия.
- files_to_modify:
    - handlers/admin.py
- context_files_required:
    - handlers/admin.py
    - database/queries.py
    - keyboards/inline.py
- success_criteria:
    - "Участники" показывает список с username/first_name
    - "Скачать список" отправляет .csv файл
    - "Рассылка" запрашивает текст сообщения
    - Превью рассылки с количеством получателей
    - "Отправить" рассылает сообщение всем активным участникам
    - Отчет об отправке: успешно/заблокировали бота
- output_validation: |
    CSV содержит корректные данные
    Рассылка доходит до участников
    Заблокировавшие бота не ломают рассылку

### TASK_011
- id: TASK_011
- title: admin_handlers_cancel_event
- hours: 2
- dependencies: TASK_008
- description: |
    Реализовать отмену мероприятия с уведомлением участников.
- files_to_modify:
    - handlers/admin.py
- context_files_required:
    - handlers/admin.py
    - database/queries.py
    - keyboards/inline.py
- success_criteria:
    - "Отменить" запрашивает подтверждение
    - При подтверждении: event.is_cancelled = True
    - Все активные участники получают уведомление об отмене
    - Отмененное мероприятие не показывается в списке пользователя
    - scheduled_reminders для этого события помечаются sent=True
- output_validation: |
    Событие помечается отмененным
    Участники получают уведомление
    Напоминания не отправляются

### TASK_012
- id: TASK_012
- title: scheduler_reminders
- hours: 4
- dependencies: TASK_002, TASK_006
- description: |
    Реализовать фоновый планировщик для отправки напоминаний.
- files_to_create:
    - scheduler/__init__.py
    - scheduler/reminders.py
- files_to_modify:
    - main.py (подключение scheduler)
- context_files_required:
    - config.py
    - database/queries.py
    - utils/formatters.py
    - main.py
- success_criteria:
    - APScheduler запускается вместе с ботом
    - Задача проверки напоминаний выполняется каждую минуту
    - Выбираются reminders где remind_at <= now() AND sent = FALSE
    - Напоминание 24h: текст с кнопками "Да, буду" / "Не смогу"
    - Напоминание 15min: текст со ссылкой/адресом
    - После отправки reminder.sent = True
    - "Не смогу" отменяет регистрацию и 15min напоминание
    - Обработка ошибок: пользователь заблокировал бота
- output_validation: |
    Напоминания отправляются в нужное время
    Повторная отправка не происходит
    Кнопки в напоминании работают

### TASK_013
- id: TASK_013
- title: integration_and_main
- hours: 3
- dependencies: TASK_005, TASK_007, TASK_008, TASK_012
- description: |
    Собрать все модули в main.py, настроить роутеры, протестировать полный цикл.
- files_to_modify:
    - main.py
    - handlers/__init__.py
- context_files_required:
    - main.py
    - config.py
    - handlers/user.py
    - handlers/admin.py
    - scheduler/reminders.py
- success_criteria:
    - Все роутеры подключены к dispatcher
    - Scheduler запускается при старте бота
    - Graceful shutdown: scheduler и бот останавливаются корректно
    - Логирование ключевых событий (регистрации, рассылки, ошибки)
    - Полный user flow работает: /start → мероприятия → запись → напоминания
    - Полный admin flow работает: /admin → создание → рассылка → участники
- output_validation: |
    docker-compose up запускает работающую систему
    E2E тест пользовательского сценария проходит
    E2E тест админского сценария проходит

### TASK_014
- id: TASK_014
- title: deployment_and_docs
- hours: 2
- dependencies: TASK_013
- description: |
    Финализировать Docker-конфигурацию, написать README с инструкцией по деплою.
- files_to_create:
    - README.md
- files_to_modify:
    - docker-compose.yml
    - Dockerfile
    - .env.example
- context_files_required:
    - docker-compose.yml
    - Dockerfile
    - .env.example
- success_criteria:
    - README содержит: описание, требования, инструкцию запуска, переменные окружения
    - docker-compose.yml: volumes для postgres, restart policies, healthchecks
    - .env.example содержит все необходимые переменные с комментариями
    - Инструкция по получению BOT_TOKEN от @BotFather
    - Инструкция по настройке ADMIN_IDS
- output_validation: |
    Свежий клон репозитория + docker-compose up = работающий бот
    README понятен для человека без контекста

---

## EXECUTION_ORDER
1. TASK_001 (init)
2. TASK_002 (database)
3. TASK_003 (keyboards) | TASK_004 (utils) — параллельно
4. TASK_005 (user handlers base)
5. TASK_006 (registration) | TASK_007 (settings) — параллельно
6. TASK_008 (admin base)
7. TASK_009 (create event)
8. TASK_010 (participants) | TASK_011 (cancel) — параллельно
9. TASK_012 (scheduler)
10. TASK_013 (integration)
11. TASK_014 (deployment)

## TOTAL_ESTIMATE
- minimum_hours: 35
- maximum_hours: 42
- parallel_execution_possible: yes, reduces wall time to ~28 hours

## NOTES_FOR_AI_EXECUTOR
- При выполнении каждой задачи загружай только файлы из context_files_required
- Проверяй success_criteria перед завершением задачи
- Используй output_validation для тестирования
- Если задача зависит от других — убедись что зависимости выполнены
- DATABASE_SCHEMA является источником истины для структуры БД
- Все datetime хранить в UTC, отображать в Europe/Moscow