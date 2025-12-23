# Architecture Documentation

## Project Overview

| Field | Value |
|-------|-------|
| Name | Meeting Notification Bot |
| Type | Telegram Bot |
| Language | Python 3.11 |
| Framework | aiogram 3.x |
| Database | PostgreSQL 15 |
| Deployment | Docker Compose |

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Bot Framework | aiogram | >=3.0.0 |
| Database Driver | asyncpg | >=0.29.0 |
| Scheduler | APScheduler | >=3.10.0 |
| Config | python-dotenv | >=1.0.0 |
| Container | Docker | - |

## Directory Structure

```
event_bot/
├── main.py              # Entry point, bot initialization
├── config.py            # Environment configuration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container build
├── docker-compose.yml   # Service orchestration
├── .env.example         # Environment template
├── database/
│   ├── __init__.py      # Module exports
│   ├── models.py        # SQL schema definitions
│   └── queries.py       # CRUD operations (457 lines)
├── handlers/
│   └── __init__.py      # [NOT IMPLEMENTED] Message/callback handlers
├── keyboards/
│   ├── __init__.py      # Module exports
│   ├── inline.py        # Inline keyboards + callbacks (401 lines)
│   └── reply.py         # Reply keyboards
├── scheduler/
│   └── __init__.py      # [NOT IMPLEMENTED] Reminder scheduler
└── utils/
    └── __init__.py      # [NOT IMPLEMENTED] Utility functions
```

## Data Model

### Entity Relationship

```
users (1) ──────< registrations >────── (1) events
                       │
                       │
                       ▼
              scheduled_reminders
```

### Tables

#### users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| telegram_id | BIGINT | PK | Telegram user ID |
| username | VARCHAR(255) | nullable | @username |
| first_name | VARCHAR(255) | NOT NULL | Display name |
| notify_it | BOOLEAN | DEFAULT TRUE | IT events subscription |
| notify_sport | BOOLEAN | DEFAULT TRUE | Sport events subscription |
| notify_books | BOOLEAN | DEFAULT TRUE | Books events subscription |
| created_at | TIMESTAMP | DEFAULT NOW() | Registration timestamp |

#### events
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | Event ID |
| title | VARCHAR(255) | NOT NULL | Event title |
| category | VARCHAR(50) | CHECK (IT/Спорт/Книги) | Event category |
| format | VARCHAR(50) | CHECK (онлайн/оффлайн) | Online/offline |
| event_datetime | TIMESTAMP | NOT NULL | Event date and time |
| location | TEXT | NOT NULL | Venue or link |
| description | TEXT | nullable | Event description |
| organizer_contact | VARCHAR(255) | NOT NULL | Organizer contact |
| is_cancelled | BOOLEAN | DEFAULT FALSE | Cancellation flag |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

#### registrations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | Registration ID |
| user_id | BIGINT | FK → users | User reference |
| event_id | INTEGER | FK → events | Event reference |
| status | VARCHAR(50) | CHECK (active/cancelled) | Registration status |
| created_at | TIMESTAMP | DEFAULT NOW() | Registration timestamp |
| - | - | UNIQUE(user_id, event_id) | One registration per user per event |

#### scheduled_reminders
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | Reminder ID |
| registration_id | INTEGER | FK → registrations | Registration reference |
| remind_at | TIMESTAMP | NOT NULL | When to send |
| reminder_type | VARCHAR(10) | CHECK (24h/15min) | Reminder timing |
| sent | BOOLEAN | DEFAULT FALSE | Sent flag |

### Indexes
- `idx_remind_at_sent` on `scheduled_reminders(remind_at, sent)` - Efficient reminder queries
- `idx_events_datetime` on `events(event_datetime)` WHERE NOT cancelled - Event lookups
- `idx_registrations_user` on `registrations(user_id)` WHERE active - User registrations

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│                 (Bot, Dispatcher)                   │
└───────────────────────┬─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  handlers/   │ │  keyboards/  │ │  scheduler/  │
│ (not impl)   │ │  inline.py   │ │  (not impl)  │
│              │ │  reply.py    │ │              │
└──────┬───────┘ └──────────────┘ └──────┬───────┘
       │                                 │
       └────────────────┬────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │    database/    │
              │   queries.py    │
              │   models.py     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   PostgreSQL    │
              └─────────────────┘
