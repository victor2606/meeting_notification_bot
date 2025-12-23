"""Calendar link generators for Google and Yandex calendars.

Functions:
- google_calendar_url(event: dict) -> str (line 12)
- yandex_calendar_url(event: dict) -> str (line 47)
"""

from datetime import datetime, timedelta
from urllib.parse import quote


def google_calendar_url(event: dict) -> str:
    """Generate a Google Calendar event creation URL.

    Args:
        event: Event dict with keys: title, event_datetime, location, description, category, format

    Returns:
        URL string for adding event to Google Calendar
    """
    event_dt: datetime = event["event_datetime"]
    # Default event duration: 2 hours
    end_dt = event_dt + timedelta(hours=2)

    # Google Calendar expects dates in UTC format: YYYYMMDDTHHMMSSZ
    date_format = "%Y%m%dT%H%M%SZ"
    dates = f"{event_dt.strftime(date_format)}/{end_dt.strftime(date_format)}"

    title = event["title"]
    location = event["location"]

    # Build description with category and format
    description_parts = []
    if event.get("description"):
        description_parts.append(event["description"])
    description_parts.append(f"Категория: {event['category']}")
    description_parts.append(f"Формат: {event['format']}")
    if event.get("organizer_contact"):
        description_parts.append(f"Организатор: {event['organizer_contact']}")
    description = "\n".join(description_parts)

    base_url = "https://calendar.google.com/calendar/render"
    params = (
        f"?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={dates}"
        f"&location={quote(location)}"
        f"&details={quote(description)}"
    )
    return base_url + params


def yandex_calendar_url(event: dict) -> str:
    """Generate a Yandex Calendar event creation URL.

    Args:
        event: Event dict with keys: title, event_datetime, location, description, category, format

    Returns:
        URL string for adding event to Yandex Calendar
    """
    event_dt: datetime = event["event_datetime"]
    # Default event duration: 2 hours
    end_dt = event_dt + timedelta(hours=2)

    title = event["title"]
    location = event["location"]

    # Build description with category and format
    description_parts = []
    if event.get("description"):
        description_parts.append(event["description"])
    description_parts.append(f"Категория: {event['category']}")
    description_parts.append(f"Формат: {event['format']}")
    if event.get("organizer_contact"):
        description_parts.append(f"Организатор: {event['organizer_contact']}")
    description = "\n".join(description_parts)

    # Yandex Calendar uses ISO format with timezone
    # Format: YYYY-MM-DDTHH:MM:SS
    date_format = "%Y-%m-%dT%H:%M:%S"

    base_url = "https://calendar.yandex.ru/event"
    params = (
        f"?startTs={quote(event_dt.strftime(date_format))}"
        f"&endTs={quote(end_dt.strftime(date_format))}"
        f"&name={quote(title)}"
        f"&where={quote(location)}"
        f"&description={quote(description)}"
    )
    return base_url + params
