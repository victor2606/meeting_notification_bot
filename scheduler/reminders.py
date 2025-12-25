"""Background reminder scheduler using APScheduler.

Functions:
- setup_scheduler(bot: Bot) -> None: Initialize and start the scheduler (line 35)
- shutdown_scheduler() -> None: Graceful shutdown of the scheduler (line 52)
- process_reminders(bot: Bot) -> None: Check and send pending reminders (line 62)
- send_24h_reminder(bot: Bot, reminder: dict) -> bool: Send 24h reminder with buttons (line 95)
- send_15min_reminder(bot: Bot, reminder: dict) -> bool: Send 15min reminder with location (line 130)
"""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import queries
from keyboards.inline import reminder_kb
from utils.formatters import format_datetime

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None
_bot: Optional[Bot] = None


async def setup_scheduler(bot: Bot) -> None:
    """Initialize and start the APScheduler.

    Args:
        bot: aiogram Bot instance for sending messages
    """
    global _scheduler, _bot
    _bot = bot

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _process_reminders_job,
        "interval",
        minutes=1,
        id="process_reminders",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Reminder scheduler started")


async def shutdown_scheduler() -> None:
    """Gracefully shutdown the scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("Reminder scheduler stopped")
        _scheduler = None


async def _process_reminders_job() -> None:
    """Job wrapper to process reminders with bot instance."""
    if _bot is None:
        logger.error("Bot instance not set in scheduler")
        return
    await process_reminders(_bot)


async def process_reminders(bot: Bot) -> None:
    """Check and send all pending reminders.

    Fetches reminders where remind_at <= now() AND sent = FALSE,
    sends appropriate message based on reminder type (24h or 15min),
    and marks reminder as sent.

    Args:
        bot: aiogram Bot instance for sending messages
    """
    pending = await queries.get_pending_reminders()

    if not pending:
        return

    logger.info("Processing %d pending reminders", len(pending))

    for reminder in pending:
        try:
            if reminder["reminder_type"] == "24h":
                success = await send_24h_reminder(bot, reminder)
            else:
                success = await send_15min_reminder(bot, reminder)

            if success:
                await queries.mark_reminder_sent(reminder["id"])
                logger.info(
                    "Sent %s reminder: user_id=%d, event_id=%d",
                    reminder["reminder_type"],
                    reminder["user_id"],
                    reminder["event_id"],
                )
        except Exception as e:
            logger.error(
                "Failed to process reminder %d: %s",
                reminder["id"],
                str(e),
            )


async def send_24h_reminder(bot: Bot, reminder: dict) -> bool:
    """Send 24-hour reminder with confirmation buttons.

    Args:
        bot: aiogram Bot instance
        reminder: Reminder dict with user_id, event_id, title, etc.

    Returns:
        True if message was sent successfully, False if user blocked bot
    """
    dt_str = format_datetime(reminder["event_datetime"])

    text = (
        f"Напоминание о мероприятии!\n\n"
        f"{reminder['title']}\n"
        f"{dt_str}\n\n"
        f"Вы все еще планируете посетить?"
    )

    try:
        await bot.send_message(
            chat_id=reminder["user_id"],
            text=text,
            reply_markup=reminder_kb(reminder["registration_id"]),
        )
        return True
    except TelegramForbiddenError:
        logger.warning(
            "User %d blocked the bot, skipping reminder",
            reminder["user_id"],
        )
        # Mark as sent to avoid retrying
        return True
    except Exception as e:
        logger.error(
            "Error sending 24h reminder to user %d: %s",
            reminder["user_id"],
            str(e),
        )
        raise


async def send_15min_reminder(bot: Bot, reminder: dict) -> bool:
    """Send 15-minute reminder with event location.

    Args:
        bot: aiogram Bot instance
        reminder: Reminder dict with user_id, event_id, title, location, etc.

    Returns:
        True if message was sent successfully, False if user blocked bot
    """
    dt_str = format_datetime(reminder["event_datetime"])

    text = (
        f"Мероприятие через 15 минут!\n\n"
        f"{reminder['title']}\n"
        f"{dt_str}\n\n"
        f"{reminder['location']}"
    )

    try:
        await bot.send_message(
            chat_id=reminder["user_id"],
            text=text,
        )
        return True
    except TelegramForbiddenError:
        logger.warning(
            "User %d blocked the bot, skipping 15min reminder",
            reminder["user_id"],
        )
        return True
    except Exception as e:
        logger.error(
            "Error sending 15min reminder to user %d: %s",
            reminder["user_id"],
            str(e),
        )
        raise
