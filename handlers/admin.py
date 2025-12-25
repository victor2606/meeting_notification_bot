"""Admin handlers for the bot.

Handlers:
- cmd_admin: /admin command - shows admin menu for authorized users (line 87)
- handle_admin_menu: Back to admin menu callback (line 118)
- handle_admin_event_list: Admin event list with registration counts (line 133)
- handle_admin_event_manage: Show management buttons for a specific event (line 169)
- handle_admin_participants: Show participants list for an event (line 209)
- handle_download_participants: Download participants as CSV (line 260)
- handle_event_broadcast_start: Start FSM for event broadcast (line 318)
- handle_event_broadcast_text: Receive broadcast text and show preview (line 358)
- handle_confirm_event_broadcast: Send broadcast to participants (line 406)
- handle_cancel_event: Show confirmation dialog for event cancellation (line 512)
- handle_confirm_cancel_event: Confirm cancellation and notify participants (line 548)
- handle_create_event_start: Start FSM for event creation (line 657)
- handle_create_event_title: Step 1 - receive event title (line 680)
- handle_create_event_category: Step 2 - receive category selection (line 711)
- handle_create_event_format: Step 3 - receive format selection (line 742)
- handle_create_event_datetime: Step 4 - receive datetime with validation (line 773)
- handle_create_event_location: Step 5 - receive location (line 829)
- handle_create_event_description: Step 6 - receive description (line 858)
- handle_create_event_publish: Publish event and send broadcast (line 914)
- handle_edit_draft: Edit draft - restart from title (line 1007)
- handle_cancel_create: Cancel event creation FSM (line 1029)
"""

import csv
import io
import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database import queries
from keyboards.inline import (
    AdminCallback,
    admin_broadcast_confirm_kb,
    admin_cancel_confirm_kb,
    admin_event_list_kb,
    admin_event_manage_kb,
    admin_menu_kb,
    admin_participants_kb,
    create_event_category_kb,
    create_event_format_kb,
    create_event_preview_kb,
)
from utils.formatters import format_event_detail


# ============== FSM States ==============


class CreateEventStates(StatesGroup):
    """FSM states for step-by-step event creation."""

    waiting_for_title = State()
    waiting_for_category = State()
    waiting_for_format = State()
    waiting_for_datetime = State()
    waiting_for_location = State()
    waiting_for_description = State()
    preview = State()


class EventBroadcastStates(StatesGroup):
    """FSM states for event broadcast."""

    waiting_for_text = State()
    preview = State()

logger = logging.getLogger(__name__)

router = Router(name="admin")


ADMIN_MENU_MESSAGE = """🔐 <b>Панель администратора</b>

Выберите действие:"""

ACCESS_DENIED_MESSAGE = "🚫 У тебя нет доступа к админ-панели."


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Handle /admin command - show admin menu for authorized users."""
    if message.from_user is None:
        logger.error("Message without from_user in cmd_admin")
        return

    user_id = message.from_user.id

    if user_id not in ADMIN_IDS:
        logger.warning(
            "Unauthorized admin access attempt: user_id=%d, username=%s",
            user_id,
            message.from_user.username,
        )
        await message.answer(ACCESS_DENIED_MESSAGE)
        return

    logger.info(
        "Admin panel accessed: user_id=%d, username=%s",
        user_id,
        message.from_user.username,
    )

    await message.answer(
        ADMIN_MENU_MESSAGE,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )


@router.callback_query(AdminCallback.filter(F.action == "menu"))
async def handle_admin_menu(callback: CallbackQuery) -> None:
    """Handle back to admin menu callback."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    await callback.message.edit_text(
        ADMIN_MENU_MESSAGE,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "list"))
