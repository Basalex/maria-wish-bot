import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN
from bot.database.db import init_db, close_db
from bot.handlers import setup_routers
from bot.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="wishes", description="Желания: Список"),
        BotCommand(command="wishes_add", description="Желания: Добавить"),
        BotCommand(command="dates", description="Даты: Список"),
        BotCommand(command="dates_add", description="Даты: Добавить"),
        BotCommand(command="notes", description="Заметки: Список"),
        BotCommand(command="notes_add", description="Заметки: Добавить"),
        BotCommand(command="stats", description="Статистика подарков"),
        BotCommand(command="help", description="Все команды (CRUD)"),
    ]
    await bot.set_my_commands(commands)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        return

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Setup commands menu
    await set_commands(bot)
    
    # Setup handlers
    setup_routers(dp)

    # Setup scheduler
    scheduler = setup_scheduler(bot)

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
