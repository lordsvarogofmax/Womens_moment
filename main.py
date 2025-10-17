import os
import sys
import logging
import json
import time
import hashlib
import re
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

# --- Database helpers ---
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
                gender TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # cooking sessions
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cooking_sessions (
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

def upsert_user(user_id, username, gender=None):
    try:
        conn = get_db()
        cur = conn.cursor()
        if gender:
            cur.execute(
                "INSERT OR REPLACE INTO users (user_id, username, gender, created_at) VALUES (?, ?, ?, ?)",
                (str(user_id), username, gender, datetime.utcnow().isoformat())
            )
        else:
            cur.execute(
                "INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
                (str(user_id), username, datetime.utcnow().isoformat())
            )
        conn.commit()
        conn.close()
    except Exception:
        logger.exception("💥 Ошибка записи пользователя")

def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, gender FROM users WHERE user_id=?", (str(user_id),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_session(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT stage, data_json FROM cooking_sessions WHERE user_id=?", (str(user_id),))
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
        "REPLACE INTO cooking_sessions (user_id, stage, data_json, updated_at) VALUES (?, ?, ?, ?)",
        (str(user_id), stage, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

# --- UI helpers ---
def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        logger.info(f"📤 Отправляем сообщение в чат {chat_id}: {text[:50]}...")
        response = requests.post(url, json=data, timeout=10)
        
        if not response.ok:
            logger.error(f"❌ Ошибка отправки сообщения: {response.status_code} - {response.text}")
        else:
            logger.info(f"✅ Сообщение отправлено успешно")
    except Exception as e:
        logger.exception(f"💥 Ошибка отправки сообщения: {e}")

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

# --- Bati personality ---
def get_gender_pronoun(gender):
    if gender == "male":
        return {"you": "сынок", "your": "твой", "you_have": "у тебя", "you_are": "ты", "address": "сынок"}
    elif gender == "female":
        return {"you": "дочка", "your": "твоя", "you_have": "у тебя", "you_are": "ты", "address": "дочка"}
    else:
        return {"you": "детка", "your": "твой", "you_have": "у тебя", "you_are": "ты", "address": "детка"}

def detect_gender_by_name(name):
    """Определяет пол по имени (простая эвристика)"""
    name = name.lower().strip()
    
    # Мужские имена
    male_names = [
        'александр', 'алексей', 'андрей', 'антон', 'артем', 'борис', 'вадим', 'валентин', 'валерий', 'василий',
        'виктор', 'владимир', 'владислав', 'владилен', 'геннадий', 'георгий', 'григорий', 'дмитрий', 'евгений',
        'егор', 'иван', 'игорь', 'кирилл', 'константин', 'максим', 'михаил', 'николай', 'олег', 'павел',
        'петр', 'роман', 'сергей', 'станислав', 'степан', 'федор', 'юрий', 'ярослав', 'денис', 'илья',
        'артур', 'эдуард', 'леонид', 'мирон', 'марк', 'тимофей', 'матвей', 'даниил', 'захар', 'семен',
        'саша', 'леша', 'андрюха', 'дима', 'миша', 'коля', 'паша', 'рома', 'серый', 'ваня', 'игорь',
        'жора', 'гоша', 'вася', 'петя', 'федя', 'юра', 'леша', 'леха', 'саня', 'санёк'
    ]
    
    # Женские имена
    female_names = [
        'александра', 'алена', 'анастасия', 'анна', 'валентина', 'валерия', 'вера', 'галина', 'дарья', 'елена',
        'екатерина', 'елена', 'жанна', 'зоя', 'ирина', 'кристина', 'лариса', 'людмила', 'мария', 'надежда',
        'наталья', 'оксана', 'ольга', 'полина', 'светлана', 'софья', 'татьяна', 'юлия', 'яна', 'виктория',
        'екатерина', 'марина', 'наташа', 'катя', 'лена', 'оля', 'таня', 'света', 'ира', 'галя', 'валя',
        'люда', 'надя', 'зоя', 'вера', 'жанна', 'кристина', 'даша', 'полина', 'софья', 'яна', 'вика',
        'маша', 'настя', 'катя', 'катюша', 'ленка', 'оленька', 'танечка', 'светка', 'ирочка', 'галочка'
    ]
    
    if name in male_names:
        return "male"
    elif name in female_names:
        return "female"
    else:
        return "unknown"

def detect_gender_correction(text):
    """Определяет поправку пола из текста"""
    text = text.lower()
    
    male_corrections = ['мальчик', 'мужчина', 'юноша', 'пацан', 'сын', 'сынок', 'я мальчик', 'я мужчина', 'я парень']
    female_corrections = ['девочка', 'девушка', 'женщина', 'девчонка', 'дочь', 'дочка', 'я девочка', 'я девушка', 'я женщина']
    
    for correction in male_corrections:
        if correction in text:
            return "male"
    
    for correction in female_corrections:
        if correction in text:
            return "female"
    
    return None

def bati_name_ask():
    """Батю спрашивает имя"""
    greetings = [
        "Блять, кто это тут у меня? Назови свое имя, а то я не знаю, как к тебе обращаться! 😤",
        "Слушай, детка, как тебя зовут? Я должен знать, с кем имею дело на кухне! 👨‍🍳",
        "Ну что, незнакомец, представься! Как тебя родители назвали? 🤔",
        "Блять, да кто ты такой? Имя скажи, а то я не буду с анонимом готовить! 😠"
    ]
    return greetings[0]

def bati_greeting(name, gender):
    pronouns = get_gender_pronoun(gender)
    greetings = [
        f"А, {name}! Ну что, {pronouns['address']}, готов(а) к кулинарным подвигам? Я тебе сейчас такое блюдо покажу, что ебать! 🔥",
        f"Так, {name}, {pronouns['address']} мой! Сегодня будем готовить по-настоящему, как в ресторане! 👨‍🍳",
        f"Слушай, {name}, {pronouns['address']}, я тебе сейчас такое блюдо покажу, что пальчики оближешь! Ебать, какая вкуснятина будет! 😋",
        f"Ну что, {name}, {pronouns['address']}, добро пожаловать в мою кухню! Сегодня будем творить кулинарные шедевры! 🍳"
    ]
    return greetings[0]

def bati_gender_correction(name, old_gender, new_gender):
    """Батю корректирует пол"""
    old_pronouns = get_gender_pronoun(old_gender)
    new_pronouns = get_gender_pronoun(new_gender)
    
    corrections = [
        f"А, блять, {name}! Извини, {old_pronouns['address']}, я думал ты {old_pronouns['address']}, а ты {new_pronouns['address']}! Ну ладно, {new_pronouns['address']}, продолжаем! 😅",
        f"Ебать, {name}, я ошибся! Ты же {new_pronouns['address']}, а не {old_pronouns['address']}! Ну ладно, {new_pronouns['address']}, давай готовить! 🤦‍♂️",
        f"Слушай, {name}, я перепутал! Ты {new_pronouns['address']}, а я тебя {old_pronouns['address']} называл! Извини, {new_pronouns['address']}! 😅",
        f"Блять, {name}, я облажался! Ты {new_pronouns['address']}, а не {old_pronouns['address']}! Ну ладно, {new_pronouns['address']}, поехали дальше! 🤷‍♂️"
    ]
    return corrections[0]

def bati_ingredients_ask(name, gender):
    pronouns = get_gender_pronoun(gender)
    return f"Слушай, {name}, {pronouns['address']}, расскажи мне честно - что у тебя в холодильнике лежит? И в шкафчиках тоже посмотри! Напиши все продукты, какие есть, через запятую или просто списком. Я из этого добра что-то вкусное состряпаю! Ебать, какая вкуснятина получится! 🥘"

def bati_recipe_intro(name, gender, recipe_name):
    pronouns = get_gender_pronoun(gender)
    intros = [
        f"Отлично, {name}, {pronouns['address']}! Я для тебя выбрал рецепт '{recipe_name}'. Это классика, проверенная временем! Ебать, какая вкуснятина будет! 👨‍🍳",
        f"Слушай, {name}, {pronouns['address']}, '{recipe_name}' - это то, что нужно! Я сам так готовил еще в молодости! Блять, как же это вкусно! 🔥",
        f"Ну что, {name}, {pronouns['address']}, готовим '{recipe_name}'? Это блюдо никогда не подводило! Ебать, пальчики оближешь! 😋"
    ]
    return intros[0]

def bati_cooking_step(step_num, instruction, name, gender):
    pronouns = get_gender_pronoun(gender)
    step_intros = [
        f"Шаг {step_num}, {name}, {pronouns['address']}:",
        f"Слушай внимательно, {name}, {pronouns['address']}, шаг {step_num}:",
        f"Теперь, {name}, {pronouns['address']}, делаем так - шаг {step_num}:",
        f"Запоминай, {name}, {pronouns['address']}, шаг {step_num}:"
    ]
    return f"{step_intros[0]} {instruction}"

def bati_encouragement(name, gender):
    pronouns = get_gender_pronoun(gender)
    encouragements = [
        f"Молодец, {name}, {pronouns['address']}! У тебя получается! Ебать, какие у тебя руки золотые! 👍",
        f"Так держать, {name}, {pronouns['address']}! Ты настоящий повар! Блять, как же ты быстро учишься! 👨‍🍳",
        f"Отлично, {name}, {pronouns['address']}! Вижу, что руки растут откуда надо! Ебать, какой ты молодец! 🔥",
        f"Красота, {name}, {pronouns['address']}! Учишься быстро! Блять, ты просто повар от бога! 😋"
    ]
    return encouragements[0]

def bati_no_ingredients(name, gender):
    pronouns = get_gender_pronoun(gender)
    return f"Блять, {name}, {pronouns['address']}, с такими продуктами особо не разгуляешься... Может, сходишь в магазин за мясом или овощами? Или закажешь доставку? А то из воздуха еду не сделаешь! 🛒"

def bati_recipe_found(name, gender, count):
    pronouns = get_gender_pronoun(gender)
    return f"Ебать, {name}, {pronouns['address']}! Из твоих продуктов я могу приготовить {count} блюд! Смотри, что у меня получилось:"

# --- Recipe database ---
RECIPES = {
    "паста_карбонара": {
        "name": "Паста Карбонара",
        "ingredients": ["макароны", "бекон", "яйца", "сыр_пармезан", "чеснок", "соль", "перец"],
        "optional": ["лук"],
        "instructions": [
            "Поставь большую кастрюлю с подсоленной водой на огонь",
            "Пока вода закипает, нарежь бекон мелкими кубиками",
            "Натри сыр на мелкой терке",
            "Взбей яйца с сыром, добавь соль и перец",
            "Обжарь бекон на сковороде до хрустящего состояния",
            "Добавь измельченный чеснок к бекону",
            "Отвари макароны до состояния аль денте",
            "Слей воду, оставив немного для соуса",
            "Смешай горячие макароны с беконом",
            "Сними с огня и добавь яично-сырную смесь, быстро перемешивая",
            "Подавай сразу, посыпав пармезаном"
        ]
    },
    "борщ": {
        "name": "Борщ",
        "ingredients": ["говядина", "свекла", "капуста", "морковь", "лук", "картофель", "томаты", "чеснок", "соль", "перец", "лавровый_лист"],
        "optional": ["укроп", "сметана"],
        "instructions": [
            "Свари мясной бульон из говядины",
            "Натри свеклу на крупной терке",
            "Нарежь капусту соломкой",
            "Нарежь картофель кубиками",
            "Нарежь лук и морковь",
            "Обжарь лук и морковь на растительном масле",
            "Добавь к ним свеклу и томаты, туши 10 минут",
            "Добавь овощи в кипящий бульон",
            "Вари 20 минут, добавь картофель",
            "Вари еще 15 минут, добавь капусту",
            "Добавь соль, перец, лавровый лист",
            "Вари еще 10 минут, добавь чеснок",
            "Подавай со сметаной и укропом"
        ]
    },
    "плов": {
        "name": "Плов",
        "ingredients": ["рис", "мясо", "морковь", "лук", "чеснок", "соль", "перец", "куркума", "растительное_масло"],
        "optional": ["барбарис", "зира"],
        "instructions": [
            "Промой рис до чистой воды",
            "Нарежь мясо кубиками",
            "Нарежь лук полукольцами, морковь соломкой",
            "Разогрей масло в казане или толстостенной кастрюле",
            "Обжарь мясо до золотистой корочки",
            "Добавь лук, обжарь до прозрачности",
            "Добавь морковь, обжарь 5 минут",
            "Добавь специи и соль",
            "Добавь рис, разровняй",
            "Залей горячей водой на 2 см выше риса",
            "Добавь целые зубчики чеснока",
            "Вари на сильном огне до выпаривания воды",
            "Уменьши огонь, накрой крышкой, томи 20 минут",
            "Перемешай и подавай"
        ]
    },
    "салат_цезарь": {
        "name": "Салат Цезарь",
        "ingredients": ["салат", "курица", "сыр_пармезан", "хлеб", "чеснок", "майонез", "горчица", "соль", "перец"],
        "optional": ["анчоусы", "каперсы"],
        "instructions": [
            "Нарежь хлеб кубиками и обжарь с чесноком",
            "Отвари курицу и нарежь кубиками",
            "Порви салат руками",
            "Смешай майонез с горчицей и чесноком",
            "Добавь соль и перец в соус",
            "Смешай салат с курицей",
            "Заправь соусом",
            "Посыпь пармезаном и сухариками",
            "Подавай сразу"
        ]
    },
    "оладьи": {
        "name": "Оладьи",
        "ingredients": ["мука", "молоко", "яйца", "сахар", "соль", "дрожжи", "растительное_масло"],
        "optional": ["ванилин"],
        "instructions": [
            "Подогрей молоко до теплого состояния",
            "Раствори дрожжи в молоке с сахаром",
            "Добавь яйца и соль",
            "Постепенно добавь муку, размешивая",
            "Замеси тесто до консистенции сметаны",
            "Накрой полотенцем, дай подойти 30 минут",
            "Разогрей масло на сковороде",
            "Выкладывай тесто ложкой",
            "Жарь с двух сторон до золотистого цвета",
            "Подавай со сметаной или вареньем"
        ]
    }
}

def parse_ingredients(text):
    """Парсит ингредиенты из свободного текста"""
    try:
        # Нормализуем текст
        text = text.lower().strip()
        
        # Убираем лишние символы
        text = re.sub(r'[^\w\s,;]', ' ', text)
        
        # Разбиваем по разделителям
        items = []
        for separator in [',', ';', '\n']:
            if separator in text:
                items = [item.strip() for item in text.split(separator) if item.strip()]
                break
        
        if not items:
            items = text.split()
        
        # Нормализуем названия
        normalized = []
        for item in items:
            item = item.strip()
            if len(item) > 2:  # Игнорируем слишком короткие слова
                # Простая нормализация
                item = item.replace(' ', '_')
                normalized.append(item)
        
        logger.info(f"🔍 Парсинг ингредиентов: '{text}' -> {normalized}")
        return normalized
    except Exception as e:
        logger.exception(f"💥 Ошибка парсинга ингредиентов: {e}")
        return []

def find_matching_recipes(ingredients):
    """Находит рецепты по имеющимся ингредиентам"""
    matches = []
    
    for recipe_id, recipe in RECIPES.items():
        required = set(recipe['ingredients'])
        optional = set(recipe.get('optional', []))
        available = set(ingredients)
        
        # Проверяем, сколько обязательных ингредиентов есть
        missing_required = required - available
        has_required = len(required - missing_required)
        required_ratio = has_required / len(required)
        
        # Если есть хотя бы 70% обязательных ингредиентов
        if required_ratio >= 0.7:
            missing_optional = optional - available
            matches.append({
                'id': recipe_id,
                'name': recipe['name'],
                'missing_required': list(missing_required),
                'missing_optional': list(missing_optional),
                'score': required_ratio
            })
    
    # Сортируем по количеству имеющихся ингредиентов
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def get_recipe_instructions(recipe_id, name, gender):
    """Возвращает пошаговые инструкции для рецепта"""
    if recipe_id not in RECIPES:
        return []
    
    recipe = RECIPES[recipe_id]
    instructions = []
    
    for i, step in enumerate(recipe['instructions'], 1):
        instructions.append(bati_cooking_step(i, step, name, gender))
    
    return instructions

# --- Conversation flows ---
def start_cooking_flow(chat_id, user_id, name, gender):
    """Начинает кулинарный диалог"""
    save_session(user_id, "ask_ingredients", {"name": name, "gender": gender})
    greeting = bati_greeting(name, gender)
    ingredients_ask = bati_ingredients_ask(name, gender)
    
    send_message(chat_id, greeting)
    send_message(chat_id, ingredients_ask)

def handle_ingredients(chat_id, user_id, text, name, gender):
    """Обрабатывает список ингредиентов"""
    try:
        logger.info(f"🔍 Обрабатываем ингредиенты от {name}: {text}")
        ingredients = parse_ingredients(text)
        logger.info(f"📋 Распознанные ингредиенты: {ingredients}")
        
        if not ingredients:
            pronouns = get_gender_pronoun(gender)
            send_message(chat_id, f"Слушай, {name}, {pronouns['address']}, я ничего не понял! Напиши нормально, что у тебя есть из продуктов! Блять, как же я тебя пойму? 😅")
            return
        
        # Сохраняем ингредиенты
        save_session(user_id, "show_recipes", {"ingredients": ingredients, "name": name, "gender": gender})
        
        # Ищем подходящие рецепты
        matches = find_matching_recipes(ingredients)
        logger.info(f"🍳 Найдено рецептов: {len(matches)}")
        
        if not matches:
            send_message(chat_id, bati_no_ingredients(name, gender))
            return
        
        # Показываем рецепты
        send_message(chat_id, bati_recipe_found(name, gender, len(matches)))
        
        recipe_options = []
        for i, match in enumerate(matches[:5]):  # Показываем максимум 5 рецептов
            missing_text = ""
            if match['missing_required']:
                missing_text = f" (нужно докупить: {', '.join(match['missing_required'])})"
            recipe_options.append((f"{match['name']}{missing_text}", f"recipe_{match['id']}"))
        
        keyboard = build_inline_keyboard(recipe_options)
        send_message(chat_id, "Выбирай, что будем готовить:", reply_markup=keyboard)
    except Exception as e:
        logger.exception(f"💥 Ошибка обработки ингредиентов: {e}")
        send_message(chat_id, "Блять, что-то пошло не так! Попробуй еще раз!")

def handle_recipe_selection(chat_id, user_id, recipe_id, name, gender):
    """Обрабатывает выбор рецепта"""
    if recipe_id not in RECIPES:
        send_message(chat_id, "Блять, что-то пошло не так... Попробуй еще раз!")
        return
    
    recipe = RECIPES[recipe_id]
    save_session(user_id, "cooking", {"recipe_id": recipe_id, "name": name, "gender": gender, "step": 0})
    
    intro = bati_recipe_intro(name, gender, recipe['name'])
    send_message(chat_id, intro)
    
    # Показываем ингредиенты
    ingredients_text = f"Ингредиенты:\n• {', '.join(recipe['ingredients'])}"
    if recipe.get('optional'):
        ingredients_text += f"\n• Дополнительно: {', '.join(recipe['optional'])}"
    
    send_message(chat_id, ingredients_text)
    
    # Начинаем готовку
    instructions = get_recipe_instructions(recipe_id, name, gender)
    if instructions:
        send_message(chat_id, "Ну что, начинаем готовить! Ебать, какая вкуснятина будет! 🔥")
        send_message(chat_id, instructions[0])

def handle_cooking_step(chat_id, user_id, name, gender):
    """Обрабатывает следующий шаг готовки"""
    session = get_session(user_id)
    if not session or session['stage'] != 'cooking':
        return
    
    recipe_id = session['data']['recipe_id']
    current_step = session['data'].get('step', 0)
    
    instructions = get_recipe_instructions(recipe_id, name, gender)
    
    if current_step + 1 < len(instructions):
        next_step = current_step + 1
        save_session(user_id, "cooking", {**session['data'], "step": next_step})
        
        send_message(chat_id, instructions[next_step])
        
        if next_step == len(instructions) - 1:
            # Последний шаг
            pronouns = get_gender_pronoun(gender)
            send_message(chat_id, f"Готово, {name}, {pronouns['address']}! Ебать, какая вкуснятина получилась! Приятного аппетита! 🍽️")
            send_message(chat_id, "Хочешь приготовить что-то еще? Напиши /start")
    else:
        # Готовка завершена
        pronouns = get_gender_pronoun(gender)
        send_message(chat_id, f"Отлично, {name}, {pronouns['address']}! Блюдо готово! Ебать, как же это вкусно! Приятного аппетита! 🍽️")
        send_message(chat_id, "Хочешь приготовить что-то еще? Напиши /start")

# --- Health check ---
@app.route("/", methods=["GET"])
def health_check():
    return "Cooking Bot is running! 👨‍🍳", 200

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "bot": "cooking-mentor"}, 200

