import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://maria:maria@localhost:5432/maria_wish_bot")

if not BOT_TOKEN:
    # We will raise error only if we try to start the bot
    pass
