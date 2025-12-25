import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database.queries import close_pool, init_db
from handlers import admin_router, user_router
from scheduler import setup_scheduler, shutdown_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Register routers
dp.include_router(user_router)
dp.include_router(admin_router)


async def main() -> None:
    logger.info("Initializing database...")
    await init_db()

    logger.info("Starting reminder scheduler...")
    await setup_scheduler(bot)

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await shutdown_scheduler()
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
