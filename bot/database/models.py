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

# WISHES CRUD
async def save_wish(user_id: int, wish_data: dict):
    if not wish_data or not wish_data.get('title'): return
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO wishes (user_id, title, description, price_range, link) VALUES ($1, $2, $3, $4, $5)",
            user_id, wish_data.get('title'), wish_data.get('description'), 
            wish_data.get('price_range'), wish_data.get('link')
        )

async def update_wish(user_id: int, wish_id: int, wish_data: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        fields = []
        params = [wish_id, user_id]
        if 'title' in wish_data and wish_data['title']:
            fields.append(f"title = ${len(params)+1}")
            params.append(wish_data['title'])
        if 'description' in wish_data:
            fields.append(f"description = ${len(params)+1}")
            params.append(wish_data['description'])
        if 'price_range' in wish_data:
            fields.append(f"price_range = ${len(params)+1}")
            params.append(wish_data['price_range'])
        if 'link' in wish_data:
            fields.append(f"link = ${len(params)+1}")
            params.append(wish_data['link'])
        if not fields: return
        query = f"UPDATE wishes SET {', '.join(fields)} WHERE id = $1 AND user_id = $2"
        await conn.execute(query, *params)

async def delete_wish(user_id: int, wish_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM wishes WHERE id = $1 AND user_id = $2", wish_id, user_id)

async def complete_wish(user_id: int, wish_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE wishes SET is_granted = TRUE WHERE id = $1 AND user_id = $2", wish_id, user_id)

# DATES CRUD
async def save_date(user_id: int, date_data: dict):
    if not date_data or not date_data.get('event_date'): return
    pool = await get_db()
    try:
        event_date = datetime.strptime(date_data.get('event_date'), '%Y-%m-%d').date()
    except: return
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO dates (user_id, title, event_date, reminder_days) VALUES ($1, $2, $3, $4)",
            user_id, date_data.get('title'), event_date, date_data.get('reminder_days', 7)
        )

async def update_date(user_id: int, date_id: int, date_data: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        fields = []
        params = [date_id, user_id]
        if 'title' in date_data and date_data['title']:
            fields.append(f"title = ${len(params)+1}")
            params.append(date_data['title'])
        if 'event_date' in date_data:
            try:
                event_date = datetime.strptime(date_data['event_date'], '%Y-%m-%d').date()
                fields.append(f"event_date = ${len(params)+1}")
                params.append(event_date)
            except: pass
        if 'reminder_days' in date_data:
            fields.append(f"reminder_days = ${len(params)+1}")
            params.append(int(date_data['reminder_days']))
        if not fields: return
        query = f"UPDATE dates SET {', '.join(fields)} WHERE id = $1 AND user_id = $2"
        await conn.execute(query, *params)

async def delete_date(user_id: int, date_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM dates WHERE id = $1 AND user_id = $2", date_id, user_id)

# NOTES CRUD
async def save_note(user_id: int, note_data: dict):
    if not note_data or not note_data.get('content'): return
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO notes (user_id, content, category) VALUES ($1, $2, $3)",
            user_id, note_data.get('content'), note_data.get('category', 'other')
        )

async def update_note(user_id: int, note_id: int, note_data: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        fields = []
        params = [note_id, user_id]
        if 'content' in note_data and note_data['content']:
            fields.append(f"content = ${len(params)+1}")
            params.append(note_data['content'])
        if 'category' in note_data:
            fields.append(f"category = ${len(params)+1}")
            params.append(note_data['category'])
        if not fields: return
        query = f"UPDATE notes SET {', '.join(fields)} WHERE id = $1 AND user_id = $2"
        await conn.execute(query, *params)

async def delete_note(user_id: int, note_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM notes WHERE id = $1 AND user_id = $2", note_id, user_id)

# GIFTS
async def save_gift(user_id: int, gift_data: dict):
    if not gift_data or not gift_data.get('title'): return
    pool = await get_db()
    async with pool.acquire() as conn:
        wish_id = gift_data.get('wish_id')
        if wish_id:
            await conn.execute("UPDATE wishes SET is_granted = TRUE WHERE id = $1 AND user_id = $2", wish_id, user_id)
        await conn.execute(
            "INSERT INTO gifts (user_id, title, is_without_reason, wish_id, given_at) VALUES ($1, $2, $3, $4, CURRENT_DATE)",
            user_id, gift_data.get('title'), gift_data.get('is_without_reason', False), wish_id
        )

async def get_gift_stats(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        last_without_reason = await conn.fetchrow(
            "SELECT * FROM gifts WHERE user_id = $1 AND is_without_reason = TRUE ORDER BY given_at DESC LIMIT 1",
            user_id
        )
        total_gifts = await conn.fetchval("SELECT COUNT(*) FROM gifts WHERE user_id = $1", user_id)
        stats = f"📊 <b>Статистика подарков:</b>\nВсего подарено: {total_gifts}\n\n"
        if last_without_reason:
            days_ago = (datetime.now().date() - last_without_reason['given_at']).days
            stats += f"🎁 <b>Последний подарок без повода:</b>\n\"{last_without_reason['title']}\"\n"
            stats += f"Дата: {last_without_reason['given_at'].strftime('%d.%m.%Y')} ({days_ago} дней назад)"
        else:
            stats += "🎁 Подарков без повода еще не было."
        return stats

# GET FORMATTED
async def get_user_context(user_id: int) -> dict:
    pool = await get_db()
    async with pool.acquire() as conn:
        wishes = await conn.fetch("SELECT * FROM wishes WHERE user_id = $1 AND is_granted = FALSE", user_id)
        dates = await conn.fetch("SELECT * FROM dates WHERE user_id = $1", user_id)
        notes = await conn.fetch("SELECT * FROM notes WHERE user_id = $1", user_id)
        return {'wishes': [dict(w) for w in wishes], 'dates': [dict(d) for d in dates], 'notes': [dict(n) for n in notes]}

async def get_wishes_formatted(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM wishes WHERE user_id = $1 AND is_granted = FALSE ORDER BY created_at DESC", user_id)
        if not rows: return "Список желаний пуст."
        return "\n".join([f"• [ID: {r['id']}] {r['title']} ({r['price_range'] or 'цена не указана'})" for r in rows])

async def get_notes_formatted(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM notes WHERE user_id = $1 ORDER BY created_at DESC", user_id)
        if not rows: return "Заметок нет."
        return "\n".join([f"• [ID: {r['id']}] {r['content']} [#{r['category'] or 'другое'}]" for r in rows])

async def get_dates_formatted(user_id: int) -> str:
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM dates WHERE user_id = $1 ORDER BY event_date ASC", user_id)
        if not rows: return "Важных дат нет."
        return "\n".join([f"• [ID: {r['id']}] {r['title']}: {r['event_date'].strftime('%d.%m.%Y')}" for r in rows])
