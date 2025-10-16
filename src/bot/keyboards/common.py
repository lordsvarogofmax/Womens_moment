from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def yes_no_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
		resize_keyboard=True,
		one_time_keyboard=True,
	)


def main_menu_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[[KeyboardButton(text="Что сегодня надеть?")]],
		resize_keyboard=True,
	)


def mood_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="Спокойное"), KeyboardButton(text="Энергичное")],
			[KeyboardButton(text="Романтичное"), KeyboardButton(text="Деловое")],
		],
		resize_keyboard=True,
		one_time_keyboard=True,
	)


def destination_kb() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="Офис"), KeyboardButton(text="Учёба")],
			[KeyboardButton(text="Свидание"), KeyboardButton(text="Прогулка")],
			[KeyboardButton(text="Спорт"), KeyboardButton(text="Вечеринка")],
		],
		resize_keyboard=True,
		one_time_keyboard=True,
	)
