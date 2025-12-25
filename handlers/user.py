"""User handlers for the bot.

Handlers:
- cmd_start: /start command - creates user, shows welcome (line 45)
- handle_events_button: "🗓 Мероприятия" button - shows events list (line 86)
- handle_settings_button: "⚙️ Настройки" button - shows notification settings (line 132)
- handle_settings_toggle: Settings toggle callback - toggles category notifications (line 156)
- handle_event_detail: Event detail callback - shows full event info (line 221)
- handle_event_list: Back to events list callback (line 258)
- handle_register: Registration callback - creates registration and reminders (line 286)
- handle_cancel_registration: Cancel registration callback (line 343)
- handle_calendar_choose: Calendar service selection (line 391)
- handle_calendar_link: Send calendar link (Google/Yandex) (line 413)
- handle_inline_share: Inline query for sharing events (line 445)
- handle_reminder_confirm: 24h reminder confirm button handler (line 480)
- handle_reminder_decline: 24h reminder decline button handler (line 499)
"""

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from database import queries
from keyboards.inline import (
    CalendarCallback,
    EventCallback,
    RegistrationCallback,
    ReminderCallback,
    SettingsCallback,
    calendar_kb,
    event_detail_kb,
    event_list_kb,
    registration_success_kb,
    settings_kb,
)
from keyboards.reply import main_menu_kb
from utils.calendar_links import google_calendar_url, yandex_calendar_url
from utils.formatters import format_event_card, format_event_detail, format_share_message

logger = logging.getLogger(__name__)

router = Router(name="user")


WELCOME_MESSAGE = """Привет, {first_name}! 👋

Я бот для записи на мероприятия. Здесь ты можешь:

🗓 Посмотреть ближайшие мероприятия и записаться
⚙️ Настроить уведомления по категориям

Используй кнопки меню ниже для навигации."""


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command - create user and show main menu."""
    if message.from_user is None:
        logger.error("Message without from_user in cmd_start")
        return

    user = await queries.create_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )

    logger.info(
        "User started bot: telegram_id=%d, username=%s",
        user["telegram_id"],
        user.get("username"),
    )

    await message.answer(
        WELCOME_MESSAGE.format(first_name=user["first_name"]),
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "🗓 Мероприятия")
async def handle_events_button(message: Message) -> None:
    """Handle events button - show list of upcoming events."""
    events = await queries.get_upcoming_events(limit=10)

    if not events:
        await message.answer(
            "📭 Пока нет запланированных мероприятий.\n\nСледите за обновлениями!"
        )
        return

    text_lines = ["📋 <b>Ближайшие мероприятия:</b>\n"]
    for event in events:
        text_lines.append(format_event_card(event))
        text_lines.append("")

    await message.answer(
        "\n".join(text_lines),
        reply_markup=event_list_kb(events),
        parse_mode="HTML",
    )


# ============== Settings Handlers ==============


SETTINGS_MESSAGE = """⚙️ <b>Настройки уведомлений</b>

Выберите категории мероприятий, о которых вы хотите получать уведомления при их создании:

{status_it} IT-мероприятия
{status_sport} Спорт
{status_books} Книжный клуб

