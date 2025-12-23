"""Database models and table creation scripts."""

INIT_TABLES_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    notify_it BOOLEAN DEFAULT TRUE,
    notify_sport BOOLEAN DEFAULT TRUE,
    notify_books BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('IT', 'Спорт', 'Книги')),
    format VARCHAR(50) NOT NULL CHECK (format IN ('онлайн', 'оффлайн')),
    event_datetime TIMESTAMP NOT NULL,
    location TEXT NOT NULL,
    description TEXT,
    organizer_contact VARCHAR(255) NOT NULL,
    is_cancelled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Registrations table
CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, event_id)
);

-- Scheduled reminders table
CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id SERIAL PRIMARY KEY,
    registration_id INTEGER REFERENCES registrations(id) ON DELETE CASCADE,
    remind_at TIMESTAMP NOT NULL,
    reminder_type VARCHAR(10) NOT NULL CHECK (reminder_type IN ('24h', '15min')),
    sent BOOLEAN DEFAULT FALSE
);

-- Index for efficient reminder queries
CREATE INDEX IF NOT EXISTS idx_remind_at_sent ON scheduled_reminders(remind_at, sent);

-- Index for faster event lookups
CREATE INDEX IF NOT EXISTS idx_events_datetime ON events(event_datetime) WHERE NOT is_cancelled;

-- Index for user registrations
CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id) WHERE status = 'active';
"""