# --- Webhook ---
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        logger.info(f"📨 Получен webhook: {data}")
        if not data:
            logger.info("❌ Пустой webhook")
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

            if action and action.startswith("recipe_"):
                recipe_id = action.replace("recipe_", "")
                session = get_session(user_id)
                if session:
                    name = session['data'].get('name', 'детка')
                    gender = session['data'].get('gender', 'unknown')
                    handle_recipe_selection(chat_id, user_id, recipe_id, name, gender)
                return "OK", 200

            if action == "next_step":
                session = get_session(user_id)
                if session:
                    name = session['data'].get('name', 'детка')
                    gender = session['data'].get('gender', 'unknown')
                    handle_cooking_step(chat_id, user_id, name, gender)
                return "OK", 200

            send_message(chat_id, "Что-то пошло не так... Попробуй еще раз!")
            return "OK", 200

        if "message" not in data:
            logger.info("❌ Нет сообщения в данных")
            return "OK", 200
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user = msg.get("from", {})
        user_id = user.get("id")
        
        logger.info(f"📝 Обрабатываем сообщение от пользователя {user_id} в чате {chat_id}")

        # Dedup
        msg_hash = get_message_hash(msg)
        if msg_hash in processed_messages:
            logger.info(f"🔄 Пропускаем дублирующееся сообщение")
            return "OK", 200
        processed_messages.add(msg_hash)

        upsert_user(user_id, user.get("username"))

        if "text" in msg:
            text = msg["text"].strip()
            logger.info(f"📝 Текстовое сообщение: '{text}'")
            
            if text == "/start":
                logger.info("🚀 Обработка команды /start")
                # Сбрасываем сессию
                save_session(user_id, "ask_name", {})
                send_message(chat_id, bati_name_ask())
                return "OK", 200

            # Обработка имени
            session = get_session(user_id)
            if session and session['stage'] == 'ask_name':
                name = text.strip()
                if len(name) < 2:
                    send_message(chat_id, "Блять, да нормальное имя скажи! Не меньше двух букв! 😤")
                    return "OK", 200
                
                # Определяем пол по имени
                gender = detect_gender_by_name(name)
                if gender == "unknown":
                    gender = "male"  # По умолчанию
                
                # Сохраняем пользователя
                upsert_user(user_id, user.get("username"), gender)
                save_session(user_id, "ask_ingredients", {"name": name, "gender": gender})
                
                # Приветствуем
                greeting = bati_greeting(name, gender)
                ingredients_ask = bati_ingredients_ask(name, gender)
                
                send_message(chat_id, greeting)
                send_message(chat_id, ingredients_ask)
                return "OK", 200

            # Проверка на поправку пола
            gender_correction = detect_gender_correction(text)
            if gender_correction:
                session = get_session(user_id)
                if session and session['data'].get('name'):
                    name = session['data']['name']
                    old_gender = session['data'].get('gender', 'unknown')
                    
                    if old_gender != gender_correction:
                        # Обновляем пол
                        upsert_user(user_id, user.get("username"), gender_correction)
                        save_session(user_id, session['stage'], {**session['data'], "gender": gender_correction})
                        
                        correction_msg = bati_gender_correction(name, old_gender, gender_correction)
                        send_message(chat_id, correction_msg)
                        return "OK", 200

            # Обработка ингредиентов
            if session and session['stage'] == 'ask_ingredients':
                name = session['data'].get('name', 'детка')
                gender = session['data'].get('gender', 'unknown')
                handle_ingredients(chat_id, user_id, text, name, gender)
                return "OK", 200

            # Обработка шагов готовки
            if session and session['stage'] == 'cooking':
                if text.lower() in ['далее', 'дальше', 'следующий шаг', 'готово', 'ок', 'ok', 'да', 'продолжаем']:
                    name = session['data'].get('name', 'детка')
                    gender = session['data'].get('gender', 'unknown')
                    handle_cooking_step(chat_id, user_id, name, gender)
                    return "OK", 200

            # Общие ответы
            if any(word in text.lower() for word in ['спасибо', 'благодарю', 'отлично', 'круто']):
                session = get_session(user_id)
                if session and session['data'].get('name'):
                    name = session['data']['name']
                    gender = session['data'].get('gender', 'unknown')
                    pronouns = get_gender_pronoun(gender)
                    send_message(chat_id, f"Пожалуйста, {name}, {pronouns['address']}! Ебать, какой ты вежливый! Рад помочь! 😊")
                else:
                    send_message(chat_id, "Пожалуйста! Ебать, какой ты вежливый! Рад помочь! 😊")
                return "OK", 200

            # Если ничего не подошло
            session = get_session(user_id)
            if session and session['data'].get('name'):
                name = session['data']['name']
                gender = session['data'].get('gender', 'unknown')
                pronouns = get_gender_pronoun(gender)
                send_message(chat_id, f"Слушай, {name}, {pronouns['address']}, я не совсем понял. Напиши /start, чтобы начать готовить! Блять, как же я тебя пойму? 👨‍🍳")
            else:
                send_message(chat_id, "Напиши /start, чтобы начать готовить! Блять, как же я тебя пойму? 👨‍🍳")

        return "OK", 200
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка webhook: {e}")
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
    logger.info("🚀 Запуск кулинарного бота-бати...")
    
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