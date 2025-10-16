import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src.config import load_config
from src.bot.routers.start import build_router as build_start_router
from src.bot.routers.profile import build_router as build_profile_router
from src.bot.routers.outfit import build_router as build_outfit_router


async def on_startup(app: web.Application) -> None:
	config = app["config"]
	bot: Bot = app["bot"]
	if config.webhook_base_url:
		url = f"{config.webhook_base_url.rstrip('/')}{config.webhook_path}/{config.bot_token}"
		await bot.set_webhook(url, drop_pending_updates=True)
		logging.info("Webhook set to %s", url)


async def on_shutdown(app: web.Application) -> None:
	bot: Bot = app["bot"]
	await bot.delete_webhook(drop_pending_updates=False)


def create_app() -> web.Application:
	logging.basicConfig(level=logging.INFO)
	config = load_config()
	if not config.bot_token:
		raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

	bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
	dp = Dispatcher(storage=MemoryStorage())
	dp.include_router(build_start_router())
	dp.include_router(build_profile_router())
	dp.include_router(build_outfit_router())

	app = web.Application()
	app["config"] = config
	app["bot"] = bot

	handler = SimpleRequestHandler(dp, bot)
	handler.register(app, path=f"{config.webhook_path}/{config.bot_token}")
	setup_application(app, dp, bot=bot)

	app.on_startup.append(on_startup)
	app.on_shutdown.append(on_shutdown)
	return app


def main() -> None:
	app = create_app()
	port = int(os.getenv("PORT", "10000"))
	web.run_app(app, port=port)


if __name__ == "__main__":
	main()
