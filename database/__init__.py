"""Database module for event bot."""

from database.queries import (
    # Connection management
    get_pool,
    close_pool,
    init_db,
    # User functions
    create_user,
    get_user,
    update_user_notifications,
    get_users_by_category,
    # Event functions
    create_event,
    get_event,
    get_upcoming_events,
    cancel_event,
    get_all_events,
    # Registration functions
    create_registration,
    cancel_registration,
    get_registration,
    get_event_registrations,
    get_user_registrations,
    get_registration_count,
    # Reminder functions
    create_reminders,
    get_pending_reminders,
    mark_reminder_sent,
    delete_registration_reminders,
    mark_event_reminders_sent,
)

__all__ = [
    # Connection management
    "get_pool",
    "close_pool",
    "init_db",
    # User functions
    "create_user",
    "get_user",
    "update_user_notifications",
    "get_users_by_category",
    # Event functions
    "create_event",
    "get_event",
    "get_upcoming_events",
    "cancel_event",
    "get_all_events",
    # Registration functions
    "create_registration",
    "cancel_registration",
    "get_registration",
    "get_event_registrations",
    "get_user_registrations",
    "get_registration_count",
    # Reminder functions
    "create_reminders",
    "get_pending_reminders",
    "mark_reminder_sent",
    "delete_registration_reminders",
    "mark_event_reminders_sent",
]
