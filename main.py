import os
import sys
import logging
import json
import time
import hashlib
from datetime import datetime
import sqlite3
import requests
from flask import Flask, request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Better error handling for missing environment variables
def check_env_vars():
    missing_vars = []
    if not BOT_TOKEN:
        missing_vars.append("BOT_TOKEN")
    if not WEBHOOK_URL:
        missing_vars.append("WEBHOOK_URL")
    
    if missing_vars:
        logger.critical(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.critical("Please set the following environment variables in your Render dashboard:")
        logger.critical("1. BOT_TOKEN - Get from @BotFather on Telegram")
        logger.critical("2. WEBHOOK_URL - Your Render app URL + /webhook (e.g., https://your-app.onrender.com/webhook)")
        sys.exit(1)
    
    logger.info("✅ Environment variables loaded successfully")

check_env_vars()

app = Flask(__name__)

# Dedup caches
processed_messages = set()
processed_callback_ids = set()

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        # users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # psychological profiles
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                traits_json TEXT NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )
        # wardrobe
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                color TEXT,
                style TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # sessions
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT PRIMARY KEY,
                stage TEXT NOT NULL,
                data_json TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception:
        logger.exception("💥 Ошибка инициализации БД")


def upsert_user(user_id, username):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
            (str(user_id), username, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        logger.exception("💥 Ошибка записи пользователя")


def get_profile(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT traits_json FROM profiles WHERE user_id=?", (str(user_id),))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def save_profile(user_id, traits):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO profiles (user_id, traits_json, completed_at) VALUES (?, ?, ?)",
        (str(user_id), json.dumps(traits, ensure_ascii=False), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def add_wardrobe_items(user_id, category, items):
    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for item in items:
        cur.execute(
            "INSERT INTO wardrobe_items (user_id, category, item_name, color, style, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(user_id), category, item.get("name"), item.get("color"), item.get("style"), now)
        )
    conn.commit()
    conn.close()


def get_wardrobe(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT category, item_name, color, style FROM wardrobe_items WHERE user_id=?", (str(user_id),))
    rows = cur.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({"category": r[0], "name": r[1], "color": r[2], "style": r[3]})
    return items


def get_session(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT stage, data_json FROM sessions WHERE user_id=?", (str(user_id),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    stage, data_json = row
    return {"stage": stage, "data": json.loads(data_json) if data_json else {}}


def save_session(user_id, stage, data):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO sessions (user_id, stage, data_json, updated_at) VALUES (?, ?, ?, ?)",
        (str(user_id), stage, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


# --- UI helpers ---

def main_keyboard():
    return {
        "keyboard": [[
            {"text": "🧠 Пройти опрос профиля"},
            {"text": "👗 Заполнить гардероб"}
        ], [
            {"text": "🌤️ Что сегодня надеть?"}
        ]],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


WELCOME = (
    "Привет! Я помогу подобрать образ на сегодня исходя из погоды, настроения, гардероба и целей.\n\n"
    "Начните с заполнения профиля и гардероба или сразу нажмите ‘🌤️ Что сегодня надеть?’"
)


def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup
        requests.post(url, json=data, timeout=10)
    except Exception:
        logger.exception("Ошибка отправки сообщения")


def answer_callback_query(callback_query_id, text=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
        requests.post(url, data=data, timeout=10)
    except Exception:
        logger.exception("Ошибка answerCallbackQuery")


def get_message_hash(message):
    s = str(message.get('message_id', '')) + str(message.get('date', ''))
    return hashlib.md5(s.encode()).hexdigest()


def build_inline_keyboard(options_with_payload):
    # options_with_payload: [(text, payload), ...]
    row = [{"text": t, "callback_data": p} for t, p in options_with_payload]
    return {"inline_keyboard": [row]}


# --- Weather ---

def geocode_city(city_name):
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name, "count": 1, "language": "ru", "format": "json"},
            timeout=10,
        )
        if not resp.ok:
            return None
        data = resp.json()
        if not data.get("results"):
            return None
        r = data["results"][0]
        return {"lat": r["latitude"], "lon": r["longitude"], "name": r.get("name")}
    except Exception:
        logger.exception("Геокодинг ошибка")
        return None


def get_current_weather(lat, lon):
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,precipitation,wind_speed_10m",
                "forecast_days": 1,
                "timezone": "auto",
            },
            timeout=10,
        )
        if not resp.ok:
            return None
        data = resp.json()
        cur = data.get("current") or {}
        return {
            "temperature": cur.get("temperature_2m"),
            "precipitation": cur.get("precipitation"),
            "wind": cur.get("wind_speed_10m"),
        }
    except Exception:
        logger.exception("Ошибка погоды")
        return None


def pretty_weather(w):
    if not w:
        return "(нет данных)"
    return f"Температура: {w['temperature']}°C, Осадки: {w['precipitation']} мм, Ветер: {w['wind']} м/с"


# --- Conversations ---

PSYCH_QUESTIONS = [
    ("psych_q1", "Как вы обычно относитесь к ярким образам?", ["Люблю выделяться", "Предпочитаю сдержанность", "Ситуативно"]),
    ("psych_q2", "Что для вас важнее?", ["Комфорт", "Стиль", "Баланс"]),
    ("psych_q3", "Как описали бы свой характер?", ["Спокойная", "Энергичная", "Романтичная", "Дерзкая"]),
]

DESTINATION_OPTIONS = [
    ("Работа/Учёба", "dest_work"),
    ("Свидание", "dest_date"),
    ("Вечеринка", "dest_party"),
    ("Прогулка", "dest_walk"),
    ("Спорт", "dest_sport"),
    ("Домашние дела", "dest_home"),
]

MOOD_OPTIONS = [
    ("Спокойное", "mood_calm"),
    ("Энергичное", "mood_energetic"),
    ("Романтичное", "mood_romantic"),
    ("Дерзкое", "mood_bold"),
    ("Уютное", "mood_cozy"),
]

WARDROBE_CATEGORIES = [
    ("Базовые вещи", "base"),
    ("Верх", "top"),
    ("Низ", "bottom"),
    ("Обувь", "shoes"),
    ("Верхняя одежда", "outerwear"),
    ("Украшения", "accessories"),
]


def ask_psych_question(chat_id, idx, current):
    key, text, options = PSYCH_QUESTIONS[idx]
    keyboard = {"inline_keyboard": [[{"text": opt, "callback_data": f"psych|{key}|{opt}"} for opt in options]]}
    send_message(chat_id, f"{idx+1}/{len(PSYCH_QUESTIONS)}. {text}", reply_markup=keyboard)


def start_psych_flow(chat_id, user_id):
    save_session(user_id, "psych_q1", {"answers": {}})
    ask_psych_question(chat_id, 0, {})


def continue_psych_flow(chat_id, user_id, payload_key, payload_value):
    sess = get_session(user_id) or {"stage": "psych_q1", "data": {"answers": {}}}
    answers = sess["data"].get("answers", {})
    answers[payload_key] = payload_value
    idx = [k for k, *_ in PSYCH_QUESTIONS].index(payload_key)
    next_idx = idx + 1
    if next_idx < len(PSYCH_QUESTIONS):
        save_session(user_id, PSYCH_QUESTIONS[next_idx][0], {"answers": answers})
        ask_psych_question(chat_id, next_idx, answers)
    else:
        save_profile(user_id, answers)
        save_session(user_id, "idle", {})
        send_message(chat_id, "✅ Профиль сохранён!")
        send_message(chat_id, "Теперь заполним гардероб.", reply_markup=main_keyboard())


def parse_items_line(line):
    items = []
    for part in [p.strip() for p in line.split(";") if p.strip()]:
        items.append({"name": part, "color": None, "style": None})
    return items


def start_wardrobe_flow(chat_id, user_id):
    save_session(user_id, "wardrobe_cat_0", {"wardrobe": {}})
    send_message(chat_id, "Заполним гардероб. Перечислите через ‘;’ что у вас есть в категории ‘Базовые вещи’.\nНапример: белая футболка; чёрный свитшот; бежевый лонгслив")


def continue_wardrobe_flow(chat_id, user_id, text):
    sess = get_session(user_id)
    if not sess:
        start_wardrobe_flow(chat_id, user_id)
        return
    stage = sess["stage"]
    data = sess["data"]
    if not stage.startswith("wardrobe_cat_"):
        start_wardrobe_flow(chat_id, user_id)
        return
    idx = int(stage.split("_")[-1])
    ru_name, code = WARDROBE_CATEGORIES[idx]
    items = parse_items_line(text)
    if items:
        add_wardrobe_items(user_id, code, items)
    next_idx = idx + 1
    if next_idx < len(WARDROBE_CATEGORIES):
        save_session(user_id, f"wardrobe_cat_{next_idx}", data)
        next_ru, _ = WARDROBE_CATEGORIES[next_idx]
        send_message(chat_id, f"Категория: {next_ru}. Перечислите через ‘;’.")
    else:
        save_session(user_id, "idle", {})
        send_message(chat_id, "✅ Гардероб сохранён!", reply_markup=main_keyboard())


def start_style_today_flow(chat_id, user_id):
    save_session(user_id, "ask_city", {"flow": "style_today"})
    send_message(chat_id, "Введите ваш город для определения погоды (например: Москва)")


def outfit_recommendation(traits, wardrobe_items, weather, destination_code, mood_code):
    temperature = (weather or {}).get("temperature")
    precip = (weather or {}).get("precipitation") or 0
    wind = (weather or {}).get("wind") or 0

    def pick(category):
        for it in wardrobe_items:
            if it["category"] == category:
                return it["name"]
        return None

    look = []
    if temperature is not None:
        if temperature <= 0:
            look.append(pick("base") or "тёплый свитер")
            look.append(pick("bottom") or "плотные брюки/джинсы")
            look.append(pick("outerwear") or "пальто/пуховик")
            look.append(pick("shoes") or "тёплая обувь")
        elif temperature <= 12:
            look.append(pick("base") or "лонгслив/свитшот")
            look.append(pick("bottom") or "брюки/джинсы")
            look.append(pick("outerwear") or "лёгкое пальто/тренч")
            look.append(pick("shoes") or "закрытая обувь")
        elif temperature <= 20:
            look.append(pick("base") or "футболка/блуза")
            look.append(pick("bottom") or "брюки/джинсы/юбка")
            look.append(pick("shoes") or "кеды/туфли")
        else:
            look.append(pick("top") or "лёгкий топ")
            look.append(pick("bottom") or "юбка/шорты/лёгкие брюки")
            look.append(pick("shoes") or "сандалии/кеды")

    if precip and precip > 0:
        look.append("зонт/непромокаемая куртка")
    if wind and wind > 8:
        look.append("ветровка/защита от ветра")

    if destination_code in ("dest_work",):
        look.append("аккуратный деловой акцент")
    elif destination_code in ("dest_date",):
        look.append("романтичная деталь образа")
    elif destination_code in ("dest_party",):
        look.append("яркий акцент/украшения")
    elif destination_code in ("dest_sport",):
        look.append("удобная спортивная посадка")

    mood_map = {
        "mood_calm": "сдержанные оттенки",
        "mood_energetic": "контраст/динамика",
        "mood_romantic": "мягкие линии/пастель",
        "mood_bold": "смелый акцент",
        "mood_cozy": "уютные фактуры",
    }
    if mood_map.get(mood_code):
        look.append(mood_map[mood_code])

    if traits:
        archetype = traits.get("psych_q3")
        if archetype == "Энергичная":
            look.append("добавьте яркий цвет")
        elif archetype == "Романтичная":
            look.append("нежные аксессуары")
        elif archetype == "Дерзкая":
            look.append("смелая деталь (кожа/металл)")

    acc = None
    for it in wardrobe_items:
        if it["category"] == "accessories":
            acc = it["name"]
            break
    if acc:
        look.append(acc)

    items_text = ", ".join([p for p in look if p])
    return f"Рекомендация: {items_text}."


# --- Health check ---
@app.route("/", methods=["GET"])
def health_check():
    return "Wardrobe Bot is running! 🌸", 200

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "bot": "wardrobe-consultant"}, 200

# --- Webhook ---
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        if not data:
            return "OK", 200

        if "callback_query" in data:
            cb = data["callback_query"]
            callback_id = cb.get("id")
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            action = cb.get("data")
            user = cb.get("from", {})
            user_id = user.get("id")

            if callback_id and callback_id in processed_callback_ids:
                return "OK", 200
            if callback_id:
                processed_callback_ids.add(callback_id)
                answer_callback_query(callback_id)

            if action and action.startswith("psych|"):
                _, key, value = action.split("|", 2)
                continue_psych_flow(chat_id, user_id, key, value)
                return "OK", 200

            if action and (action.startswith("dest_") or action.startswith("mood_")):
                sess = get_session(user_id)
                if not sess:
                    save_session(user_id, "ask_city", {"flow": "style_today"})
                    send_message(chat_id, "Введите город")
                    return "OK", 200
                data_s = sess.get("data", {})
                if action.startswith("dest_"):
                    data_s["destination"] = action
                    save_session(user_id, "ask_mood", data_s)
                    send_message(chat_id, "Какое у вас настроение?", reply_markup=build_inline_keyboard(MOOD_OPTIONS))
                    return "OK", 200
                if action.startswith("mood_"):
                    data_s["mood"] = action
                    traits = get_profile(user_id) or {}
                    wardrobe = get_wardrobe(user_id)
                    weather = data_s.get("weather")
                    rec = outfit_recommendation(traits, wardrobe, weather, data_s.get("destination"), data_s.get("mood"))
                    save_session(user_id, "idle", {})
                    send_message(chat_id, f"Погода: {pretty_weather(weather)}\n\n{rec}")
                    return "OK", 200

            send_message(chat_id, "Неизвестное действие")
            return "OK", 200

        if "message" not in data:
            return "OK", 200
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user = msg.get("from", {})
        user_id = user.get("id")

        msg_hash = get_message_hash(msg)
        if msg_hash in processed_messages:
            return "OK", 200
        processed_messages.add(msg_hash)

        upsert_user(user_id, user.get("username"))

        if "text" in msg:
            text = msg["text"].strip()
            if text == "/start":
                send_message(chat_id, WELCOME, reply_markup=main_keyboard())
                profile = get_profile(user_id)
                if not profile:
                    start_psych_flow(chat_id, user_id)
                return "OK", 200

            if text == "🧠 Пройти опрос профиля":
                start_psych_flow(chat_id, user_id)
                return "OK", 200

            if text == "👗 Заполнить гардероб":
                start_wardrobe_flow(chat_id, user_id)
                return "OK", 200

            if text == "🌤️ Что сегодня надеть?":
                start_style_today_flow(chat_id, user_id)
                return "OK", 200

            sess = get_session(user_id)
            if sess:
                if sess["stage"].startswith("wardrobe_cat_"):
                    continue_wardrobe_flow(chat_id, user_id, text)
                    return "OK", 200
                if sess["stage"] == "ask_city":
                    place = geocode_city(text)
                    if not place:
                        send_message(chat_id, "Не нашла город. Повторите, например: Санкт-Петербург")
                        return "OK", 200
                    w = get_current_weather(place["lat"], place["lon"])
                    data_s = sess.get("data", {})
                    data_s.update({"city": place["name"], "lat": place["lat"], "lon": place["lon"], "weather": w})
                    save_session(user_id, "ask_dest", data_s)
                    send_message(chat_id, f"Погода в {place['name']}: {pretty_weather(w)}")
                    send_message(chat_id, "Куда вы направляетесь?", reply_markup=build_inline_keyboard(DESTINATION_OPTIONS))
                    return "OK", 200

        return "OK", 200
    except Exception:
        logger.exception("Критическая ошибка webhook")
        return "OK", 200


def set_webhook():
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        webhook_url = WEBHOOK_URL.rstrip("/") + "/webhook"
        resp = requests.post(url, json={"url": webhook_url}, timeout=10)
        if resp.ok:
            logger.info(f"✅ Webhook установлен: {webhook_url}")
        else:
            logger.error(f"❌ Ошибка webhook: {resp.status_code} - {resp.text}")
    except Exception:
        logger.exception("Ошибка установки webhook")


if __name__ == "__main__":
    logger.info("🚀 Запуск гардероб-бота...")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        sys.exit(1)
    
    # Set webhook
    try:
        set_webhook()
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        # Don't exit, continue without webhook for testing
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 Запуск сервера на порту {port}")
    
    # Run Flask app
    app.run(
        host="0.0.0.0",  # Important for Docker
        port=port,
        debug=False,  # Disable debug in production
        threaded=True  # Enable threading for better performance
    )