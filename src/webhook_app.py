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
	try:
		if config.webhook_base_url:
			url = f"{config.webhook_base_url.rstrip('/')}{config.webhook_path}/{config.bot_token}"
			await bot.set_webhook(url, drop_pending_updates=True)
			logging.info("Webhook set to %s", url)
		else:
			logging.warning("WEBHOOK_BASE_URL is not set; webhook will not be configured")
	except Exception:
		logging.exception("Failed to set webhook")
		raise


async def on_shutdown(app: web.Application) -> None:
	bot: Bot = app["bot"]
	try:
		await bot.delete_webhook(drop_pending_updates=False)
		logging.info("Webhook deleted")
	except Exception:
		logging.exception("Failed to delete webhook")


def create_app() -> web.Application:
	config = load_config()
	logging.basicConfig(
		level=getattr(logging, config.log_level.upper(), logging.INFO),
		format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
	)
	logging.info(
		"Starting webhook app | base_url=%s path=%s openrouter_enabled=%s weather_enabled=%s",
		config.webhook_base_url,
		config.webhook_path,
		bool(config.openrouter_api_key),
		bool(config.openweather_api_key),
	)
	if not config.bot_token:
		raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment")

	bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
	dp = Dispatcher(storage=MemoryStorage())
	dp.include_router(build_start_router())
	dp.include_router(build_profile_router())
	dp.include_router(build_outfit_router())
	logging.info("Routers registered: start, profile, outfit")

	app = web.Application()
	app["config"] = config
	app["bot"] = bot

	handler = SimpleRequestHandler(dp, bot)
	handler.register(app, path=f"{config.webhook_path}/{config.bot_token}")
	setup_application(app, dp, bot=bot)

	# Healthcheck endpoint for Render
	async def healthcheck(_: web.Request) -> web.Response:
		return web.Response(text="ok")
	app.router.add_get("/healthz", healthcheck)

	app.on_startup.append(on_startup)
	app.on_shutdown.append(on_shutdown)
	return app


def main() -> None:
	app = create_app()
	port = int(os.getenv("PORT", "10000"))
	logging.info("Binding HTTP server on port %d", port)
	web.run_app(app, port=port)


if __name__ == "__main__":
	main()
