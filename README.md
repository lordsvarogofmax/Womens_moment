# Кулинарный Бот-Наставник 👨‍🍳

Telegram-бот, который отыгрывает роль сурового повара-бати из 90-х, помогающего готовить вкусные блюда. Матершинник, но с золотым сердцем! 😄

## Особенности

- **Аутентичная личность**: Суровый батя из 90-х с матом и характерными выражениями
- **Умное определение пола**: Определяет пол по имени, корректирует при поправке
- **Персонализация**: Обращается по имени и правильно (сынок/дочка)
- **Умный парсинг**: Понимает ингредиенты в свободной форме
- **Подбор рецептов**: Находит подходящие блюда по имеющимся продуктам
- **Пошаговые инструкции**: Детальные рецепты с матерными комментариями
- **Советы по покупкам**: Подсказывает, что нужно докупить

## База рецептов

- **Паста Карбонара** - классическая итальянская паста
- **Борщ** - традиционный русский суп
- **Плов** - восточное блюдо из риса и мяса
- **Салат Цезарь** - популярный салат с курицей
- **Оладьи** - русские блины

## Как работает

1. **Приветствие**: Бот спрашивает имя пользователя
2. **Определение пола**: Автоматически определяет пол по имени
3. **Сбор ингредиентов**: Пользователь пишет, что есть дома
4. **Подбор рецептов**: Бот находит подходящие блюда
5. **Выбор блюда**: Пользователь выбирает из предложенных вариантов
6. **Готовка**: Пошаговые инструкции с матерными комментариями

## Примеры диалогов

### Начало
```
Бот: Блять, кто это тут у меня? Назови свое имя, а то я не знаю, как к тебе обращаться! 😤
Пользователь: Аня
Бот: А, Аня! Ну что, дочка, готов(а) к кулинарным подвигам? Я тебе сейчас такое блюдо покажу, что ебать! 🔥
```

### Поправка пола
```
Пользователь: я мальчик
Бот: А, блять, Аня! Извини, дочка, я думал ты дочка, а ты сынок! Ну ладно, сынок, продолжаем! 😅
```

### Сбор ингредиентов
```
Бот: Слушай, Аня, сынок, расскажи мне честно - что у тебя в холодильнике лежит? И в шкафчиках тоже посмотри! Напиши все продукты, какие есть, через запятую или просто списком. Я из этого добра что-то вкусное состряпаю! Ебать, какая вкуснятина получится! 🥘
Пользователь: макароны, яйца, бекон, сыр, лук
```

### Подбор рецептов
```
Бот: Ебать, Аня, сынок! Из твоих продуктов я могу приготовить 1 блюд! Смотри, что у меня получилось:
- Паста Карбонара (нужно докупить: чеснок, соль, перец)
```

### Готовка
```
Бот: Отлично, Аня, сынок! Я для тебя выбрал рецепт 'Паста Карбонара'. Это классика, проверенная временем! Ебать, какая вкуснятина будет! 👨‍🍳

Шаг 1, Аня, сынок: Поставь большую кастрюлю с подсоленной водой на огонь
```

## Setup for Render.com (Docker)

### 1. Create Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Save the `BOT_TOKEN` you receive

### 2. Deploy to Render with Docker
1. Connect your GitHub repository to Render
2. Create a new "Web Service"
3. Choose **Docker** as the environment
4. Render will automatically detect the Dockerfile
5. No build/start commands needed - Docker handles everything

### 3. Set Environment Variables
In your Render dashboard, go to Environment and add:

```
BOT_TOKEN=your_bot_token_from_botfather
WEBHOOK_URL=https://your-app-name.onrender.com/webhook
```

Replace `your-app-name` with your actual Render app name.

### 4. Test the Bot
1. Find your bot on Telegram using the username you created
2. Send `/start` to begin
3. Follow the cooking flow!

## Local Development

### Option 1: Direct Python
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   ```bash
   export BOT_TOKEN="your_bot_token"
   export WEBHOOK_URL="https://your-ngrok-url.ngrok.io/webhook"
   ```
4. Run: `python main.py`

### Option 2: Docker (Recommended)
1. Clone the repository
2. Build Docker image:
   ```bash
   docker build -t cooking-bot .
   ```
3. Run container:
   ```bash
   docker run -p 10000:10000 \
     -e BOT_TOKEN="your_bot_token" \
     -e WEBHOOK_URL="https://your-ngrok-url.ngrok.io/webhook" \
     cooking-bot
   ```
4. Test: Visit `http://localhost:10000` - should show "Cooking Bot is running! 👨‍🍳"

## Bot Commands

- `/start` - Begin or restart the bot
- **Имя** - Tell your name (bot determines gender automatically)
- **я мальчик/девочка/мужчина/женщина** - Correct gender if bot was wrong
- **далее/дальше/готово/продолжаем** - Next cooking step
- **спасибо** - Thank the bot

## Personality Features

### Character Traits
- **Суровый батя**: Матершинник из 90-х с золотым сердцем
- **Опытный повар**: Знает множество рецептов
- **Заботливый отец**: Обращается по имени и правильно (сынок/дочка)
- **Умный**: Определяет пол по имени, корректирует при поправке
- **Поощряющий**: Подбадривает во время готовки

### Speech Patterns
- "Блять, кто это тут у меня?"
- "Слушай, [имя], [сынок/дочка]..."
- "Ебать, какая вкуснятина будет!"
- "Пальчики оближешь!"
- "Руки растут откуда надо!"
- "Классика, проверенная временем!"
- "Блять, какой ты молодец!"

## Database Schema

- `users` - User information (gender, username)
- `cooking_sessions` - Current cooking session state

## API Dependencies

- **Telegram Bot API**: For bot functionality
- **SQLite**: Local database for user data
- **Flask**: Web framework for webhook handling

## Free Tier Optimizations

- Minimal dependencies (Flask + requests only)
- Lightweight Docker image
- Efficient database queries
- No external AI services (rule-based recipe matching)

## Troubleshooting

### Bot not responding
- Check that `BOT_TOKEN` is set correctly
- Verify `WEBHOOK_URL` includes your full Render URL + `/webhook`
- Check Render logs for errors

### Recipe not found
- Make sure you have enough ingredients
- Try different ingredient names
- Check spelling

### Database issues
- Database is automatically created on first run
- Data persists between deployments on Render
- No manual setup required

## Support

If you encounter issues:
1. Check Render deployment logs
2. Verify environment variables are set
3. Test bot with `/start` command
4. Check that webhook URL is accessible

---

Приятного аппетита! 🍽️