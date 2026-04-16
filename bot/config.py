import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://maria:maria@postgres:5432/maria_wish_bot")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "basalex")

if not BOT_TOKEN:
    pass
