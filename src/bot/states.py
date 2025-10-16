from aiogram.fsm.state import State, StatesGroup


class ProfileSurvey(StatesGroup):
	q_style = State()
	q_risk = State()
	q_colors = State()
	completed = State()


class WardrobeSurvey(StatesGroup):
	category = State()
	items = State()
	completed = State()


class OutfitFlow(StatesGroup):
	city = State()
	destination = State()
	mood = State()
	result = State()

