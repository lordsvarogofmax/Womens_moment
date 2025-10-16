import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
	bot_token: str
	database_url: str
	openweather_api_key: str | None
	openweather_base_url: str
	default_locale: str
	timezone: str
	# Webhook/hosting
	webhook_base_url: str | None
	webhook_path: str
	# OpenRouter
	openrouter_api_key: str | None
	openrouter_base_url: str
	openrouter_model: str
	openrouter_referer: str | None
	openrouter_title: str
	# Logging
	log_level: str


def load_config() -> Config:
	load_dotenv()
	return Config(
		bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
		database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./womens_moment.db"),
		openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
		openweather_base_url=os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5"),
		default_locale=os.getenv("DEFAULT_LOCALE", "ru"),
		timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
		webhook_base_url=os.getenv("WEBHOOK_BASE_URL"),
		webhook_path=os.getenv("WEBHOOK_PATH", "/webhook"),
		openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
		openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
		openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-5"),
		openrouter_referer=os.getenv("OPENROUTER_REFERER"),
		openrouter_title=os.getenv("OPENROUTER_TITLE", "Womens Moment TG Bot"),
		log_level=os.getenv("LOG_LEVEL", "INFO"),
	)
