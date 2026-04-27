import telebot
from telebot import types
import json
import os
import random
import threading
import time

TOKEN = "8761456311:AAHa6z8Y-Z_ENh65hG8Onq0tNxy70vyAWxE"
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "players.json"

WORK_DURATION_MIN = 20
WORK_DURATION_MAX = 60
PENALTY_SHORT = 1800
SPECIAL_CHANCE = 0.25
SPECIAL_POWER_DIFF = 20

data_lock = threading.Lock()
fight_lock = threading.Lock()
scheduled_fights = {}

# ===================== РАЙОНЫ =====================
DISTRICTS = {
    "Центр": "Деловое сердце города: банки, офисы, дорогие рестораны. Много полиции.",
    "Старый город": "Исторические здания, узкие улочки, мало камер.",
    "Промышленный": "Заводы, склады, промзона. Мрачно и безлюдно по ночам.",
    "Порт": "Доки, склады, много фур и контейнеров.",
    "Спальный район": "Многоэтажки, дворы, детские площадки. Обычная жизнь.",
    "Рынок": "Огромный вещевой и продуктовый рынок. Хаос и суета.",
    "Университетский городок": "Студенты, общаги, кафе. Молодёжная атмосфера.",
    "Трущобы": "Ветхие дома, высокий уровень преступности. Опасное место.",
    "Элитный квартал": "Коттеджи, закрытые посёлки, охрана на каждом шагу.",
    "Железнодорожный вокзал": "Постоянный поток людей, камеры, полиция.",
    "Набережная": "Прогулочная зона, рестораны, парки. Много туристов.",
    "Гаражный кооператив": "Сотни гаражей, идеальное место для «схронов».",
    "ТЦ «Галактика»": "Огромный торговый центр с подземной парковкой.",
    "Кольцевая развязка": "Перекрёсток крупных дорог, много мотелей и кафе.",
    "Кладбище": "Старые склепы и аллеи. Мрачное и тихое место ночью.",
    "Мебельная фабрика": "Заброшенные цеха на окраине. Идеально для нелегальных дел.",
    "Автосалон «Люкс»": "Дорогие машины на продажу, сервис и мойка. Много камер.",
    "Больничный городок": "Несколько больниц, морг, аптеки. Специфическая атмосфера.",
    "Стадион «Арена»": "Главная спортивная арена города. Много фанатов и полиции.",
    "Заброшенная стройка": "Недостроенные многоэтажки, арматура и бетон. Опасно и безлюдно.",
}

# ===================== МАГАЗИН =====================
SHOP_ITEMS = {
    "medkit": {"name": "Аптечка", "type": "item", "price": 50, "desc": "Снимает штраф и восстанавливает силы."},
    "mask": {"name": "Маска", "type": "item", "price": 80, "desc": "Снижает риск провала у бандита."},
    "lockpick": {"name": "Отмычка", "type": "item", "price": 100, "desc": "Повышает шанс успешной кражи."},
    "radio": {"name": "Рация", "type": "item", "price": 120, "desc": "Повышает шанс удачной операции копа."},
    "armor": {"name": "Бронежилет", "type": "item", "price": 150, "desc": "Снижает штрафы при провале."},
    "pistol": {"name": "Пистолет", "type": "weapon", "price": 200, "desc": "Базовое оружие."},
    "baton": {"name": "Дубинка", "type": "weapon", "price": 170, "desc": "Оружие для копа."},
    "knife": {"name": "Нож", "type": "weapon", "price": 220, "desc": "Оружие для бандита."},
    "bike": {"name": "Мотоцикл", "type": "vehicle", "price": 300, "desc": "Даёт бонус к скорости и реакции."},
    "sedan": {"name": "Седан", "type": "vehicle", "price": 450, "desc": "Комфортный транспорт."},
}

# ===================== РАНГИ =====================
COP_RANKS = [
    (0, "Кадет", 0),
    (50, "Патрульный", 1),
    (150, "Сержант", 3),
    (300, "Детектив", 4),
    (600, "Лейтенант", 5),
    (1000, "Капитан", 6),
    (1500, "Майор", 7),
    (2500, "Подполковник", 8),
    (4000, "Полковник", 9),
    (7000, "Генерал", 10),
]

BANDIT_RANKS = [
    (0, "Шестёрка", 0),
    (50, "Гопник", 1),
    (150, "Боец", 3),
    (300, "Бригадир", 4),
    (600, "Авторитет", 5),
    (1000, "Смотрящий", 6),
    (1500, "Положенец", 7),
    (2500, "Вор в законе", 8),
    (4000, "Смотрящий за городом", 9),
    (7000, "Крёстный отец", 10),
]