async def handle_admin_event_list(callback: CallbackQuery) -> None:
    """Handle admin event list callback - show events with registration counts."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    events = await queries.get_all_events(include_cancelled=False)

    if not events:
        await callback.message.edit_text(
            "📭 <b>Нет активных мероприятий</b>\n\n"
            "Создайте новое мероприятие с помощью кнопки «Создать».",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Add registration count to each event
    events_with_counts = []
    for event in events:
        reg_count = await queries.get_registration_count(event["id"])
        event_with_count = dict(event)
        event_with_count["registrations_count"] = reg_count
        events_with_counts.append(event_with_count)

    await callback.message.edit_text(
        "📋 <b>Мои мероприятия</b>\n\n"
        "Выберите мероприятие для управления:",
        reply_markup=admin_event_list_kb(events_with_counts),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "manage"))
async def handle_admin_event_manage(
    callback: CallbackQuery,
    callback_data: AdminCallback,
) -> None:
    """Handle event management callback - show management buttons for an event."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)

    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    # Get registration count for display
    reg_count = await queries.get_registration_count(event["id"])

    event_info = format_event_detail(event)
    text = (
        f"{event_info}\n\n"
        f"👥 <b>Записалось:</b> {reg_count} чел."
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_event_manage_kb(event["id"]),
        parse_mode="HTML",
    )
    await callback.answer()


# ============== Participants and Broadcast Handlers ==============


@router.callback_query(AdminCallback.filter(F.action == "participants"))
async def handle_admin_participants(
    callback: CallbackQuery,
    callback_data: AdminCallback,
) -> None:
    """Show participants list for an event."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    registrations = await queries.get_event_registrations(callback_data.event_id)

    if not registrations:
        await callback.message.edit_text(
            f"📋 <b>Участники: {event['title']}</b>\n\n"
            "📭 Пока никто не записался на это мероприятие.",
            reply_markup=admin_participants_kb(callback_data.event_id),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Build participants list
    participants_text = f"📋 <b>Участники: {event['title']}</b>\n"
    participants_text += f"👥 Всего записалось: {len(registrations)}\n\n"

    for idx, reg in enumerate(registrations, 1):
        username = reg.get("username")
        first_name = reg.get("first_name", "Без имени")
        if username:
            participants_text += f"{idx}. {first_name} (@{username})\n"
        else:
            participants_text += f"{idx}. {first_name}\n"

    await callback.message.edit_text(
        participants_text,
        reply_markup=admin_participants_kb(callback_data.event_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "download_participants"))
async def handle_download_participants(
    callback: CallbackQuery,
    callback_data: AdminCallback,
) -> None:
    """Download participants list as CSV file."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    registrations = await queries.get_event_registrations(callback_data.event_id)

    if not registrations:
        await callback.answer("Нет участников для скачивания", show_alert=True)
        return

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["#", "Имя", "Username", "Telegram ID", "Дата записи"])

    # Write participants
    for idx, reg in enumerate(registrations, 1):
        writer.writerow([
            idx,
            reg.get("first_name", ""),
            reg.get("username") or "",
            reg.get("telegram_id", ""),
            reg.get("created_at", "").strftime("%d.%m.%Y %H:%M")
            if reg.get("created_at") else "",
        ])

    csv_content = output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility
    output.close()

    # Create filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in event["title"])[:30]
    filename = f"participants_{safe_title}_{callback_data.event_id}.csv"

    await callback.message.answer_document(
        BufferedInputFile(csv_content, filename=filename),
        caption=f"📥 Список участников: {event['title']}\n"
                f"👥 Всего: {len(registrations)} чел.",
    )
    await callback.answer("Файл отправлен")


