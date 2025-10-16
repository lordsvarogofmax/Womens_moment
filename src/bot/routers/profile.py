from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.bot.keyboards.common import yes_no_kb, main_menu_kb
from src.bot.states import ProfileSurvey


def build_router() -> Router:
	router = Router(name="profile_survey")

	@router.message(F.text.regexp("^(Привет|/start)$"))
	async def greet(message: Message, state: FSMContext) -> None:
		await state.clear()
		await message.answer(
			"Начнём с небольшой анкеты, чтобы понять ваш стиль. Готовы?",
			reply_markup=yes_no_kb(),
		)

	@router.message(F.text == "Да")
	async def q1(message: Message, state: FSMContext) -> None:
		await state.set_state(ProfileSurvey.q_style)
		await message.answer(
			"Какой стиль вам ближе? (минимализм, классика, романтика, спорт-шик и т.п.)"
		)

	@router.message(ProfileSurvey.q_style)
	async def q2(message: Message, state: FSMContext) -> None:
		await state.update_data(style=message.text.strip())
		await state.set_state(ProfileSurvey.q_risk)
		await message.answer("Насколько вы открыты к экспериментам? (низко/средне/высоко)")

	@router.message(ProfileSurvey.q_risk)
	async def q3(message: Message, state: FSMContext) -> None:
		await state.update_data(risk=message.text.strip())
		await state.set_state(ProfileSurvey.q_colors)
		await message.answer("Какие цвета любите носить чаще всего?")

	@router.message(ProfileSurvey.q_colors)
	async def finish(message: Message, state: FSMContext) -> None:
		await state.update_data(colors=message.text.strip())
		await state.set_state(ProfileSurvey.completed)
		await message.answer(
			"Спасибо! Профиль сохранён. Теперь можете запросить рекомендацию:",
			reply_markup=main_menu_kb(),
		)

	@router.message(F.text == "Нет")
	async def skip(message: Message, state: FSMContext) -> None:
		await state.clear()
		await message.answer(
			"Хорошо, можно вернуться к анкете позже.", reply_markup=main_menu_kb()
		)

	return router
