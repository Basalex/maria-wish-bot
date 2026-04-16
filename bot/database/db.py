import asyncpg
from bot.config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def get_db() -> asyncpg.Pool:
    return await get_pool()


async def init_db():
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                language TEXT NOT NULL DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT NOW(),
                last_active_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS wishes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                description TEXT,
                price_range TEXT,
                link TEXT,
                is_granted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dates (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                event_date DATE NOT NULL,
                reminder_days INTEGER DEFAULT 7,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                content TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                given_at DATE DEFAULT CURRENT_DATE,
                is_without_reason BOOLEAN DEFAULT FALSE,
                wish_id INTEGER REFERENCES wishes(id) ON DELETE SET NULL
            )
        """)

async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