@router.callback_query(AdminCallback.filter(F.action == "event_broadcast"))
async def handle_event_broadcast_start(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
) -> None:
    """Start FSM for event broadcast - ask for message text."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    reg_count = await queries.get_registration_count(callback_data.event_id)

    if reg_count == 0:
        await callback.answer("Нет участников для рассылки", show_alert=True)
        return

    await state.clear()
    await state.set_state(EventBroadcastStates.waiting_for_text)
    await state.update_data(event_id=callback_data.event_id, event_title=event["title"])

    await callback.message.edit_text(
        f"📢 <b>Рассылка участникам</b>\n\n"
        f"Мероприятие: <b>{event['title']}</b>\n"
        f"Получателей: <b>{reg_count}</b>\n\n"
        "Введите текст сообщения для рассылки:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(StateFilter(EventBroadcastStates.waiting_for_text))
async def handle_event_broadcast_text(
    message: Message,
    state: FSMContext,
) -> None:
    """Receive broadcast text and show preview."""
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        return

    text = message.text
    if not text or len(text.strip()) < 3:
        await message.answer(
            "❌ Сообщение должно содержать минимум 3 символа. Попробуйте ещё раз:",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    event_id = data.get("event_id")
    event_title = data.get("event_title")

    if event_id is None:
        logger.error("Missing event_id in FSM data during broadcast")
        await state.clear()
        await message.answer("Ошибка: данные утеряны. Начните заново.")
        return

    reg_count = await queries.get_registration_count(event_id)

    await state.update_data(broadcast_text=text.strip())
    await state.set_state(EventBroadcastStates.preview)

    preview_message = (
        f"👀 <b>Предпросмотр рассылки</b>\n\n"
        f"📌 Мероприятие: <b>{event_title}</b>\n"
        f"👥 Получателей: <b>{reg_count}</b>\n\n"
        f"📝 <b>Текст сообщения:</b>\n"
        f"<blockquote>{text.strip()}</blockquote>\n\n"
        f"Отправить рассылку?"
    )

    await message.answer(
        preview_message,
        reply_markup=admin_broadcast_confirm_kb(event_id),
        parse_mode="HTML",
    )


@router.callback_query(
    StateFilter(EventBroadcastStates.preview),
    AdminCallback.filter(F.action == "confirm_event_broadcast"),
)
async def handle_confirm_event_broadcast(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Send broadcast to all active participants of the event."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    data = await state.get_data()
    event_id = data.get("event_id")
    event_title = data.get("event_title")
    broadcast_text = data.get("broadcast_text")

    if event_id is None or broadcast_text is None:
        logger.error("Missing data in FSM during broadcast confirm")
        await state.clear()
        await callback.answer("Ошибка: данные утеряны", show_alert=True)
        return

    await state.clear()

    registrations = await queries.get_event_registrations(event_id)

    if not registrations:
        await callback.message.edit_text(
            "📭 Нет активных участников для рассылки.",
            reply_markup=admin_menu_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    # Send broadcast
    successful = 0
    failed = 0
    blocked = 0

    message_text = (
        f"📢 <b>Сообщение от организатора</b>\n\n"
        f"📌 Мероприятие: <b>{event_title}</b>\n\n"
        f"{broadcast_text}"
    )

    for reg in registrations:
        telegram_id = reg.get("telegram_id")
        if telegram_id is None:
            failed += 1
            continue

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode="HTML",
            )
            successful += 1
        except Exception as e:
            error_str = str(e).lower()
            if "blocked" in error_str or "deactivated" in error_str:
                blocked += 1
            else:
                failed += 1
            logger.warning(
                "Failed to send broadcast to user %d: %s",
                telegram_id,
                str(e),
            )

    # Report results
    result_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📌 Мероприятие: <b>{event_title}</b>\n\n"
        f"📊 <b>Результаты:</b>\n"
        f"• ✅ Доставлено: {successful}\n"
        f"• 🚫 Заблокировали бота: {blocked}\n"
        f"• ❌ Ошибки доставки: {failed}"
    )

    await callback.message.edit_text(
        result_text,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Рассылка завершена!")

    logger.info(
        "Event broadcast completed: event_id=%d, successful=%d, blocked=%d, failed=%d, admin=%d",
        event_id,
        successful,
        blocked,
        failed,
        callback.from_user.id,
    )


# ============== Cancel Event Handlers ==============


@router.callback_query(AdminCallback.filter(F.action == "cancel"))
async def handle_cancel_event(
    callback: CallbackQuery,
    callback_data: AdminCallback,
) -> None:
    """Show confirmation dialog for event cancellation."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    if event.get("is_cancelled"):
        await callback.answer("Мероприятие уже отменено", show_alert=True)
        return

    reg_count = await queries.get_registration_count(callback_data.event_id)

    await callback.message.edit_text(
        f"⚠️ <b>Отмена мероприятия</b>\n\n"
        f"📌 <b>{event['title']}</b>\n\n"
        f"Вы уверены, что хотите отменить это мероприятие?\n\n"
        f"👥 Записалось: <b>{reg_count}</b> чел.\n"
        f"Все участники получат уведомление об отмене.",
        reply_markup=admin_cancel_confirm_kb(callback_data.event_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "confirm_cancel"))
