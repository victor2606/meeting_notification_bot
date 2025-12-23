"""Message formatting utilities for events.

Functions:
- format_datetime(dt: datetime) -> str (line 35)
- format_event_card(event: dict) -> str (line 66)
- format_event_detail(event: dict) -> str (line 85)
- format_share_message(event: dict, bot_username: str) -> str (line 117)
"""

from datetime import datetime

# Russian month names in genitive case
MONTHS_GENITIVE = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

# Russian weekday abbreviations
WEEKDAYS_SHORT = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "вс",
}


def format_datetime(dt: datetime) -> str:
    """Format datetime in Russian format: "27 января, пн, 19:00".

    Args:
        dt: datetime object to format

    Returns:
        Formatted string like "27 января, пн, 19:00"
    """
    day = dt.day
    month = MONTHS_GENITIVE[dt.month]
    weekday = WEEKDAYS_SHORT[dt.weekday()]
    time = dt.strftime("%H:%M")
    return f"{day} {month}, {weekday}, {time}"


# Category emoji mapping
CATEGORY_EMOJI = {
    "IT": "💻",
    "Спорт": "🏃",
    "Книги": "📚",
}

# Format emoji mapping
FORMAT_EMOJI = {
    "онлайн": "🌐",
    "оффлайн": "📍",
}


def format_event_card(event: dict) -> str:
    """Format event for list display (short card format).

    Args:
        event: Event dict with keys: title, category, event_datetime, format

    Returns:
        Short formatted string for event list
    """
    category_emoji = CATEGORY_EMOJI.get(event["category"], "📌")
    format_emoji = FORMAT_EMOJI.get(event["format"], "")
    dt_str = format_datetime(event["event_datetime"])

    return (
        f"{category_emoji} <b>{event['title']}</b>\n"
        f"📅 {dt_str} {format_emoji}"
    )


def format_event_detail(event: dict) -> str:
    """Format full event details for detail view.

    Args:
        event: Event dict with all event fields

    Returns:
        Full formatted string with all event information
    """
    category_emoji = CATEGORY_EMOJI.get(event["category"], "📌")
    format_emoji = FORMAT_EMOJI.get(event["format"], "")
    dt_str = format_datetime(event["event_datetime"])

    lines = [
        f"{category_emoji} <b>{event['title']}</b>",
        "",
        f"📅 <b>Дата:</b> {dt_str}",
        f"🏷 <b>Категория:</b> {event['category']}",
        f"{format_emoji} <b>Формат:</b> {event['format']}",
        f"📍 <b>Место:</b> {event['location']}",
    ]

    if event.get("description"):
        lines.append("")
        lines.append(f"📝 {event['description']}")

    if event.get("organizer_contact"):
        lines.append("")
        lines.append(f"👤 <b>Организатор:</b> {event['organizer_contact']}")

    return "\n".join(lines)


def format_share_message(event: dict, bot_username: str) -> str:
    """Format event for sharing via forward/link.

    Args:
        event: Event dict with event fields
        bot_username: Bot's username for deep link

    Returns:
        Share-friendly formatted message with bot link
    """
    category_emoji = CATEGORY_EMOJI.get(event["category"], "📌")
    dt_str = format_datetime(event["event_datetime"])

    lines = [
        f"{category_emoji} {event['title']}",
        "",
        f"📅 {dt_str}",
        f"📍 {event['location']}",
    ]

    if event.get("description"):
        # Truncate long descriptions for sharing
        desc = event["description"]
        if len(desc) > 100:
            desc = desc[:97] + "..."
        lines.append(f"📝 {desc}")

    lines.append("")
    event_id = event["id"]
    lines.append(f"👉 Записаться: https://t.me/{bot_username}?start=event_{event_id}")

    return "\n".join(lines)
