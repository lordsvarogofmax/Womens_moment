## Womens Moment Telegram Bot

Бот-консультант по гардеробу: рекомендации на основе погоды, психологического портрета, содержимого гардероба и настроения.

### Быстрый старт (локально)
1. Создайте бота у `@BotFather` и получите токен.
2. Создайте `.env` в корне и задайте переменные:
   - `TELEGRAM_BOT_TOKEN=...`
   - `DATABASE_URL=sqlite+aiosqlite:///./womens_moment.db`
   - `OPENWEATHER_API_KEY=...` (опционально)
   - `OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5`
   - `DEFAULT_LOCALE=ru`
   - `TIMEZONE=Europe/Moscow`
   - `OPENROUTER_API_KEY=...`
   - `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
   - `OPENROUTER_MODEL=openai/gpt-5`
3. Установите зависимости:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
4. Запуск (polling):
```bash
python -m src.main
```

### Деплой на Render (webhook)
1. Создайте Web Service на `render.com` и укажите репозиторий проекта.
2. В переменных окружения укажите:
   - `TELEGRAM_BOT_TOKEN`
   - `WEBHOOK_BASE_URL=https://happy-girls.onrender.com`
   - Другие переменные из блока выше (OpenWeather/OpenRouter и т.д.)
3. Команда запуска: `python -m src.webhook_app`
4. После запуска приложение автоматически установит webhook на `WEBHOOK_BASE_URL + /webhook/{TELEGRAM_BOT_TOKEN}`.

### Структура
- `src/main.py` — точка входа (polling)
- `src/webhook_app.py` — веб-сервер (webhook для Render)
- `src/config.py` — конфиг
- `src/bot/routers/` — роутеры и сценарии
- `src/services/weather.py` — погода
- `src/services/ai.py` — клиент OpenRouter
- `src/storage/` — хранилище/БД (будет добавлено)

### Примечание
- OpenRouter — единый интерфейс к LLM-моделям, OpenAI-совместимый API. См. `https://openrouter.ai/`.
- Проект использует aiogram 3, SQLAlchemy 2, httpx, aiohttp.
