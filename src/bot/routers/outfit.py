from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.common import destination_kb, mood_kb, main_menu_kb
from src.bot.states import OutfitFlow
from src.config import load_config
from src.services.weather import WeatherService
from src.services.ai import OpenRouterClient


def build_router() -> Router:
	router = Router(name="outfit_today")

	@router.message(F.text == "Что сегодня надеть?")
	async def ask_city(message: Message, state: FSMContext) -> None:
		await state.set_state(OutfitFlow.city)
		await message.answer("Укажите город для прогноза погоды (например: Москва)")

	@router.message(OutfitFlow.city)
	async def ask_destination(message: Message, state: FSMContext) -> None:
		await state.update_data(city=message.text.strip())
		await state.set_state(OutfitFlow.destination)
		await message.answer("Куда вы направляетесь?", reply_markup=destination_kb())

	@router.message(OutfitFlow.destination)
	async def ask_mood(message: Message, state: FSMContext) -> None:
		await state.update_data(destination=message.text.strip())
		await state.set_state(OutfitFlow.mood)
		await message.answer("Что у вас сегодня с настроением?", reply_markup=mood_kb())

	@router.message(OutfitFlow.mood)
	async def make_recommendation(message: Message, state: FSMContext) -> None:
		await state.update_data(mood=message.text.strip())
		data = await state.get_data()
		config = load_config()

		weather_client = WeatherService(config.openweather_base_url, config.openweather_api_key)
		weather = await weather_client.get_current_by_city(data["city"]) if data.get("city") else None

		desc = f"Погода: {weather.temp_c:.0f}°C, {weather.description}" if weather else "Погода: недоступна"
		user_prompt = (
			"Вы выступаете как женский стилист и психолог. "
			"Дайте конкретную рекомендацию по образу с учётом цели (место), настроения и погоды. "
			f"Место: {data.get('destination')}. Настроение: {data.get('mood')}. {desc}. "
			"Используйте структуру: Верх, Низ, Обувь, Верхняя одежда (если нужно), Украшения, Макияж. "
			"Коротко и по делу (5-8 пунктов)."
		)
		client = OpenRouterClient(config.openrouter_base_url, config.openrouter_api_key, config.openrouter_model)
		ai_resp = await client.chat(
			system_prompt="Ты внимательный и тактичный женский стилист-консультант.",
			user_prompt=user_prompt,
		)
		text = ai_resp.text if ai_resp else "Не удалось получить рекомендацию от ИИ. Попробуйте позже."

		await message.answer(text, reply_markup=main_menu_kb())
		await state.set_state(OutfitFlow.result)

	return router

