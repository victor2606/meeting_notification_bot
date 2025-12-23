"""Inline keyboards and callback data factories for the bot."""

from typing import Any, Dict, List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


# ============== Callback Data Factories ==============

class EventCallback(CallbackData, prefix="event"):
    """Callback data for event actions."""
    action: str  # "detail", "list"
    event_id: Optional[int] = None


class RegistrationCallback(CallbackData, prefix="reg"):
    """Callback data for registration actions."""
    action: str  # "register", "cancel"
    event_id: int


class SettingsCallback(CallbackData, prefix="settings"):
    """Callback data for settings toggles."""
    action: str  # "toggle"
    category: str  # "it", "sport", "books"


class CalendarCallback(CallbackData, prefix="cal"):
    """Callback data for calendar actions."""
    action: str  # "google", "yandex"
    event_id: int


class AdminCallback(CallbackData, prefix="admin"):
    """Callback data for admin actions."""
    action: str  # "create", "list", "broadcast", "participants", "edit", "cancel"
    event_id: Optional[int] = None


class ReminderCallback(CallbackData, prefix="remind"):
    """Callback data for reminder responses."""
    action: str  # "confirm", "decline"
    registration_id: int


# ============== User Keyboards ==============

def event_list_kb(events: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Create keyboard with event list buttons."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"📌 {event['title']}",
                callback_data=EventCallback(action="detail", event_id=event["id"]).pack()
            )
        ]
        for event in events
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_detail_kb(event_id: int, is_registered: bool, organizer_contact: str) -> InlineKeyboardMarkup:
    """Create keyboard for event details with registration/cancel buttons."""
    buttons = []

    if is_registered:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить запись",
                callback_data=RegistrationCallback(action="cancel", event_id=event_id).pack()
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Записаться",
                callback_data=RegistrationCallback(action="register", event_id=event_id).pack()
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="📅 В календарь",
            callback_data=CalendarCallback(action="choose", event_id=event_id).pack()
        ),
        InlineKeyboardButton(
            text="📤 Поделиться",
            switch_inline_query=f"event_{event_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="👤 Связаться с организатором",
            url=organizer_contact if organizer_contact.startswith("http") else f"https://t.me/{organizer_contact.lstrip('@')}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data=EventCallback(action="list").pack()
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def registration_success_kb(event_id: int) -> InlineKeyboardMarkup:
    """Create keyboard after successful registration."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Добавить в календарь",
                callback_data=CalendarCallback(action="choose", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ К мероприятию",
                callback_data=EventCallback(action="detail", event_id=event_id).pack()
            )
        ]
    ])


def settings_kb(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Create settings keyboard with category toggles."""
    def toggle_icon(enabled: bool) -> str:
        return "✅" if enabled else "❌"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{toggle_icon(user['notify_it'])} IT-мероприятия",
                callback_data=SettingsCallback(action="toggle", category="it").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{toggle_icon(user['notify_sport'])} Спорт",
                callback_data=SettingsCallback(action="toggle", category="sport").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{toggle_icon(user['notify_books'])} Книжный клуб",
                callback_data=SettingsCallback(action="toggle", category="books").pack()
            )
        ]
    ])


def calendar_kb(event_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for calendar service selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 Google Calendar",
                callback_data=CalendarCallback(action="google", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Яндекс Календарь",
                callback_data=CalendarCallback(action="yandex", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=EventCallback(action="detail", event_id=event_id).pack()
            )
        ]
    ])


def reminder_kb(registration_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for 24h reminder response."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, буду",
                callback_data=ReminderCallback(action="confirm", registration_id=registration_id).pack()
            ),
            InlineKeyboardButton(
                text="❌ Не смогу",
                callback_data=ReminderCallback(action="decline", registration_id=registration_id).pack()
            )
        ]
    ])


# ============== Admin Keyboards ==============

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Create admin panel main menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Создать мероприятие",
                callback_data=AdminCallback(action="create").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои мероприятия",
                callback_data=AdminCallback(action="list").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Рассылка по категории",
                callback_data=AdminCallback(action="broadcast").pack()
            )
        ]
    ])


def admin_event_list_kb(events: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Create admin event list with management buttons."""
    buttons = []
    for event in events:
        reg_count = event.get("registrations_count", 0)
        buttons.append([
            InlineKeyboardButton(
                text=f"📌 {event['title']} ({reg_count} чел.)",
                callback_data=AdminCallback(action="manage", event_id=event["id"]).pack()
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data=AdminCallback(action="menu").pack()
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_event_manage_kb(event_id: int) -> InlineKeyboardMarkup:
    """Create management keyboard for a specific event."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👥 Участники",
                callback_data=AdminCallback(action="participants", event_id=event_id).pack()
            ),
            InlineKeyboardButton(
                text="📢 Рассылка",
                callback_data=AdminCallback(action="event_broadcast", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=AdminCallback(action="edit", event_id=event_id).pack()
            ),
            InlineKeyboardButton(
                text="🗑 Отменить",
                callback_data=AdminCallback(action="cancel", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад к списку",
                callback_data=AdminCallback(action="list").pack()
            )
        ]
    ])


def create_event_category_kb() -> InlineKeyboardMarkup:
    """Create keyboard for event category selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💻 IT",
                callback_data=AdminCallback(action="category_it").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⚽️ Спорт",
                callback_data=AdminCallback(action="category_sport").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Книги",
                callback_data=AdminCallback(action="category_books").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCallback(action="cancel_create").pack()
            )
        ]
    ])


def create_event_format_kb() -> InlineKeyboardMarkup:
    """Create keyboard for event format selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🌐 Онлайн",
                callback_data=AdminCallback(action="format_online").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="📍 Оффлайн",
                callback_data=AdminCallback(action="format_offline").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCallback(action="cancel_create").pack()
            )
        ]
    ])


def create_event_preview_kb() -> InlineKeyboardMarkup:
    """Create keyboard for event preview confirmation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Опубликовать",
                callback_data=AdminCallback(action="publish").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=AdminCallback(action="edit_draft").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCallback(action="cancel_create").pack()
            )
        ]
    ])


def admin_cancel_confirm_kb(event_id: int) -> InlineKeyboardMarkup:
    """Create confirmation keyboard for event cancellation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, отменить",
                callback_data=AdminCallback(action="confirm_cancel", event_id=event_id).pack()
            ),
            InlineKeyboardButton(
                text="❌ Нет, вернуться",
                callback_data=AdminCallback(action="manage", event_id=event_id).pack()
            )
        ]
    ])


def admin_broadcast_confirm_kb(event_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create confirmation keyboard for broadcast."""
    action = "confirm_event_broadcast" if event_id else "confirm_broadcast"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Отправить",
                callback_data=AdminCallback(action=action, event_id=event_id).pack()
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=AdminCallback(action="list" if event_id else "menu", event_id=event_id).pack()
            )
        ]
    ])


def admin_participants_kb(event_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for participants list."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📥 Скачать список",
                callback_data=AdminCallback(action="download_participants", event_id=event_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminCallback(action="manage", event_id=event_id).pack()
            )
        ]
    ])