async def handle_confirm_cancel_event(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    bot: Bot,
) -> None:
    """Confirm event cancellation, notify participants, and mark reminders as sent."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    if callback_data.event_id is None:
        await callback.answer("Ошибка: не указан ID мероприятия", show_alert=True)
        return

    event = await queries.get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Мероприятие не найдено", show_alert=True)
        return

    if event.get("is_cancelled"):
        await callback.answer("Мероприятие уже отменено", show_alert=True)
        return

    # Get active participants before cancellation
    registrations = await queries.get_event_registrations(callback_data.event_id)

    # Cancel the event
    await queries.cancel_event(callback_data.event_id)

    # Mark all scheduled reminders as sent
    await queries.mark_event_reminders_sent(callback_data.event_id)

    logger.info(
        "Event cancelled: event_id=%d, title=%s, by admin=%d",
        callback_data.event_id,
        event["title"],
        callback.from_user.id,
    )

    # Notify all active participants
    successful = 0
    blocked = 0
    failed = 0

    cancellation_message = (
        f"❌ <b>Мероприятие отменено</b>\n\n"
        f"К сожалению, мероприятие <b>«{event['title']}»</b> было отменено.\n\n"
        f"Приносим извинения за неудобства."
    )

    for reg in registrations:
        telegram_id = reg.get("telegram_id")
        if telegram_id is None:
            failed += 1
            continue

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=cancellation_message,
                parse_mode="HTML",
            )
            successful += 1
        except Exception as e:
            error_str = str(e).lower()
            if "blocked" in error_str or "deactivated" in error_str:
                blocked += 1
            else:
                failed += 1
            logger.warning(
                "Failed to send cancellation notification to user %d: %s",
                telegram_id,
                str(e),
            )

    # Report results to admin
    result_text = (
        f"✅ <b>Мероприятие отменено!</b>\n\n"
        f"📌 <b>{event['title']}</b>\n\n"
        f"📊 <b>Уведомления:</b>\n"
        f"• ✅ Доставлено: {successful}\n"
        f"• 🚫 Заблокировали бота: {blocked}\n"
        f"• ❌ Ошибки доставки: {failed}"
    )

    await callback.message.edit_text(
        result_text,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Мероприятие отменено!")


# ============== Event Creation FSM Handlers ==============


CATEGORY_MAP = {
    "category_it": "IT",
    "category_sport": "Спорт",
    "category_books": "Книги",
}

FORMAT_MAP = {
    "format_online": "онлайн",
    "format_offline": "оффлайн",
}


@router.callback_query(AdminCallback.filter(F.action == "create"))
async def handle_create_event_start(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Start FSM for event creation - ask for title."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    await state.clear()
    await state.set_state(CreateEventStates.waiting_for_title)

    await callback.message.edit_text(
        "📝 <b>Создание мероприятия</b>\n\n"
        "<b>Шаг 1/6:</b> Введите название мероприятия:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(
    StateFilter(CreateEventStates.waiting_for_title),
)
async def handle_create_event_title(
    message: Message,
    state: FSMContext,
) -> None:
    """Step 1: Receive event title and ask for category."""
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        return

    title = message.text
    if not title or len(title.strip()) < 3:
        await message.answer(
            "❌ Название должно содержать минимум 3 символа. Попробуйте ещё раз:",
            parse_mode="HTML",
        )
        return

    await state.update_data(title=title.strip())
    await state.set_state(CreateEventStates.waiting_for_category)

    await message.answer(
        "📝 <b>Создание мероприятия</b>\n\n"
        "<b>Шаг 2/6:</b> Выберите категорию:",
        reply_markup=create_event_category_kb(),
        parse_mode="HTML",
    )


@router.callback_query(
    StateFilter(CreateEventStates.waiting_for_category),
    AdminCallback.filter(F.action.in_(["category_it", "category_sport", "category_books"])),
)
async def handle_create_event_category(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
) -> None:
    """Step 2: Receive category selection and ask for format."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    category = CATEGORY_MAP.get(callback_data.action)
    if category is None:
        await callback.answer("Ошибка: неизвестная категория", show_alert=True)
        return

    await state.update_data(category=category)
    await state.set_state(CreateEventStates.waiting_for_format)

    await callback.message.edit_text(
        "📝 <b>Создание мероприятия</b>\n\n"
        "<b>Шаг 3/6:</b> Выберите формат:",
        reply_markup=create_event_format_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(
    StateFilter(CreateEventStates.waiting_for_format),
    AdminCallback.filter(F.action.in_(["format_online", "format_offline"])),
)
async def handle_create_event_format(
    callback: CallbackQuery,
    callback_data: AdminCallback,
    state: FSMContext,
) -> None:
    """Step 3: Receive format selection and ask for datetime."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    event_format = FORMAT_MAP.get(callback_data.action)
    if event_format is None:
        await callback.answer("Ошибка: неизвестный формат", show_alert=True)
        return

    await state.update_data(format=event_format)
    await state.set_state(CreateEventStates.waiting_for_datetime)

    await callback.message.edit_text(
        "📝 <b>Создание мероприятия</b>\n\n"
        "<b>Шаг 4/6:</b> Введите дату и время мероприятия\n"
        "в формате <code>DD.MM.YYYY HH:MM</code>\n\n"
        "Например: <code>25.12.2024 19:00</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(
    StateFilter(CreateEventStates.waiting_for_datetime),
)
async def handle_create_event_datetime(
    message: Message,
    state: FSMContext,
) -> None:
    """Step 4: Receive datetime with validation and ask for location."""
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        return

    datetime_text = message.text
    if not datetime_text:
        await message.answer(
            "❌ Введите дату и время в формате <code>DD.MM.YYYY HH:MM</code>",
            parse_mode="HTML",
        )
        return

    try:
        event_datetime = datetime.strptime(datetime_text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте формат <code>DD.MM.YYYY HH:MM</code>\n\n"
            "Например: <code>25.12.2024 19:00</code>",
            parse_mode="HTML",
        )
        return

    if event_datetime <= datetime.now():
        await message.answer(
            "❌ Дата мероприятия должна быть в будущем.\n"
            "Введите корректную дату:",
            parse_mode="HTML",
        )
        return

    await state.update_data(event_datetime=event_datetime)
    await state.set_state(CreateEventStates.waiting_for_location)

    data = await state.get_data()
    event_format = data.get("format", "")

    if event_format == "онлайн":
        location_prompt = "Введите ссылку на онлайн-трансляцию:"
    else:
        location_prompt = "Введите адрес проведения:"

    await message.answer(
        f"📝 <b>Создание мероприятия</b>\n\n"
        f"<b>Шаг 5/6:</b> {location_prompt}",
        parse_mode="HTML",
    )


@router.message(
    StateFilter(CreateEventStates.waiting_for_location),
)
async def handle_create_event_location(
    message: Message,
    state: FSMContext,
) -> None:
    """Step 5: Receive location and ask for description."""
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        return

    location = message.text
    if not location or len(location.strip()) < 3:
        await message.answer(
            "❌ Укажите корректное место/ссылку (минимум 3 символа):",
            parse_mode="HTML",
        )
        return

    await state.update_data(location=location.strip())
    await state.set_state(CreateEventStates.waiting_for_description)

    await message.answer(
        "📝 <b>Создание мероприятия</b>\n\n"
        "<b>Шаг 6/6:</b> Введите описание мероприятия:",
        parse_mode="HTML",
    )


@router.message(
    StateFilter(CreateEventStates.waiting_for_description),
)
async def handle_create_event_description(
    message: Message,
    state: FSMContext,
) -> None:
    """Step 6: Receive description and show preview."""
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        return

    description = message.text
    if not description:
        await message.answer(
            "❌ Введите описание мероприятия:",
            parse_mode="HTML",
        )
        return

    # Store organizer contact as the admin's username or ID
    organizer_contact = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else f"tg://user?id={message.from_user.id}"
    )

    await state.update_data(
        description=description.strip(),
        organizer_contact=organizer_contact,
    )
    await state.set_state(CreateEventStates.preview)

    # Build preview
    data = await state.get_data()
    preview_event = {
        "title": data["title"],
        "category": data["category"],
        "format": data["format"],
        "event_datetime": data["event_datetime"],
        "location": data["location"],
        "description": data["description"],
        "organizer_contact": data["organizer_contact"],
    }

    preview_text = format_event_detail(preview_event)

    await message.answer(
        f"👀 <b>Предпросмотр мероприятия</b>\n\n"
        f"{preview_text}\n\n"
        f"Всё верно? Опубликуйте мероприятие или отмените создание.",
        reply_markup=create_event_preview_kb(),
        parse_mode="HTML",
    )


@router.callback_query(
    StateFilter(CreateEventStates.preview),
    AdminCallback.filter(F.action == "publish"),
)
async def handle_create_event_publish(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Publish event to DB and send broadcast to category subscribers."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    data = await state.get_data()

    # Validate all required data is present
    required_fields = ["title", "category", "format", "event_datetime", "location", "organizer_contact"]
    for field in required_fields:
        if field not in data:
            logger.error("Missing field %s in FSM data during publish", field)
            await callback.answer("Ошибка: не все данные заполнены", show_alert=True)
            return

    # Create event in database
    event = await queries.create_event(
        title=data["title"],
        category=data["category"],
        format=data["format"],
        event_datetime=data["event_datetime"],
        location=data["location"],
        organizer_contact=data["organizer_contact"],
        description=data.get("description"),
    )

    logger.info(
        "Event created: id=%d, title=%s, category=%s, by admin=%d",
        event["id"],
        event["title"],
        event["category"],
        callback.from_user.id,
    )

    # Clear FSM state
    await state.clear()

    # Get users subscribed to this category for broadcast
    subscribers = await queries.get_users_by_category(data["category"])

    # Send broadcast to subscribers
    successful = 0
    failed = 0
    broadcast_text = (
        f"🎉 <b>Новое мероприятие!</b>\n\n"
        f"{format_event_detail(event)}"
    )

    for user in subscribers:
        # Don't send to the admin who created the event
        if user["telegram_id"] == callback.from_user.id:
            continue

        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=broadcast_text,
                parse_mode="HTML",
            )
            successful += 1
        except Exception as e:
            logger.warning(
                "Failed to send broadcast to user %d: %s",
                user["telegram_id"],
                str(e),
            )
            failed += 1

    # Report results to admin
    result_text = (
        f"✅ <b>Мероприятие опубликовано!</b>\n\n"
        f"📊 <b>Рассылка:</b>\n"
        f"• Отправлено: {successful}\n"
        f"• Не доставлено: {failed}"
    )

    await callback.message.edit_text(
        result_text,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Мероприятие опубликовано!")


@router.callback_query(
    StateFilter(CreateEventStates.preview),
    AdminCallback.filter(F.action == "edit_draft"),
)
async def handle_edit_draft(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Go back to edit the draft - restart from title."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    # Keep the data but go back to title step
    await state.set_state(CreateEventStates.waiting_for_title)

    await callback.message.edit_text(
        "✏️ <b>Редактирование мероприятия</b>\n\n"
        "<b>Шаг 1/6:</b> Введите название мероприятия\n"
        "(или введите новое название для изменения):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AdminCallback.filter(F.action == "cancel_create"))
async def handle_cancel_create(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Cancel event creation FSM at any stage."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(ACCESS_DENIED_MESSAGE, show_alert=True)
        return

    await state.clear()

    await callback.message.edit_text(
        "❌ Создание мероприятия отменено.\n\n" + ADMIN_MENU_MESSAGE,
        reply_markup=admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
