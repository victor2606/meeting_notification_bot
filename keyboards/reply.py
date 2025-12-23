"""Reply keyboards for the bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Create main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🗓 Мероприятия"),
                KeyboardButton(text="⚙️ Настройки"),
            ]
        ],
        resize_keyboard=True,
    )
