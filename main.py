import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import user_handlers, admin_handlers, moder_handlers

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        print("Error: BOT_TOKEN not set in .env")
        return

    # Initialize database
    init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register routers
    dp.include_router(admin_handlers.router)
    dp.include_router(moder_handlers.router)
    dp.include_router(user_handlers.router)

    # Start polling
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
 