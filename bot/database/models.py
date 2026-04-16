from bot.database.db import get_db
from datetime import datetime

async def get_or_create_user(telegram_id: int, username: str = None):
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        if row:
            return row
        
        await conn.execute(
            "INSERT INTO users (telegram_id, username) VALUES ($1, $2) ON CONFLICT (telegram_id) DO NOTHING",
            telegram_id, username
        )
        return await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)

async def save_wish(user_id: int, wish_data: dict):
    if not wish_data or not wish_data.get('title'): return
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO wishes (user_id, title, description, price_range, link) VALUES ($1, $2, $3, $4, $5)",
            user_id, wish_data.get('title'), wish_data.get('description'), 
            wish_data.get('price_range'), wish_data.get('link')
        )

async def save_date(user_id: int, date_data: dict):
    if not date_data or not date_data.get('event_date'): return
    pool = await get_db()
    try:
        event_date = datetime.strptime(date_data.get('event_date'), '%Y-%m-%d').date()
    except:
        return
        
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO dates (user_id, title, event_date, reminder_days) VALUES ($1, $2, $3, $4)",
            user_id, date_data.get('title'), event_date, date_data.get('reminder_days', 7)
        )

async def save_note(user_id: int, note_data: dict):
    if not note_data or not note_data.get('content'): return
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO notes (user_id, content, category) VALUES ($1, $2, $3)",
            user_id, note_data.get('content'), note_data.get('category', 'other')
        )

async def get_user_context(user_id: int) -> dict:
    pool = await get_db()
    async with pool.acquire() as conn:
        wishes = await conn.fetch("SELECT * FROM wishes WHERE user_id = $1 AND is_granted = FALSE", user_id)
        dates = await conn.fetch("SELECT * FROM dates WHERE user_id = $1", user_id)
        notes = await conn.fetch("SELECT * FROM notes WHERE user_id = $1", user_id)
        
        return {
            'wishes': [dict(w) for w in wishes],
            'dates': [dict(d) for d in dates],
            'notes': [dict(n) for n in notes]
        }

async def get_wishes_formatted(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM wishes WHERE user_id = $1 AND is_granted = FALSE ORDER BY created_at DESC", user_id)
        if not rows: return "Список пока пуст."
        return "\n".join([f"• {r['title']} ({r['price_range'] or 'цена не указана'})" for r in rows])

async def get_notes_formatted(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM notes WHERE user_id = $1 ORDER BY created_at DESC", user_id)
        if not rows: return "Заметок пока нет."
        return "\n".join([f"• {r['content']} [#{r['category'] or 'другое'}]" for r in rows])
