import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database.queries import close_pool, init_db
from handlers import user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Register routers
dp.include_router(user_router)


async def main() -> None:
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
