import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import load_config
from src.bot.routers.start import build_router as build_start_router
from src.bot.routers.profile import build_router as build_profile_router
from src.bot.routers.outfit import build_router as build_outfit_router


async def run() -> None:
	config = load_config()
	logging.basicConfig(
		level=getattr(logging, config.log_level.upper(), logging.INFO),
		format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
	)
	logging.info(
		"Starting polling bot | locale=%s tz=%s openrouter_enabled=%s weather_enabled=%s",
		config.default_locale,
		config.timezone,
		bool(config.openrouter_api_key),
		bool(config.openweather_api_key),
	)

	if not config.bot_token:
		raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

	bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
	dp = Dispatcher(storage=MemoryStorage())

	# Routers
	dp.include_router(build_start_router())
	dp.include_router(build_profile_router())
	dp.include_router(build_outfit_router())
	logging.info("Routers registered: start, profile, outfit")

	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot)


def main() -> None:
	try:
		asyncio.run(run())
	except Exception:
		logging.exception("Fatal error while running polling bot")
		raise


if __name__ == "__main__":
	main()
