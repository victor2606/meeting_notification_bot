"""Database queries and CRUD operations."""

from datetime import datetime, timedelta
from typing import Optional

import asyncpg

from config import DATABASE_URL
from database.models import INIT_TABLES_SQL

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    """Initialize database tables."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(INIT_TABLES_SQL)


# ============== User Functions ==============


async def create_user(
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None
) -> dict:
    """Create a new user or return existing one."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (telegram_id, first_name, username)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                username = EXCLUDED.username
            RETURNING *
            """,
            telegram_id, first_name, username
        )
        return dict(row)


async def get_user(telegram_id: int) -> Optional[dict]:
    """Get user by telegram_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            telegram_id
        )
        return dict(row) if row else None


async def update_user_notifications(
    telegram_id: int,
    notify_it: Optional[bool] = None,
    notify_sport: Optional[bool] = None,
    notify_books: Optional[bool] = None
) -> Optional[dict]:
    """Update user notification preferences."""
    pool = await get_pool()

    updates = []
    params = []
    param_idx = 1

    if notify_it is not None:
        updates.append(f"notify_it = ${param_idx}")
        params.append(notify_it)
        param_idx += 1
    if notify_sport is not None:
        updates.append(f"notify_sport = ${param_idx}")
        params.append(notify_sport)
        param_idx += 1
    if notify_books is not None:
        updates.append(f"notify_books = ${param_idx}")
        params.append(notify_books)
        param_idx += 1

    if not updates:
        return await get_user(telegram_id)

    params.append(telegram_id)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE users SET {', '.join(updates)}
            WHERE telegram_id = ${param_idx}
            RETURNING *
            """,
            *params
        )
        return dict(row) if row else None


async def get_users_by_category(category: str) -> list[dict]:
    """Get users subscribed to a category."""
    pool = await get_pool()

    category_field = {
        "IT": "notify_it",
        "Спорт": "notify_sport",
        "Книги": "notify_books"
    }.get(category)

    if not category_field:
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM users WHERE {category_field} = TRUE"
        )
        return [dict(row) for row in rows]


# ============== Event Functions ==============


async def create_event(
    title: str,
    category: str,
    format: str,
    event_datetime: datetime,
    location: str,
    organizer_contact: str,
    description: Optional[str] = None
) -> dict:
    """Create a new event."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO events (title, category, format, event_datetime, location, description, organizer_contact)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            title, category, format, event_datetime, location, description, organizer_contact
        )
        return dict(row)


async def get_event(event_id: int) -> Optional[dict]:
    """Get event by id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM events WHERE id = $1",
            event_id
        )
        return dict(row) if row else None


async def get_upcoming_events(
    category: Optional[str] = None,
    limit: int = 10
) -> list[dict]:
    """Get upcoming events, optionally filtered by category."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if category:
            rows = await conn.fetch(
                """
                SELECT * FROM events
                WHERE event_datetime > NOW()
                    AND is_cancelled = FALSE
                    AND category = $1
                ORDER BY event_datetime ASC
                LIMIT $2
                """,
                category, limit
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM events
                WHERE event_datetime > NOW()
                    AND is_cancelled = FALSE
                ORDER BY event_datetime ASC
                LIMIT $1
                """,
                limit
            )
        return [dict(row) for row in rows]


async def cancel_event(event_id: int) -> Optional[dict]:
    """Cancel an event."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE events SET is_cancelled = TRUE
            WHERE id = $1
            RETURNING *
            """,
            event_id
        )
        return dict(row) if row else None


async def get_all_events(include_cancelled: bool = False) -> list[dict]:
    """Get all events for admin view."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if include_cancelled:
            rows = await conn.fetch(
                "SELECT * FROM events ORDER BY event_datetime DESC"
            )
        else:
            rows = await conn.fetch(
                """
                SELECT * FROM events
                WHERE is_cancelled = FALSE
                ORDER BY event_datetime DESC
                """
            )
        return [dict(row) for row in rows]


# ============== Registration Functions ==============


async def create_registration(user_id: int, event_id: int) -> Optional[dict]:
    """Create or reactivate a registration."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO registrations (user_id, event_id, status)
            VALUES ($1, $2, 'active')
            ON CONFLICT (user_id, event_id) DO UPDATE SET status = 'active'
            RETURNING *
            """,
            user_id, event_id
        )
        return dict(row) if row else None


async def cancel_registration(user_id: int, event_id: int) -> Optional[dict]:
    """Cancel a registration."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE registrations SET status = 'cancelled'
            WHERE user_id = $1 AND event_id = $2
            RETURNING *
            """,
            user_id, event_id
        )
        return dict(row) if row else None


