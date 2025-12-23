"""Keyboards module for the bot."""

from keyboards.reply import main_menu_kb
from keyboards.inline import (
    # Callback Data Factories
    EventCallback,
    RegistrationCallback,
    SettingsCallback,
    CalendarCallback,
    AdminCallback,
    ReminderCallback,
    # User Keyboards
    event_list_kb,
    event_detail_kb,
    registration_success_kb,
    settings_kb,
    calendar_kb,
    reminder_kb,
    # Admin Keyboards
    admin_menu_kb,
    admin_event_list_kb,
    admin_event_manage_kb,
    create_event_category_kb,
    create_event_format_kb,
    create_event_preview_kb,
    admin_cancel_confirm_kb,
    admin_broadcast_confirm_kb,
    admin_participants_kb,
)

__all__ = [
    # Reply Keyboards
    "main_menu_kb",
    # Callback Data Factories
    "EventCallback",
    "RegistrationCallback",
    "SettingsCallback",
    "CalendarCallback",
    "AdminCallback",
    "ReminderCallback",
    # User Keyboards
    "event_list_kb",
    "event_detail_kb",
    "registration_success_kb",
    "settings_kb",
    "calendar_kb",
    "reminder_kb",
    # Admin Keyboards
    "admin_menu_kb",
    "admin_event_list_kb",
    "admin_event_manage_kb",
    "create_event_category_kb",
    "create_event_format_kb",
    "create_event_preview_kb",
    "admin_cancel_confirm_kb",
    "admin_broadcast_confirm_kb",
    "admin_participants_kb",
]