```

## Module APIs

### database/queries.py

#### Connection Management
| Function | Signature | Description |
|----------|-----------|-------------|
| get_pool | `() → asyncpg.Pool` | Get/create connection pool |
| close_pool | `() → None` | Close connection pool |
| init_db | `() → None` | Initialize database tables |

#### User Operations
| Function | Signature | Description |
|----------|-----------|-------------|
| create_user | `(telegram_id, first_name, username?) → dict` | Create or update user |
| get_user | `(telegram_id) → dict?` | Get user by ID |
| update_user_notifications | `(telegram_id, notify_it?, notify_sport?, notify_books?) → dict?` | Update notification preferences |
| get_users_by_category | `(category) → list[dict]` | Get users subscribed to category |

#### Event Operations
| Function | Signature | Description |
|----------|-----------|-------------|
| create_event | `(title, category, format, event_datetime, location, organizer_contact, description?) → dict` | Create event |
| get_event | `(event_id) → dict?` | Get event by ID |
| get_upcoming_events | `(category?, limit=10) → list[dict]` | Get future events |
| cancel_event | `(event_id) → dict?` | Cancel event |
| get_all_events | `(include_cancelled=False) → list[dict]` | Get all events (admin) |

#### Registration Operations
| Function | Signature | Description |
|----------|-----------|-------------|
| create_registration | `(user_id, event_id) → dict?` | Register user for event |
| cancel_registration | `(user_id, event_id) → dict?` | Cancel registration |
| get_registration | `(user_id, event_id) → dict?` | Get specific registration |
| get_event_registrations | `(event_id, active_only=True) → list[dict]` | Get event participants |
| get_user_registrations | `(user_id, active_only=True) → list[dict]` | Get user's registrations |
| get_registration_count | `(event_id) → int` | Count active registrations |

#### Reminder Operations
| Function | Signature | Description |
|----------|-----------|-------------|
| create_reminders | `(registration_id, event_datetime) → list[dict]` | Create 24h and 15min reminders |
| get_pending_reminders | `() → list[dict]` | Get unsent due reminders |
| mark_reminder_sent | `(reminder_id) → None` | Mark reminder as sent |
| delete_registration_reminders | `(registration_id) → None` | Delete pending reminders |
| mark_event_reminders_sent | `(event_id) → None` | Mark all event reminders sent |

### keyboards/inline.py

#### Callback Data Factories
| Class | Prefix | Fields | Actions |
|-------|--------|--------|---------|
| EventCallback | event | action, event_id? | detail, list |
| RegistrationCallback | reg | action, event_id | register, cancel |
| SettingsCallback | settings | action, category | toggle |
| CalendarCallback | cal | action, event_id | google, yandex, choose |
| AdminCallback | admin | action, event_id? | create, list, broadcast, participants, edit, cancel, etc. |
| ReminderCallback | remind | action, registration_id | confirm, decline |

#### Keyboard Builders
| Function | Returns | Description |
|----------|---------|-------------|
| event_list_kb | InlineKeyboardMarkup | Event list with detail buttons |
| event_detail_kb | InlineKeyboardMarkup | Event actions (register/cancel/calendar/share) |
| registration_success_kb | InlineKeyboardMarkup | Post-registration options |
| settings_kb | InlineKeyboardMarkup | Notification toggles |
| calendar_kb | InlineKeyboardMarkup | Calendar service selection |
| reminder_kb | InlineKeyboardMarkup | 24h reminder confirm/decline |
| admin_menu_kb | InlineKeyboardMarkup | Admin main menu |
| admin_event_list_kb | InlineKeyboardMarkup | Admin event list |
| admin_event_manage_kb | InlineKeyboardMarkup | Event management options |
| create_event_category_kb | InlineKeyboardMarkup | Category selection |
| create_event_format_kb | InlineKeyboardMarkup | Format selection |
| create_event_preview_kb | InlineKeyboardMarkup | Preview confirmation |
| admin_cancel_confirm_kb | InlineKeyboardMarkup | Cancel confirmation |
| admin_broadcast_confirm_kb | InlineKeyboardMarkup | Broadcast confirmation |
| admin_participants_kb | InlineKeyboardMarkup | Participants list actions |

### keyboards/reply.py

| Function | Returns | Description |
|----------|---------|-------------|
| main_menu_kb | ReplyKeyboardMarkup | Main menu (Мероприятия, Настройки) |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| BOT_TOKEN | Yes | Telegram bot token from @BotFather |
| DATABASE_URL | Yes | PostgreSQL connection string |
| ADMIN_IDS | No | Comma-separated admin Telegram IDs |

### Validation
- `BOT_TOKEN`: Raises `ValueError` if not set
- `DATABASE_URL`: Used as-is, no validation
- `ADMIN_IDS`: Parsed to `list[int]`, empty list if not set

## Deployment

### Docker Compose Services

| Service | Image | Port | Volume |
|---------|-------|------|--------|
| postgres | postgres:15-alpine | 5432 (internal) | postgres_data |
| bot | Built from Dockerfile | - | - |

### Container Dependencies
```
bot → postgres (depends_on)
```

## Implementation Status

| Module | Status | Notes |
|--------|--------|-------|
| main.py | Minimal | Only /start command |
| config.py | Complete | - |
| database/models.py | Complete | - |
| database/queries.py | Complete | All CRUD operations |
| keyboards/inline.py | Complete | All keyboards defined |
| keyboards/reply.py | Complete | - |
| handlers/ | Not implemented | Empty __init__.py |
| scheduler/ | Not implemented | Empty __init__.py |
| utils/ | Not implemented | Empty __init__.py |

## User Flows

### Event Registration Flow
```
User: /start → Мероприятия → Select Event → Detail View → Записаться → Success
```

### Admin Event Creation Flow
```
Admin: /admin → Создать мероприятие → Category → Format → Title → DateTime → Location → Description → Contact → Preview → Опубликовать
```

### Reminder Flow
```
Registration → Create Reminders (24h, 15min) → Scheduler checks → Send reminder → User confirms/declines
```

## Event Categories

| Category | DB Value | Notification Field |
|----------|----------|-------------------|
| IT | IT | notify_it |
| Sport | Спорт | notify_sport |
| Books | Книги | notify_books |

## Event Formats

| Format | DB Value |
|--------|----------|
| Online | онлайн |
| Offline | оффлайн |
