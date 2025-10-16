from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


def build_router() -> Router:
	router = Router(name="start")

	@router.message(CommandStart())
	async def handle_start(message: Message) -> None:
		await message.answer(
			"Привет! Я помогу подобрать образ с учётом погоды, настроения и вашего гардероба.\n"
			"Начнём с небольшой анкеты. Готовы?"
		)

	return router