# ===================== БАЗА =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if "groups" not in data:
                    return {"groups": {}}
                return data
            except json.JSONDecodeError:
                return {"groups": {}}
    return {"groups": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_group(data, chat_id):
    chat_id = str(chat_id)
    if "groups" not in data:
        data["groups"] = {}
    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {"players": {}}

def get_player(data, chat_id, user_id):
    chat_id = str(chat_id)
    user_id = str(user_id)
    ensure_group(data, chat_id)
    return data["groups"][chat_id]["players"].get(user_id)

def get_all_players_in_group(data, chat_id):
    chat_id = str(chat_id)
    ensure_group(data, chat_id)
    return data["groups"][chat_id]["players"]

def ensure_player_defaults(player):
    defaults = {
        "exp": 0,
        "money": 0,
        "working_until": 0,
        "penalty_until": 0,
        "district": None,
        "chat_id": None,
        "medals": 0,
        "inventory": {},
        "weapon": None,
        "vehicle": None,
        "clues": 0,
        "active_effects": [],
        "wanted": 0,
        "heat": 0,
        "stealth": 0,
        "evidence": 0,
        "target": None,
        "last_action": 0,
        "bounty": 0,
    }
    for k, v in defaults.items():
        if k not in player:
            player[k] = v
    return player

def add_exp(player, amount):
    player["exp"] = max(0, player.get("exp", 0) + amount)

def add_money(player, amount):
    player["money"] = max(0, player.get("money", 0) + amount)

def remove_money(player, amount):
    player["money"] = max(0, player.get("money", 0) - amount)

def add_item(player, item_id, count=1):
    if not isinstance(player.get("inventory"), dict):
        player["inventory"] = {}
    player["inventory"][item_id] = player["inventory"].get(item_id, 0) + count
    if player["inventory"][item_id] <= 0:
        del player["inventory"][item_id]

def remove_item(player, item_id, count=1):
    if not isinstance(player.get("inventory"), dict):
        player["inventory"] = {}
        return
    if item_id not in player["inventory"]:
        return
    player["inventory"][item_id] -= count
    if player["inventory"][item_id] <= 0:
        del player["inventory"][item_id]

def has_item(player, item_id, count=1):
    return player.get("inventory", {}).get(item_id, 0) >= count

def format_time(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m} мин {s} сек" if m > 0 else f"{s} сек"

def get_rank_info(side, exp):
    table = COP_RANKS if side == "cop" else BANDIT_RANKS
    rank_name, rank_bonus = table[0][1], table[0][2]
    for threshold, name, bonus in table:
        if exp >= threshold:
            rank_name, rank_bonus = name, bonus
    return rank_name, rank_bonus

def get_rank(side, exp):
    return get_rank_info(side, exp)[0]

def get_next_rank_info(side, exp):
    table = COP_RANKS if side == "cop" else BANDIT_RANKS
    for threshold, name, bonus in table:
        if exp < threshold:
            return name, threshold - exp
    return None, 0

def make_progress_bar(current, total, length=12):
    if total <= 0:
        return "█" * length
    filled = int(length * current / total)
    filled = max(0, min(length, filled))
    return "█" * filled + "░" * (length - filled)

def get_profile_progress(side, exp):
    table = COP_RANKS if side == "cop" else BANDIT_RANKS
    current_threshold = 0
    next_name = None
    next_threshold = None

    for threshold, name, bonus in table:
        if exp >= threshold:
            current_threshold = threshold
        else:
            next_name = name
            next_threshold = threshold
            break

    if next_name is None:
        return None, None, None

    current_in_rank = exp - current_threshold
    total_needed = next_threshold - current_threshold
    bar = make_progress_bar(current_in_rank, total_needed)
    return next_name, bar, f"{current_in_rank}/{total_needed}"

def get_item_display(player):
    inv = player.get("inventory", {})
    if not inv:
        return "пусто"
    parts = []
    for item_id, count in inv.items():
        name = SHOP_ITEMS.get(item_id, {}).get("name", item_id)
        parts.append(f"{name} x{count}")
    return ", ".join(parts)

def active_effects_cleanup(player):
    now = time.time()
    effects = player.get("active_effects", [])
    if not isinstance(effects, list):
        player["active_effects"] = []
        return
    player["active_effects"] = [e for e in effects if e.get("until", 0) > now]

def has_active_effect(player, effect_type):
    active_effects_cleanup(player)
    for e in player.get("active_effects", []):
        if e.get("type") == effect_type:
            return True
    return False

def add_effect(player, effect_type, duration=3600):
    player.setdefault("active_effects", [])
    player["active_effects"].append({"type": effect_type, "until": time.time() + duration})

def apply_item_effect(player, item_id):
    if item_id == "medkit":
        if player.get("penalty_until", 0) > time.time():
            player["penalty_until"] = 0
            return "Аптечка сняла штраф."
        add_exp(player, 10)
        return "Аптечка помогла восстановиться. +10 опыта."
    if item_id == "mask":
        add_effect(player, "mask", 3600)
        return "Маска активирована на 1 час."
    if item_id == "lockpick":
        add_effect(player, "lockpick", 3600)
        return "Отмычка активирована на 1 час."
    if item_id == "radio":
        add_effect(player, "radio", 3600)
        return "Рация активирована на 1 час."
    if item_id == "armor":
        add_effect(player, "armor", 3600)
        return "Бронежилет активирован на 1 час."
    return "Этот предмет нельзя использовать."

def get_weapon_bonus(weapon_name):
    if not weapon_name:
        return 0
    w = weapon_name.lower()
    if "пистолет" in w:
        return 10
    if "дубинка" in w:
        return 8
    if "нож" in w:
        return 12
    return 5

def get_vehicle_bonus(vehicle_name):
    if not vehicle_name:
        return 0
    v = vehicle_name.lower()
    if "мотоцикл" in v:
        return 7
    if "седан" in v:
        return 5
    return 3

def get_effect_bonus(player, side):
    bonus = 0
    if side == "cop" and has_active_effect(player, "radio"):
        bonus += 8
    if side == "bandit" and has_active_effect(player, "lockpick"):
        bonus += 8
    if side == "bandit" and has_active_effect(player, "mask"):
        bonus += 5
    if has_active_effect(player, "armor"):
        bonus += 4
    return bonus

def get_district_bonus(district, side):
    if not district:
        return 0
    d = district.lower()
    cop_places = ["центр", "вокзал", "тц", "галактика", "элит", "больнич"]
    bandit_places = ["трущ", "заброш", "пром", "стройка", "гараж", "кладби"]
    if side == "cop":
        for x in cop_places:
            if x in d:
                return 6
    else:
        for x in bandit_places:
            if x in d:
                return 6
    return 0

def calc_player_power(player):
    side = player["side"]
    _, rank_bonus = get_rank_info(side, player["exp"])
    base = player["exp"] + rank_bonus * 10
    weapon_bonus = get_weapon_bonus(player.get("weapon"))
    vehicle_bonus = get_vehicle_bonus(player.get("vehicle"))
    effect_bonus = get_effect_bonus(player, side)
    district_bonus = get_district_bonus(player.get("district"), side)
    luck = random.randint(-5, 5)
    return base + weapon_bonus + vehicle_bonus + effect_bonus + district_bonus + luck

def add_wanted(player, amount):
    player["wanted"] = max(0, player.get("wanted", 0) + amount)

def add_heat(player, amount):
    player["heat"] = max(0, player.get("heat", 0) + amount)

def add_stealth(player, amount):
    player["stealth"] = max(0, player.get("stealth", 0) + amount)

def get_visibility_score(player):
    score = 0
    score += player.get("wanted", 0) * 10
    score += player.get("heat", 0) * 5
    score -= player.get("stealth", 0) * 4
    if has_active_effect(player, "mask"):
        score -= 8
    if player.get("vehicle"):
        score += 3
    if player.get("weapon"):
        score += 2
    return max(0, score)

def get_evidence_needed(wanted_level):
    if wanted_level <= 0:
        return 0
    if wanted_level == 1:
        return 10
    if wanted_level == 2:
        return 15
    if wanted_level == 3:
        return 20
    if wanted_level == 4:
        return 25
    return 30

def calculate_bounty(target):
    bounty = 30
    bounty += target.get("wanted", 0) * 20
    bounty += target.get("stealth", 0) * 8
    bounty += target.get("heat", 0) * 5
    bounty += target.get("medals", 0) * 10
    bounty += target.get("exp", 0) // 50
    return min(bounty, 500)

def decay_heat_and_wanted(player):
    now = time.time()
    last = player.get("last_action", 0)
    if not last:
        return
    passed = now - last
    if passed < 3600:
        return
    hours = int(passed // 3600)
    if hours > 0:
        player["heat"] = max(0, player.get("heat", 0) - hours)
        if player.get("wanted", 0) > 0 and hours >= 3:
            player["wanted"] = max(0, player["wanted"] - 1)

# ===================== /start =====================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, "Игра работает только в группе.")
        return
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        if get_player(data, chat_id, user_id):
            bot.reply_to(message, "Ты уже в игре.")
            return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("👮 Полицейский", callback_data="side_cop"))
    kb.add(types.InlineKeyboardButton("🔫 Бандит", callback_data="side_bandit"))
    bot.send_message(chat_id, "Выбери свою сторону:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("side_"))
def choose_side(call):
    side = call.data.split("_")[1]
    chat_id = str(call.message.chat.id)
    user_id = str(call.from_user.id)
    name = call.from_user.first_name or call.from_user.username or "Игрок"

    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        if get_player(data, chat_id, user_id):
            bot.answer_callback_query(call.id, "Ты уже в игре!")
            return
        data["groups"][chat_id]["players"][user_id] = {
            "name": name,
            "side": side,
            "exp": 0,
            "money": 100,
            "working_until": 0,
            "penalty_until": 0,
            "district": None,
            "chat_id": chat_id,
            "medals": 0,
            "inventory": {},
            "weapon": None,
            "vehicle": None,
            "clues": 0,
            "active_effects": [],
            "wanted": 0,
            "heat": 0,
            "stealth": 0,
            "evidence": 0,
            "target": None,
            "last_action": 0,
            "bounty": 0,
        }
        save_data(data)

    side_emoji = "👮" if side == "cop" else "🔫"
    side_name = "полицейский" if side == "cop" else "бандит"

    welcome_text = (
        f"✅ {name}, теперь ты {side_emoji} {side_name}!\n"
        f"──────────────────────────────\n\n"
        f"🎯 Как играть:\n\n"
        f"1️⃣ Напиши «работать» или «работать <район>»\n"
        f"   чтобы начать задание и зарабатывать опыт\n\n"
        f"2️⃣ Используй «профиль» для просмотра статистики\n\n"
        f"3️⃣ Покупай снаряжение в «магазин»\n\n"
        f"4️⃣ Полный список команд — «помощь»\n\n"
        f"💰 Стартовый капитал: 100$\n"
        f"🗺️ Доступные районы: «районы»\n\n"
        f"Удачи в игре! 🎮"
    )

    bot.edit_message_text(
        welcome_text,
        call.message.chat.id,
        call.message.message_id
    )

# ===================== РАЙОНЫ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["районы", "/districts"])
def cmd_districts(message):
    text = (
        "🗺️ СПИСОК РАЙОНОВ ГОРОДА\n"
        "──────────────────────────────\n\n"
    )
    for i, (name, desc) in enumerate(DISTRICTS.items(), 1):
        text += (
            f"📍 {i}. {name}\n"
            f"   ➤ {desc}\n\n"
        )
    bot.reply_to(message, text)

# ===================== РАБОТАТЬ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith("работать"))
def cmd_work(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    text = message.text.strip()
    parts = text.split(maxsplit=1)

    selected_district = None
    if len(parts) > 1:
        selected_district_raw = parts[1].strip().lower()
        matched = None
        for dname in DISTRICTS.keys():
            if dname.lower() == selected_district_raw:
                matched = dname
                break
        if not matched:
            for dname in DISTRICTS.keys():
                if selected_district_raw in dname.lower():
                    matched = dname
                    break
        if matched:
            selected_district = matched
        else:
            bot.reply_to(message, f"Неизвестный район '{parts[1]}'. Используй 'районы'.")
            return

    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)

        now = time.time()
        if player.get("penalty_until", 0) > now:
            bot.reply_to(message, "Ты на штрафе и не можешь работать.")
            return
        if player.get("working_until", 0) > now:
            bot.reply_to(message, "Ты уже занят заданием.")
            return

        side = player["side"]

        if selected_district is None:
            district = random.choice(list(DISTRICTS.keys()))
            msg = (
                f"Ты отправился в случайный район «{district}».\n"
                f"Чтобы выбрать район вручную, напиши: работать <название района>\n"
                f"Для списка районов — команда 'районы'"
            )
        else:
            district = selected_district
            msg = f"Ты отправился в район «{district}»."

        player["district"] = district
        player["last_action"] = now
        duration = random.randint(WORK_DURATION_MIN, WORK_DURATION_MAX) * 60
        player["working_until"] = now + duration
        save_data(data)

    bot.reply_to(message, f"{msg}\nЗадание завершится через {format_time(duration)}.")
    threading.Timer(duration, finish_mission, args=(user_id, chat_id)).start()

def finish_mission(pid, chat_id):
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, pid)
        if not player:
            return
        ensure_player_defaults(player)
        if player.get("working_until", 0) == 0:
            return

        side = player["side"]
        active_effects_cleanup(player)

        success_chance = 0.65
        if side == "cop" and has_active_effect(player, "radio"):
            success_chance += 0.10
        if side == "bandit" and has_active_effect(player, "lockpick"):
            success_chance += 0.10
        if side == "bandit" and has_active_effect(player, "mask"):
            success_chance += 0.07
        if player.get("vehicle"):
            success_chance += 0.03
        if player.get("district"):
            success_chance += get_district_bonus(player["district"], side) / 100.0

        success = random.random() < success_chance
        old_rank = get_rank(side, player["exp"])

        if success:
            if side == "cop":
                reward = random.randint(10, 25)
                player["money"] += reward
                player["exp"] += reward
            else:
                reward = random.randint(20, 60)
                player["money"] += reward
                player["exp"] += reward
                add_wanted(player, 1)
                add_heat(player, 2)
        else:
            if side == "cop":
                player["money"] = max(0, player["money"] - random.randint(5, 15))
                player["penalty_until"] = time.time() + 900
            else:
                reward = random.randint(5, 20)
                player["money"] += reward
                player["exp"] += reward
                add_wanted(player, 2)
                add_heat(player, 3)

        player["last_action"] = time.time()
        new_rank = get_rank(side, player["exp"])
        district = player["district"]
        player["working_until"] = 0
        player["district"] = None
        save_data(data)

    result_text = "✅ Задание выполнено!" if success else "❌ Задание провалено!"
    rank_text = f"\nЗвание: {old_rank} → {new_rank}" if old_rank != new_rank else f"\nЗвание: {new_rank}"
    bot.send_message(
        chat_id,
        f"{result_text}\n"
        f"Район: {district}\n"
        f"Баланс: {player['money']}$\n"
        f"Опыт: {player['exp']}{rank_text}"
    )

# ===================== СКРЫТЬСЯ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["скрыться", "/hide"])
def cmd_hide(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        if player["side"] != "bandit":
            bot.reply_to(message, "Скрываться могут только бандиты.")
            return
        now = time.time()
        if player.get("penalty_until", 0) > now:
            bot.reply_to(message, "На штрафе нельзя скрываться.")
            return
        success = random.random() < (0.5 + player.get("stealth", 0) * 0.03)
        player["last_action"] = now
        if success:
            reduced = random.randint(1, 3)
            player["heat"] = max(0, player.get("heat", 0) - reduced)
            player["stealth"] += 1
            save_data(data)
            bot.reply_to(message, f"Ты залёг на дно. Шум снизился на {reduced}. Скрытность +1.")
        else:
            add_wanted(player, 1)
            add_heat(player, 1)
            save_data(data)
            bot.reply_to(message, "Попытка скрыться провалилась. Розыск +1, шум +1.")

# ===================== ИСКАТЬ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["искать", "/search"])
def cmd_search(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        cop = get_player(data, chat_id, user_id)
        if not cop:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(cop)
        if cop["side"] != "cop":
            bot.reply_to(message, "Искать могут только копы.")
            return
        district = cop.get("district")
        if not district:
            bot.reply_to(message, "Сначала отправься в район командой 'работать <район>'.")
            return

        group_players = get_all_players_in_group(data, chat_id)
        found = []
        total_clues = 0

        for pid, p in group_players.items():
            if p["side"] != "bandit":
                continue
            if p.get("district") != district:
                continue
            vis = get_visibility_score(p)
            chance = 0.35 + min(vis / 100.0, 0.4)
            if random.random() < chance:
                clues = random.randint(1, 4)
                total_clues += clues
                found.append((p["name"], clues))
                p["wanted"] = min(5, p.get("wanted", 0) + 1)

        cop["clues"] = cop.get("clues", 0) + total_clues
        cop["last_action"] = time.time()
        save_data(data)

    if not found:
        bot.reply_to(message, f"В районе «{district}» следов не найдено.")
        return

    text = f"Ты нашёл следы в районе «{district}»:\n"
    for name, clues in found:
        text += f"• {name}: +{clues} улик\n"
    text += f"\nВсего улик собрано: +{total_clues}"
    bot.reply_to(message, text)

# ===================== ОХОТА =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith("охота "))
def cmd_hunt(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(message, "Укажи имя цели. Пример: охота Вася")
        return

    target_name = parts[1].strip().lower()

    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        cop = get_player(data, chat_id, user_id)
        if not cop:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(cop)
        if cop["side"] != "cop":
            bot.reply_to(message, "Охоту может объявлять только коп.")
            return

        group_players = get_all_players_in_group(data, chat_id)
        target_id = None
        target_player = None

        for pid, p in group_players.items():
            if p["name"].lower() == target_name and p["side"] == "bandit":
                target_id = pid
                target_player = p
                break

        if not target_player:
            bot.reply_to(message, "Такой бандит в группе не найден.")
            return

        needed = get_evidence_needed(target_player.get("wanted", 0))
        if cop.get("clues", 0) < needed:
            bot.reply_to(message, f"Недостаточно улик для охоты. Нужно {needed}, у тебя {cop.get('clues', 0)}.")
            return

        cop["target"] = target_id
        cop["clues"] -= needed
        cop["last_action"] = time.time()
        target_player["bounty"] = calculate_bounty(target_player)
        save_data(data)

    bot.reply_to(
        message,
        f"Охота объявлена на {target_player['name']}.\n"
        f"Награда за поимку: {target_player['bounty']}$"
    )

# ===================== ЗАДЕРЖАТЬ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["задержать", "/arrest"])
def cmd_arrest(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        cop = get_player(data, chat_id, user_id)
        if not cop:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(cop)
        if cop["side"] != "cop":
            bot.reply_to(message, "Задерживать могут только копы.")
            return

        target_id = cop.get("target")
        if not target_id:
            bot.reply_to(message, "У тебя нет цели. Сначала объяви охоту.")
            return

        group_players = get_all_players_in_group(data, chat_id)
        target = group_players.get(target_id)
        if not target or target.get("side") != "bandit":
            cop["target"] = None
            save_data(data)
            bot.reply_to(message, "Цель недоступна.")
            return

        arrest_power = calc_player_power(cop)
        escape_power = calc_player_power(target)

        wanted = target.get("wanted", 0)
        arrest_power += max(0, (cop.get("clues", 0)) * 2)
        escape_power += wanted * 8

        if target.get("vehicle"):
            escape_power += 5
        if has_active_effect(target, "mask"):
            escape_power += 6

        bounty = target.get("bounty", calculate_bounty(target))

        if arrest_power >= escape_power:
            target["money"] = int(target.get("money", 0) * 0.7)
            target["wanted"] = 0
            target["heat"] = 0
            target["penalty_until"] = time.time() + PENALTY_SHORT
            cop["exp"] += 20
            cop["money"] += bounty
            cop["medals"] = cop.get("medals", 0) + 1
            cop["target"] = None
            save_data(data)
            bot.reply_to(
                message,
                f"✅ Цель {target['name']} задержана!\n"
                f"Награда: +{bounty}$\n"
                f"+20 опыта и медаль."
            )
        else:
            cop["target"] = None
            cop["penalty_until"] = time.time() + 900
            save_data(data)
            bot.reply_to(message, f"❌ Цель {target['name']} ушла. Попробуй снова позже.")

# ===================== ПРОФИЛЬ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["профиль", "/profile"])
def cmd_profile(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        active_effects_cleanup(player)
        save_data(data)

    side_emoji = "👮" if player["side"] == "cop" else "🔫"
    side_text = "Полицейский" if player["side"] == "cop" else "Бандит"
    rank = get_rank(player["side"], player["exp"])
    next_rank, progress_bar, progress_nums = get_profile_progress(player["side"], player["exp"])

    weapon = player.get("weapon") or "нет"
    vehicle = player.get("vehicle") or "нет"
    inventory = get_item_display(player)

    effects_list = player.get("active_effects", [])
    effects = "нет" if not effects_list else ", ".join(
        f"{e['type']} ({format_time(e['until'] - time.time())})" for e in effects_list
    )

    now = time.time()
    if player.get("working_until", 0) > now:
        remaining = int(player["working_until"] - now)
        district = player.get("district", "неизвестно")
        status = f"🔄 На задании в «{district}» ({format_time(remaining)})"
    elif player.get("penalty_until", 0) > now:
        remaining = int(player["penalty_until"] - now)
        status = f"⛔ На штрафе ({format_time(remaining)})"
    else:
        status = "✅ Свободен"

    if next_rank is None:
        progress_text = "📊 Прогресс: Максимальное звание"
        next_rank_text = "макс"
    else:
        progress_text = f"📊 Прогресс: {progress_bar} {progress_nums}"
        next_rank_text = next_rank

    text = (
        "📋 ЛИЧНОЕ ДЕЛО\n"
        "─────────────────────────\n"
        f"👤 Имя: {player['name']}\n"
        f"🏷 Статус: {side_emoji} {side_text}\n"
        f"🎖 Звание: {rank}\n"
        f"⭐ Опыт: {player['exp']}\n"
        f"💰 Деньги: {player['money']}$\n"
        f"📍 Состояние: {status}\n"
        f"{progress_text}\n"
        f"⏭ Следующее звание: {next_rank_text}\n\n"
        f"🔫 Оружие: {weapon}\n"
        f"🚗 Транспорт: {vehicle}\n"
        f"🎒 Инвентарь: {inventory}\n"
        f"✨ Эффекты: {effects}\n"
        f"🚨 Розыск: {player.get('wanted', 0)}\n"
        f"🥷 Скрытность: {player.get('stealth', 0)}\n"
        f"🔥 Шум: {player.get('heat', 0)}"
    )
    bot.reply_to(message, text)

# ===================== БАЛАНС =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["баланс", "/balance", "/money"])
def cmd_balance(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)

    text = (
        "💰 ФИНАНСЫ\n"
        "─────────────────────────\n"
        f"💵 Баланс: {player['money']}$\n"
        f"🎒 Инвентарь: {get_item_display(player)}"
    )
    bot.reply_to(message, text)

# ===================== МАГАЗИН =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["магазин", "/shop"])
def cmd_shop(message):
    text = (
        "🛒 МАГАЗИН\n"
        "─────────────────────────\n\n"
        "💊 Аптечка — 50$\n"
        "   Код: medkit\n"
        "   Снимает штраф и восстанавливает силы.\n\n"
        "🎭 Маска — 80$\n"
        "   Код: mask\n"
        "   Снижает риск провала у бандита.\n\n"
        "🔓 Отмычка — 100$\n"
        "   Код: lockpick\n"
        "   Повышает шанс успешной кражи.\n\n"
        "📻 Рация — 120$\n"
        "   Код: radio\n"
        "   Повышает шанс удачной операции копа.\n\n"
        "🛡 Бронежилет — 150$\n"
        "   Код: armor\n"
        "   Снижает штрафы при провале.\n\n"
        "🔫 Пистолет — 200$\n"
        "   Код: pistol\n"
        "   Базовое оружие.\n\n"
        "🪵 Дубинка — 170$\n"
        "   Код: baton\n"
        "   Оружие для копа.\n\n"
        "🔪 Нож — 220$\n"
        "   Код: knife\n"
        "   Оружие для бандита.\n\n"
        "🏍 Мотоцикл — 300$\n"
        "   Код: bike\n"
        "   Даёт бонус к скорости и реакции.\n\n"
        "🚗 Седан — 450$\n"
        "   Код: sedan\n"
        "   Комфортный транспорт.\n\n"
        "─────────────────────────\n"
        "Купить: купить <код>"
    )
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith("купить "))
def cmd_buy(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    parts = message.text.lower().strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажи код товара.")
        return
    item_id = parts[1]
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        if item_id not in SHOP_ITEMS:
            bot.reply_to(message, "Нет такого товара.")
            return
        item = SHOP_ITEMS[item_id]
        if player["money"] < item["price"]:
            bot.reply_to(message, "Не хватает денег.")
            return
        remove_money(player, item["price"])
        if item["type"] == "item":
            add_item(player, item_id, 1)
            result = f"Куплен предмет: {item['name']}"
        elif item["type"] == "weapon":
            player["weapon"] = item["name"]
            result = f"Куплено оружие: {item['name']}"
        else:
            player["vehicle"] = item["name"]
            result = f"Куплен транспорт: {item['name']}"
        save_data(data)
    bot.reply_to(message, f"✅ {result}\nОсталось: {player['money']}$")

# ===================== ИНВЕНТАРЬ / ЭФФЕКТЫ / СНАРЯЖЕНИЕ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["инвентарь", "/inventory"])
def cmd_inventory(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)

    text = (
        "🎒 ИНВЕНТАРЬ\n"
        "─────────────────────────\n"
        f"{get_item_display(player)}"
    )
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip().startswith("использовать "))
def cmd_use_item(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    parts = message.text.lower().strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажи предмет.")
        return
    item_id = parts[1]
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        if not has_item(player, item_id):
            bot.reply_to(message, "У тебя нет такого предмета.")
            return
        result = apply_item_effect(player, item_id)
        remove_item(player, item_id, 1)
        save_data(data)
    bot.reply_to(message, f"✅ {result}")


@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["эффекты", "/effects"])
def cmd_effects(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        active_effects_cleanup(player)
        save_data(data)

    effects = player.get("active_effects", [])
    if not effects:
        text = (
            "✨ АКТИВНЫЕ ЭФФЕКТЫ\n"
            "─────────────────────────\n"
            "Активных эффектов нет."
        )
    else:
        lines = [
            "✨ АКТИВНЫЕ ЭФФЕКТЫ\n"
            "─────────────────────────"
        ]
        for e in effects:
            lines.append(f"• {e['type']} — осталось {format_time(e['until'] - time.time())}")
        text = "\n".join(lines)

    bot.reply_to(message, text)


@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["снаряжение", "/gear"])
def cmd_gear(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)

    weapon = player.get("weapon") or "нет"
    vehicle = player.get("vehicle") or "нет"

    text = (
        "⚔️ СНАРЯЖЕНИЕ\n"
        "─────────────────────────\n"
        f"🔫 Оружие: {weapon}\n"
        f"🚗 Транспорт: {vehicle}"
    )
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["снять оружие", "/unequip_weapon"])
def cmd_unequip_weapon(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        if not player.get("weapon"):
            bot.reply_to(message, "У тебя нет оружия.")
            return
        old = player["weapon"]
        player["weapon"] = None
        save_data(data)
    bot.reply_to(message, f"Оружие снято: {old}")

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["снять транспорт", "/unequip_vehicle"])
def cmd_unequip_vehicle(message):
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        player = get_player(data, chat_id, user_id)
        if not player:
            bot.reply_to(message, "Ты ещё не в игре.")
            return
        ensure_player_defaults(player)
        if not player.get("vehicle"):
            bot.reply_to(message, "У тебя нет транспорта.")
            return
        old = player["vehicle"]
        player["vehicle"] = None
        save_data(data)
    bot.reply_to(message, f"Транспорт снят: {old}")

# ===================== ТОП / ПОМОЩЬ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["топ", "/top"])
def cmd_top(message):
    chat_id = str(message.chat.id)
    with data_lock:
        data = load_data()
        ensure_group(data, chat_id)
        players = list(get_all_players_in_group(data, chat_id).values())

    if not players:
        bot.reply_to(message, "Пока нет игроков.")
        return

    players = sorted(players, key=lambda p: p["exp"], reverse=True)

    text = (
        "🏆 ТОП ИГРОКОВ\n"
        "─────────────────────────\n\n"
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(players[:15]):
        mark = medals[i] if i < 3 else f"{i + 1}."
        emoji = "👮" if p["side"] == "cop" else "🔫"
        rank = get_rank(p["side"], p["exp"])
        text += f"{mark} {emoji} {p['name']}\n   {rank} • {p['exp']} опыта\n\n"

    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in ["помощь", "/help"])
def cmd_help(message):
    text = (
        "📌 КОМАНДЫ\n"
        "─────────────────────────\n\n"
        "🎯 Основные:\n"
        "• работать [<район>] — начать задание\n"
        "• районы — список районов\n"
        "• профиль — твоё личное дело\n"
        "• баланс — финансы и инвентарь\n"
        "• топ — рейтинг игроков\n\n"
        "🛒 Магазин:\n"
        "• магазин — список товаров\n"
        "• купить <код> — купить предмет\n\n"
        "🎒 Инвентарь:\n"
        "• инвентарь — показать предметы\n"
        "• использовать <код> — использовать\n"
        "• эффекты — активные эффекты\n"
        "• снаряжение — оружие и транспорт\n"
        "• снять оружие — снять оружие\n"
        "• снять транспорт — снять транспорт\n\n"
        "🔫 Для бандитов:\n"
        "• скрыться — снизить розыск\n\n"
        "👮 Для копов:\n"
        "• искать — собрать улики\n"
        "• охота <имя> — объявить охоту\n"
        "• задержать — задержать цель"
    )
    bot.reply_to(message, text)

# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()