Нажмите на категорию, чтобы включить или выключить уведомления."""


def _format_settings_status(user: dict) -> dict:
    """Format notification status icons for settings message."""
    return {
        "status_it": "✅" if user["notify_it"] else "❌",
        "status_sport": "✅" if user["notify_sport"] else "❌",
        "status_books": "✅" if user["notify_books"] else "❌",
    }


@router.message(F.text == "⚙️ Настройки")
async def handle_settings_button(message: Message) -> None:
    """Handle settings button - show notification preferences."""
    if message.from_user is None:
        logger.error("Message without from_user in handle_settings_button")
        return

    user = await queries.get_user(message.from_user.id)

    if user is None:
        # Create user if not exists (edge case - user deleted and came back)
        user = await queries.create_user(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )

    await message.answer(
        SETTINGS_MESSAGE.format(**_format_settings_status(user)),
        reply_markup=settings_kb(user),
        parse_mode="HTML",
    )


@router.callback_query(SettingsCallback.filter(F.action == "toggle"))
async def handle_settings_toggle(
    callback: CallbackQuery,
    callback_data: SettingsCallback,
) -> None:
    """Handle settings toggle callback - toggle category notification."""
    user = await queries.get_user(callback.from_user.id)

    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    # Map category to database field
    category_field_map = {
        "it": "notify_it",
        "sport": "notify_sport",
        "books": "notify_books",
    }

    field = category_field_map.get(callback_data.category)
    if field is None:
        logger.error("Unknown settings category: %s", callback_data.category)
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    # Toggle the current value
    current_value = user[field]
    new_value = not current_value

    # Update database
    update_kwargs = {field: new_value}
    updated_user = await queries.update_user_notifications(
        callback.from_user.id, **update_kwargs
    )

    if updated_user is None:
        logger.error(
            "Failed to update user notifications: user_id=%d, field=%s",
            callback.from_user.id,
            field,
        )
        await callback.answer("Ошибка при сохранении", show_alert=True)
        return

    logger.info(
        "User updated notification: user_id=%d, %s=%s",
        callback.from_user.id,
        field,
        new_value,
    )

    # Update message with new keyboard
    await callback.message.edit_text(
        SETTINGS_MESSAGE.format(**_format_settings_status(updated_user)),
        reply_markup=settings_kb(updated_user),
        parse_mode="HTML",
    )

    # Show brief confirmation
    category_names = {"it": "IT", "sport": "Спорт", "books": "Книги"}
    category_name = category_names.get(callback_data.category, callback_data.category)
    status = "включены" if new_value else "выключены"
    await callback.answer(f"Уведомления «{category_name}» {status}")


@router.callback_query(EventCallback.filter(F.action == "detail"))
async def handle_event_detail(
    callback: CallbackQuery,
    callback_data: EventCallback,
) -> None:
    """Handle event detail callback - show full event information."""
    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    if event.get("is_cancelled"):
        await callback.answer("Это мероприятие отменено", show_alert=True)
        return

    # Check if user is registered for this event
    user_id = callback.from_user.id
    registration = await queries.get_registration(user_id, event["id"])
    is_registered = registration is not None and registration["status"] == "active"

    await callback.message.edit_text(
        format_event_detail(event),
        reply_markup=event_detail_kb(
            event_id=event["id"],
            is_registered=is_registered,
            organizer_contact=event["organizer_contact"],
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(EventCallback.filter(F.action == "list"))
async def handle_event_list(callback: CallbackQuery) -> None:
    """Handle back to events list callback."""
    events = await queries.get_upcoming_events(limit=10)

    if not events:
        await callback.message.edit_text(
            "📭 Пока нет запланированных мероприятий.\n\nСледите за обновлениями!"
        )
        await callback.answer()
        return

    text_lines = ["📋 <b>Ближайшие мероприятия:</b>\n"]
    for event in events:
        text_lines.append(format_event_card(event))
        text_lines.append("")

    await callback.message.edit_text(
        "\n".join(text_lines),
        reply_markup=event_list_kb(events),
        parse_mode="HTML",
    )
    await callback.answer()


# ============== Registration Handlers ==============


@router.callback_query(RegistrationCallback.filter(F.action == "register"))
async def handle_register(
    callback: CallbackQuery,
    callback_data: RegistrationCallback,
) -> None:
    """Handle registration callback - create registration and reminders."""
    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    if event.get("is_cancelled"):
        await callback.answer("Это мероприятие отменено", show_alert=True)
        return

    user_id = callback.from_user.id

    # Check if already registered
    existing = await queries.get_registration(user_id, event["id"])
    if existing is not None and existing["status"] == "active":
        await callback.answer("Вы уже записаны на это мероприятие", show_alert=True)
        return

    # Create registration
    registration = await queries.create_registration(user_id, event["id"])
    if registration is None:
        logger.error(
            "Failed to create registration: user_id=%d, event_id=%d",
            user_id,
            event["id"],
        )
        await callback.answer("Ошибка при записи. Попробуйте позже.", show_alert=True)
        return

    # Create reminders (24h and 15min before event)
    reminders = await queries.create_reminders(
        registration["id"], event["event_datetime"]
    )

    logger.info(
        "User registered: user_id=%d, event_id=%d, reminders=%d",
        user_id,
        event["id"],
        len(reminders),
    )

    await callback.message.edit_text(
        f"✅ <b>Вы записаны!</b>\n\n"
        f"📌 {event['title']}\n\n"
        f"Мы напомним вам о мероприятии за 24 часа и за 15 минут до начала.",
        reply_markup=registration_success_kb(event["id"]),
        parse_mode="HTML",
    )
    await callback.answer("Вы успешно записались!")


@router.callback_query(RegistrationCallback.filter(F.action == "cancel"))
async def handle_cancel_registration(
    callback: CallbackQuery,
    callback_data: RegistrationCallback,
) -> None:
    """Handle cancel registration callback."""
    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    user_id = callback.from_user.id

    # Get registration to delete its reminders
    registration = await queries.get_registration(user_id, event["id"])
    if registration is None or registration["status"] != "active":
        await callback.answer("Вы не записаны на это мероприятие", show_alert=True)
        return

    # Delete pending reminders for this registration
    await queries.delete_registration_reminders(registration["id"])

    # Cancel registration
    await queries.cancel_registration(user_id, event["id"])

    logger.info(
        "User cancelled registration: user_id=%d, event_id=%d",
        user_id,
        event["id"],
    )

    # Refresh event detail view with updated registration status
    await callback.message.edit_text(
        format_event_detail(event),
        reply_markup=event_detail_kb(
            event_id=event["id"],
            is_registered=False,
            organizer_contact=event["organizer_contact"],
        ),
        parse_mode="HTML",
    )
    await callback.answer("Запись отменена")


# ============== Calendar Handlers ==============


@router.callback_query(CalendarCallback.filter(F.action == "choose"))
async def handle_calendar_choose(
    callback: CallbackQuery,
    callback_data: CalendarCallback,
) -> None:
    """Handle calendar service selection - show Google/Yandex options."""
    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    await callback.message.edit_text(
        f"📅 <b>Добавить в календарь</b>\n\n"
        f"📌 {event['title']}\n\n"
        f"Выберите календарь:",
        reply_markup=calendar_kb(event["id"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(CalendarCallback.filter(F.action.in_({"google", "yandex"})))
async def handle_calendar_link(
    callback: CallbackQuery,
    callback_data: CalendarCallback,
) -> None:
    """Handle calendar link generation - send Google or Yandex calendar URL."""
    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    if callback_data.action == "google":
        url = google_calendar_url(event)
        calendar_name = "Google Calendar"
    else:
        url = yandex_calendar_url(event)
        calendar_name = "Яндекс Календарь"

    await callback.message.answer(
        f"📅 <b>Ссылка для {calendar_name}:</b>\n\n"
        f"👉 <a href=\"{url}\">Добавить в календарь</a>\n\n"
        f"Нажмите на ссылку выше, чтобы добавить мероприятие в ваш календарь.",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


# ============== Share Handler (Inline Query) ==============


@router.inline_query(F.query.startswith("event_"))
async def handle_inline_share(inline_query: InlineQuery, bot: Bot) -> None:
    """Handle inline query for sharing events."""
    try:
        event_id_str = inline_query.query.replace("event_", "")
        event_id = int(event_id_str)
    except ValueError:
        await inline_query.answer(results=[], cache_time=1)
        return

    event = await queries.get_event(event_id)

    if event is None or event.get("is_cancelled"):
        await inline_query.answer(results=[], cache_time=1)
        return

    bot_info = await bot.get_me()
    share_text = format_share_message(event, bot_info.username)

    result = InlineQueryResultArticle(
        id=str(event_id),
        title=event["title"],
        description=f"Поделиться мероприятием: {event['title']}",
        input_message_content=InputTextMessageContent(
            message_text=share_text,
            parse_mode=None,
        ),
    )

    await inline_query.answer(results=[result], cache_time=60)


# ============== Reminder Callback Handlers ==============


@router.callback_query(ReminderCallback.filter(F.action == "confirm"))
async def handle_reminder_confirm(
    callback: CallbackQuery,
    callback_data: ReminderCallback,
) -> None:
    """Handle reminder confirmation - user confirms attendance."""
    logger.info(
        "User confirmed attendance: user_id=%d, registration_id=%d",
        callback.from_user.id,
        callback_data.registration_id,
    )

    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        "Отлично! Ждем вас на мероприятии!"
    )
    await callback.answer("Отлично! Ждем вас!")


@router.callback_query(ReminderCallback.filter(F.action == "decline"))
async def handle_reminder_decline(
    callback: CallbackQuery,
    callback_data: ReminderCallback,
) -> None:
    """Handle reminder decline - cancel registration and 15min reminder."""
    registration_id = callback_data.registration_id

    # Delete pending 15min reminder for this registration
    await queries.delete_registration_reminders(registration_id)

    # We need to get registration to find event_id for cancellation
    # Since we have registration_id, we query via raw pool
    from database.queries import get_pool

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, event_id FROM registrations WHERE id = $1",
            registration_id,
        )

    if row:
        await queries.cancel_registration(row["user_id"], row["event_id"])
        logger.info(
            "User declined, registration cancelled: user_id=%d, event_id=%d",
            row["user_id"],
            row["event_id"],
        )

    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        "Хорошо, ваша запись отменена. Ждем вас на других мероприятиях!"
    )
    await callback.answer("Запись отменена")
