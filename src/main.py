import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import load_config
from src.bot.routers.start import build_router as build_start_router
from src.bot.routers.profile import build_router as build_profile_router
from src.bot.routers.outfit import build_router as build_outfit_router


async def main() -> None:
	logging.basicConfig(level=logging.INFO)
	config = load_config()

	if not config.bot_token:
		raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

	bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
	dp = Dispatcher(storage=MemoryStorage())

	# Routers
	dp.include_router(build_start_router())
	dp.include_router(build_profile_router())
	dp.include_router(build_outfit_router())

	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot)


if __name__ == "__main__":
	asyncio.run(main())
