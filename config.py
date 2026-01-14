import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD", "moder123")
DATABASE_NAME = "bot_database.db"

# Social links (placeholders, can be modified by user)
SOCIAL_LINKS = {
    "instagram": "https://www.instagram.com/avlodventures/",
    "telegram": "https://t.me/avlodventures",
    }