async def get_registration(user_id: int, event_id: int) -> Optional[dict]:
    """Get registration for a user and event."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM registrations
            WHERE user_id = $1 AND event_id = $2
            """,
            user_id, event_id
        )
        return dict(row) if row else None


async def get_event_registrations(event_id: int, active_only: bool = True) -> list[dict]:
    """Get all registrations for an event with user info."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if active_only:
            rows = await conn.fetch(
                """
                SELECT r.*, u.username, u.first_name, u.telegram_id
                FROM registrations r
                JOIN users u ON r.user_id = u.telegram_id
                WHERE r.event_id = $1 AND r.status = 'active'
                ORDER BY r.created_at
                """,
                event_id
            )
        else:
            rows = await conn.fetch(
                """
                SELECT r.*, u.username, u.first_name, u.telegram_id
                FROM registrations r
                JOIN users u ON r.user_id = u.telegram_id
                WHERE r.event_id = $1
                ORDER BY r.created_at
                """,
                event_id
            )
        return [dict(row) for row in rows]


async def get_user_registrations(user_id: int, active_only: bool = True) -> list[dict]:
    """Get all registrations for a user with event info."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if active_only:
            rows = await conn.fetch(
                """
                SELECT r.*, e.title, e.category, e.format, e.event_datetime, e.location
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE r.user_id = $1 AND r.status = 'active' AND e.is_cancelled = FALSE
                ORDER BY e.event_datetime
                """,
                user_id
            )
        else:
            rows = await conn.fetch(
                """
                SELECT r.*, e.title, e.category, e.format, e.event_datetime, e.location
                FROM registrations r
                JOIN events e ON r.event_id = e.id
                WHERE r.user_id = $1
                ORDER BY e.event_datetime
                """,
                user_id
            )
        return [dict(row) for row in rows]


async def get_registration_count(event_id: int) -> int:
    """Get count of active registrations for an event."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT COUNT(*) FROM registrations
            WHERE event_id = $1 AND status = 'active'
            """,
            event_id
        )
        return result or 0


# ============== Reminder Functions ==============


async def create_reminders(registration_id: int, event_datetime: datetime) -> list[dict]:
    """Create 24h and 15min reminders for a registration."""
    pool = await get_pool()

    remind_24h = event_datetime - timedelta(hours=24)
    remind_15min = event_datetime - timedelta(minutes=15)
    now = datetime.utcnow()

    reminders = []

    async with pool.acquire() as conn:
        # Only create reminders that are in the future
        if remind_24h > now:
            row = await conn.fetchrow(
                """
                INSERT INTO scheduled_reminders (registration_id, remind_at, reminder_type)
                VALUES ($1, $2, '24h')
                RETURNING *
                """,
                registration_id, remind_24h
            )
            if row:
                reminders.append(dict(row))

        if remind_15min > now:
            row = await conn.fetchrow(
                """
                INSERT INTO scheduled_reminders (registration_id, remind_at, reminder_type)
                VALUES ($1, $2, '15min')
                RETURNING *
                """,
                registration_id, remind_15min
            )
            if row:
                reminders.append(dict(row))

    return reminders


async def get_pending_reminders() -> list[dict]:
    """Get all unsent reminders that should be sent now."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT sr.*, r.user_id, r.event_id, e.title, e.location, e.event_datetime,
                   e.category, e.format, u.first_name
            FROM scheduled_reminders sr
            JOIN registrations r ON sr.registration_id = r.id
            JOIN events e ON r.event_id = e.id
            JOIN users u ON r.user_id = u.telegram_id
            WHERE sr.remind_at <= NOW()
                AND sr.sent = FALSE
                AND r.status = 'active'
                AND e.is_cancelled = FALSE
            ORDER BY sr.remind_at
            """
        )
        return [dict(row) for row in rows]


async def mark_reminder_sent(reminder_id: int) -> None:
    """Mark a reminder as sent."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE scheduled_reminders SET sent = TRUE WHERE id = $1",
            reminder_id
        )


async def delete_registration_reminders(registration_id: int) -> None:
    """Delete unsent reminders for a registration (used when cancelling)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM scheduled_reminders WHERE registration_id = $1 AND sent = FALSE",
            registration_id
        )


async def mark_event_reminders_sent(event_id: int) -> None:
    """Mark all reminders for an event as sent (used when cancelling event)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE scheduled_reminders SET sent = TRUE
            WHERE registration_id IN (
                SELECT id FROM registrations WHERE event_id = $1
            ) AND sent = FALSE
            """,
            event_id
        )
