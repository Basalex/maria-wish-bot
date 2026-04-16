import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from bot.database.db import get_db

logger = logging.getLogger(__name__)

async def check_reminders(bot: Bot):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Get dates that are happening in the next 7 days
        # We check if (event_date - current_date) matches the reminder_days setting
        # For simplicity, let's notify if it's exactly 5, 3, or 1 day before
        rows = await conn.fetch("""
            SELECT d.*, u.telegram_id 
            FROM dates d
            JOIN users u ON d.user_id = u.id
        """)
        
        now = datetime.now().date()
        for row in rows:
            event_date = row['event_date']
            # If it's a recurring yearly event (like birthday), adjust year
            event_this_year = event_date.replace(year=now.year)
            if event_this_year < now:
                event_this_year = event_this_year.replace(year=now.year + 1)
            
            days_left = (event_this_year - now).days
            
            if days_left in [7, 5, 3, 1]:
                try:
                    await bot.send_message(
                        row['telegram_id'],
                        f"🔔 <b>Напоминание!</b>\n\nСкоро событие: <b>{row['title']}</b>\n"
                        f"Дата: {event_this_year.strftime('%d.%m.%Y')}\n"
                        f"Осталось дней: {days_left}\n\n"
                        f"Пора подумать о подарке! Спроси меня, если нужны идеи."
                    )
                except Exception as e:
                    logger.error(f"Failed to send reminder to {row['telegram_id']}: {e}")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    # Check every day at 10:00 AM
    scheduler.add_job(check_reminders, 'cron', hour=10, minute=0, args=[bot])
    # Also run once on startup for debugging/immediate check
    scheduler.add_job(check_reminders, args=[bot])
    scheduler.start()
    return scheduler
