import telebot
import random
import threading
import json
import os
import time
import string

TOKEN =""
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "players.json"
LOCK = threading.Lock()

MAX_GANGSTERS = 5
MISSION_DURATION = 60
DISTRICTS = [
    "Центр",
    "Старый город",
    "Промышленный",
    "Порт",
    "Спальный район",
    "Рынок",
    "Университетский городок",
    "Трущобы",
    "Элитный квартал",
    "Железнодорожный вокзал",
    "Набережная",
    "Гаражный кооператив",
    "ТЦ «Галактика»",
    "Кольцевая развязка",
    "Кладбище",
    "Мебельная фабрика",
    "Автосалон «Люкс»",
    "Больничный городок",
    "Стадион «Арена»",
    "Заброшенная стройка"
]

DEAD_CLEANUP_SECONDS = 3600  # удалять мёртвых через 1 час

EQUIPMENT_SHOP = {
    "пистолет": {"price": 300, "desc": "Оружие дальнего боя."},
    "нож": {"price": 150, "desc": "Холодное оружие для ближнего боя."},
    "бронежилет": {"price": 200, "desc": "Повышает выживаемость."},
}

MALE_NAMES = [
    "Джон", "Марк", "Алексей", "Виктор", "Дмитрий",
    "Аарон", "Бенджамин", "Чарльз", "Давид", "Эдвард",
    "Франсиско", "Габриэль", "Генри", "Исаак", "Джеймс",
    "Кристиан", "Леонардо", "Майкл", "Натан", "Оливер",
    "Патрик", "Куинтон", "Райан", "Стивен", "Тимофей",
    "Уильям", "Василий", "Захар", "Игорь", "Карл",
    "Лукас", "Матиас", "Николас", "Оскар", "Павел",
    "Роберт", "Сэмюэл", "Тимур", "Уэсли", "Эрик"
]

FEMALE_NAMES = [
    "Йоко", "Анна", "Елена", "Марина", "Кира",
    "Александра", "Белла", "Кэтрин", "Диана", "Ева",
    "Фатима", "Габриэлла", "Ханна", "Изабель", "Джессика",
    "Клара", "Лилия", "Мелисса", "Нина", "Оливия",
    "Полина", "Куин", "Рэйчел", "София", "Тамара",
    "Ульяна", "Валентина", "Зоя", "Ирина", "Карина",
    "Лаура", "Маргарита", "Наталья", "Оксана", "Петра",
    "Роза", "Светлана", "Татьяна", "Урсула", "Элина"
]

SURNAMES = [
    "Смит", "Иванов", "Петров", "Джонсон", "Ковальчук",
    "Мюллер", "Гонсалес", "Такэучи", "Нгуен", "Пападопулос",
    "О’Коннор", "Ли", "Хансен", "Романов", "Фернандес",
    "Ким", "Кузнецов", "Седов", "Перес", "Шварц",
    "Фишер", "Танaka", "Абдуллаев", "Мартинес", "Самуэль",
    "Джексон", "Нильсен", "Чжан", "Лопес", "Волков",
    "Салазар", "Оливейра", "Камачо", "Рай", "Беккер",
    "Медина", "Шмидт", "Браун", "Гарсия", "Сингх"
]
BODY_TYPES = ["худой", "нормальный", "плотный", "мускулистый"]

BANDIT_EVENTS = [
    ("Украл бумажник с уличного кафе", 6),
    ("Сбил с толпы часы", 8),
    ("Ограбил мелкий киоск с напитками", 12),
    ("Взорвал банкомат на окраине", 25),
    ("Похитил посылку с рынка", 15),
    ("Организовал мелкую вымогательскую схему", 18),
    ("Подбросил наркотики конкурирующей банде", 20),
    ("Провёл ловушку на наивного прохожего", 7),
    ("Купил и перепродал краденый телефон", 22),
    ("Погонялся за наёмником соперника и ограбил", 30),
    ("Организовал подпольный бар", 40),
    ("Выполнил заказ по кражам картин из галереи", 50),
    ("Провёл контрабанду сигарет через порт", 45),
    ("Устроил поджог в районе конкурентов", 38),
    ("Ограбил инкассаторскую машину с кокаином", 60),
    ("Продал поддельный алкоголь в элитном квартале", 28),
    ("Взял под контроль склад с авто-запчастями", 50),
    ("Организовал похищение влиятельного бизнесмена", 70),
    ("Устроил крупную сделку на рынке краденого оружия", 65),
    ("Провёл успешное очищение территории от врагов", 80),
    ("Организовал подпольный казино-клуб", 75),
    ("Взял заказ на устранение конкурента", 85),
    ("Провёл диверсию на складе спецтехники", 90),
    ("Разогнал полицейский рейд на банде соперников", 70),
    ("Ограбил банк с использованием взрывчатки", 100),
    ("Закрыл дорогостоящую сделку по продаже наркотиков", 95),
    ("Организовал транспортировку контрабанды через порт", 85),
    ("Сорвал сделку у вражеской организации", 60),
    ("Успешно захватил новый район и установил контроль", 100),
]

BANDIT_FAIL_EVENTS = [
    ("Попался на мелком воре, едва улизнул", -10),
    ("Заказчик отказался платить по надуманной причине", -15),
    ("Подельник сдал тебя полиции — пришлось залечь на дно", -20),
    ("Облава испортила всю операцию, пришлось бежать", -18),
    ("Товар оказался контрафактным — всё ушло в убыток", -25),
    ("Жертва оказалась крепче, чем ожидалось — миссия провалена", -22),
    ("Конкуренты перехватили груз в последний момент", -30),
    ("Сработала сигнализация раньше времени, операция сорвалась", -16),
    ("Камера зафиксировала твоё лицо, пришлось срочно менять план", -12),
    ("Покупатель оказался подставой — потерял всё", -28),
    ("Машина скрытия сломалась во время отхода", -18),
    ("Полиция внезапно устроила облаву прямо на месте", -20),
    ("Информатор оказался двойным агентом", -22),
    ("План провалился из-за измены напарника", -35),
    ("Проникновение в хранилище закончилось падением и травмой", -25),
    ("Склад оказался пуст — ложная наводка", -15),
    ("При отходе попал в ДТП, засветился", -20),
    ("Вражеская банда устроила засаду и забрала всё", -30),
    ("Крыша потребовала большую долю — операция провалена", -40),
    ("Операция сорвалась из-за неожиданного подкрепления полиции", -35),
]

MARKET_OFFERS = {}
DELETED_IDS = set()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"groups": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"groups": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_group(data, chat_id):
    return data.setdefault("groups", {}).setdefault(str(chat_id), {"players": {}, "districts": {}})

def get_player(data, chat_id, user_id, message=None):
    group = get_group(data, chat_id)
    players = group.setdefault("players", {})
    player = players.setdefault(str(user_id), {
        "money": 1000,
        "gangsters": {},
        "districts_controlled": [],
        "kills": 0,
        "first_name": "",
        "last_name": "",
        "username": ""
    })
    if message is not None:
        player["first_name"] = message.from_user.first_name or ""
        player["last_name"] = message.from_user.last_name or ""
        player["username"] = message.from_user.username or ""
    return player

def ensure_defaults(player):
    player.setdefault("money", 1000)
    player.setdefault("gangsters", {})
    player.setdefault("districts_controlled", [])
    player.setdefault("kills", 0)
    player.setdefault("first_name", "")
    player.setdefault("last_name", "")
    player.setdefault("username", "")

def player_display_name(player):
    name = " ".join([x for x in [player.get("first_name", "").strip(), player.get("last_name", "").strip()] if x]).strip()
    if name:
        return name
    if player.get("username"):
        return f"@{player['username']}"
    return "Игрок"

def send_player_notice(chat_id, player, text):
    bot.send_message(chat_id, f"📢 {player_display_name(player)}, {text}")

def can_add_gangster(player):
    return len(player["gangsters"]) < MAX_GANGSTERS

def generate_unique_gangster_id(existing_ids):
    while True:
        new_id = "g_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        if new_id not in existing_ids and new_id not in DELETED_IDS:
            return new_id

def generate_gangster(existing_names):
    for _ in range(100):
        gender = random.choice(["мужской", "женский"])
        first = random.choice(MALE_NAMES if gender == "мужской" else FEMALE_NAMES)
        surname = random.choice(SURNAMES)
        name = f"{first} {surname}"
        if name not in existing_names:
            return {
                "full_name": name,
                "gender": gender,
                "age": random.randint(18, 60),
                "height": random.randint(165, 195) if gender == "мужской" else random.randint(150, 180),
                "body_type": random.choice(BODY_TYPES),
                "alive": True,
                "location": None,
                "equipment": {},
                "created_at": int(time.time()),
                "on_mission_until": 0,
                "mission_status": "none",
                "mission_result": None,
            }
    return None

def has_item(gangster, item):
    return gangster.get("equipment", {}).get(item, 0) > 0

def attacker_power(gangster):
    power = 50
    if has_item(gangster, "пистолет"):
        power += 25
    if has_item(gangster, "нож"):
        power += 15
    if has_item(gangster, "бронежилет"):
        power += 10
    return power

def find_gangster_in_chat(data, chat_id, gangster_id):
    group = get_group(data, chat_id)
    for owner_id, player in group["players"].items():
        if gangster_id in player.get("gangsters", {}):
            return owner_id, player, player["gangsters"][gangster_id]
    return None, None, None

def cleanup_dead_gangsters(data):
    now = int(time.time())
    for chat_id, group in data.get("groups", {}).items():
        for owner_id, player in group.get("players", {}).items():
            gangsters = player.get("gangsters", {})
            to_delete = []
            for gid, g in gangsters.items():
                if not g.get("alive", True):
                    dead_at = g.get("dead_at", g.get("created_at", now))
                    if now - dead_at >= DEAD_CLEANUP_SECONDS:
                        to_delete.append(gid)
            for gid in to_delete:
                DELETED_IDS.add(gid)
                del gangsters[gid]

def fmt_money(n):
    return f"+{n}$" if n > 0 else f"{n}$"

@bot.message_handler(commands=["start"])
def start(message):
    with LOCK:
        data = load_data()
        get_player(data, message.chat.id, message.from_user.id, message)
        save_data(data)
    bot.reply_to(message, "🎉 Ты зарегистрирован!\nНапиши: помощь")

@bot.message_handler(func=lambda m: m.text is not None)
def handle_commands(message):
    text = message.text.strip()
    lowered = text.lower()
    chat_id = message.chat.id
    user_id = message.from_user.id

    if lowered == "помощь":
        help_text = (
            "📜 Доступные команды:\n\n"
            "баланс — показать свой баланс денег\n"
            "магазин — список доступного снаряжения\n"
            "рынок наемников — показать наемников для найма\n"
            "нанять <номер> или нанять — нанять наемника с рынка либо случайного\n"
            "гангстеры — показать своих гангстеров\n"
            "все гангстеры — показать всех гангстеров в чате\n"
            "гэнста — ответом на сообщение показать гангстеров того игрока\n"
            "купить <предмет> <id_гангстера> — купить снаряжение\n"
            "отправить <id_гангстера> <район> — отправить гангстера в район\n"
            "выстрелить <id_атакующего> <id_жертвы> — атаковать гангстера с пистолетом\n"
            "ограбить <id_атакующего> <id_жертвы> — попытаться ограбить гангстера с ножом\n"
            "захватить <id_гангстера> <район> — захватить район гангстером\n"
            "районы — показать доступные районы\n"
            "топ — топ 5 игроков по деньгам\n"
        )
        bot.reply_to(message, help_text)
        return

    if lowered == "баланс":
        with LOCK:
            data = load_data()
            player = get_player(data, chat_id, user_id, message)
            ensure_defaults(player)
        bot.reply_to(message, f"💰 Твой баланс: {player['money']}$")
        return

    if lowered == "магазин":
        out = "🛒 Магазин снаряжения:\n\n"
        for item, info in EQUIPMENT_SHOP.items():
            out += f"• {item.capitalize()} ({info['price']}$) — {info['desc']}\n"
        bot.reply_to(message, out)
        return

    if lowered == "районы":
        bot.reply_to(message, "📍 Доступные районы:\n" + "\n".join(f"• {d}" for d in DISTRICTS))
        return

    if lowered == "гэнста":
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Используй эту команду ответом на сообщение игрока.")
            return
        target_user_id = message.reply_to_message.from_user.id
        with LOCK:
            data = load_data()
            group = get_group(data, chat_id)
            target_player = group["players"].get(str(target_user_id))
            if not target_player:
                bot.reply_to(message, "⚠️ У этого игрока нет данных.")
                return
            if not target_player.get("gangsters"):
                bot.reply_to(message, "⚠️ У этого игрока нет гангстеров.")
                return
            out = f"🕵️ Гангстеры игрока {player_display_name(target_player)}:\n\n"
            for gid, g in target_player["gangsters"].items():
                status = "☠️ мёртв" if not g.get("alive", True) else "✅ жив"
                loc = g.get("location") or "без района"
                out += f"ID: {gid}\nИмя: {g['full_name']}\nСтатус: {status}\nРайон: {loc}\n\n"
            bot.reply_to(message, out)
        return

    if lowered == "гангстеры":
        with LOCK:
            data = load_data()
            player = get_player(data, chat_id, user_id, message)
            ensure_defaults(player)
            if not player["gangsters"]:
                bot.reply_to(message, "⚠️ У тебя нет гангстеров.")
                return
            out = "🕵️ Твои гангстеры:\n\n"
            for gid, g in player["gangsters"].items():
                status = "☠️ мёртв" if not g.get("alive", True) else "✅ жив"
                loc = g.get("location") or "не назначен"
                equip = ", ".join(f"{k} x{v}" for k, v in g.get("equipment", {}).items()) or "без экипировки"
                out += f"ID: {gid}\nИмя: {g['full_name']}\nСтатус: {status}\nЛокация: {loc}\nЭкипировка: {equip}\n\n"
            bot.reply_to(message, out)
        return

    if lowered == "все гангстеры":
        with LOCK:
            data = load_data()
            group = get_group(data, chat_id)
            out = "📋 Все гангстеры в чате:\n\n"
            found = False
            for _, player in group["players"].items():
                for gid, g in player.get("gangsters", {}).items():
                    found = True
                    out += f"Владелец: {player_display_name(player)}\nID: {gid}\nИмя: {g['full_name']}\n\n"
            if not found:
                bot.reply_to(message, "⚠️ В этом чате пока нет гангстеров.")
                return
            bot.reply_to(message, out)
        return

    if lowered.startswith("рынок наемников"):
        offers = []
        used = set()
        while len(offers) < 3:
            g = generate_gangster(set())
            if g["full_name"] in used:
                continue
            used.add(g["full_name"])
            g["price"] = random.choice([400, 500, 600, 700, 800])
            offers.append(g)
        MARKET_OFFERS[str(user_id)] = offers
        out = "💼 Рынок наемников:\n\n"
        for i, g in enumerate(offers, 1):
            out += (
                f"{i}. {g['full_name']}\n"
                f"   Пол: {g['gender']}\n"
                f"   Возраст: {g['age']}\n"
                f"   Рост: {g['height']} см\n"
                f"   Телосложение: {g['body_type']}\n"
                f"   Цена найма: {g['price']}$\n\n"
            )
        out += "Чтобы нанять, пиши: нанять <номер>\nИли просто: нанять"
        bot.reply_to(message, out)
        return

    if lowered.startswith("нанять"):
        parts = text.split()
        with LOCK:
            data = load_data()
            player = get_player(data, chat_id, user_id, message)
            ensure_defaults(player)
            if not can_add_gangster(player):
                bot.reply_to(message, "⚠️ Максимум гангстеров достигнут.")
                return

            if len(parts) == 2:
                try:
                    choice = int(parts[1]) - 1
                except ValueError:
                    bot.reply_to(message, "⚠️ Используй: нанять <номер>")
                    return
                offers = MARKET_OFFERS.get(str(user_id))
                if not offers:
                    bot.reply_to(message, "⚠️ Сначала открой рынок: рынок наемников")
                    return
                if choice < 0 or choice >= len(offers):
                    bot.reply_to(message, "⚠️ Нет такого номера.")
                    return
                gangster = offers[choice]
                price = gangster["price"]
            else:
                existing = {g["full_name"] for g in player["gangsters"].values()}
                gangster = generate_gangster(existing)
                if gangster is None:
                    bot.reply_to(message, "⚠️ Не удалось создать гангстера.")
                    return
                price = 500
                gangster["price"] = price

            if player["money"] < price:
                bot.reply_to(message, f"⚠️ Недостаточно денег. Нужно {price}$.")
                return

            existing_ids = set(player["gangsters"].keys())
            gid = generate_unique_gangster_id(existing_ids)

            player["money"] -= price
            player["gangsters"][gid] = gangster
            save_data(data)

        send_player_notice(chat_id, player, f"нанял гангстера {gangster['full_name']} (ID: {gid}).")
        return

    if lowered.startswith("купить"):
        parts = text.split()
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Используй: купить <предмет> <id_гангстера>")
            return
        item = parts[1].lower()
        gid = parts[2]
        if item not in EQUIPMENT_SHOP:
            bot.reply_to(message, "⚠️ Такого предмета нет в магазине.")
            return
        with LOCK:
            data = load_data()
            player = get_player(data, chat_id, user_id, message)
            gangster = player["gangsters"].get(gid)
            if not gangster:
                bot.reply_to(message, "⚠️ Гангстер не найден.")
                return
            price = EQUIPMENT_SHOP[item]["price"]
            if player["money"] < price:
                bot.reply_to(message, f"⚠️ Не хватает денег. Нужно {price}$.")
                return
            player["money"] -= price
            gangster.setdefault("equipment", {})
            gangster["equipment"][item] = gangster["equipment"].get(item, 0) + 1
            save_data(data)
        send_player_notice(chat_id, player, f"купил {item} для гангстера {gangster['full_name']}.")
        return

    if lowered.startswith("отправить"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Используй: отправить <id_гангстера> <район>")
            return
        gid = parts[1]
        district = parts[2]
        if district not in DISTRICTS:
            bot.reply_to(message, "⚠️ Такого района нет.")
            return
        with LOCK:
            data = load_data()
            player = get_player(data, chat_id, user_id, message)
            gangster = player["gangsters"].get(gid)
            if not gangster or not gangster.get("alive", True):
                bot.reply_to(message, "⚠️ Гангстер не найден или мёртв.")
                return
            gangster["location"] = district
            gangster["on_mission_until"] = int(time.time()) + MISSION_DURATION
            gangster["mission_status"] = "active"
            gangster["mission_result"] = None
            save_data(data)
        send_player_notice(chat_id, player, f"отправил гангстера {gangster['full_name']} в район {district}.")
        return

    if lowered.startswith("выстрелить"):
        parts = text.split()
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Используй: выстрелить <id_атакующего> <id_жертвы>")
            return
        attacker_id, victim_id = parts[1], parts[2]
        with LOCK:
            data = load_data()
            att_owner_id, attacker_owner, attacker = find_gangster_in_chat(data, chat_id, attacker_id)
            vic_owner_id, victim_owner, victim = find_gangster_in_chat(data, chat_id, victim_id)
            if not attacker or not victim:
                bot.reply_to(message, "⚠️ Один из гангстеров не найден.")
                return
            if att_owner_id == vic_owner_id:
                bot.reply_to(message, "⚠️ Нельзя атаковать своего гангстера.")
                return
            if not attacker.get("alive", True) or not victim.get("alive", True):
                bot.reply_to(message, "⚠️ Один из гангстеров мёртв.")
                return
            if not has_item(attacker, "пистолет"):
                bot.reply_to(message, "⚠️ У атакующего нет пистолета.")
                return
            if attacker.get("location") != victim.get("location") or attacker.get("location") is None:
                bot.reply_to(message, "⚠️ Гангстеры должны находиться в одном районе.")
                return

            success = random.random() < (attacker_power(attacker) / (attacker_power(attacker) + attacker_power(victim)))
            if success:
                victim["alive"] = False
                victim["dead_at"] = int(time.time())
                attacker_owner["kills"] = attacker_owner.get("kills", 0) + 1
                save_data(data)
                send_player_notice(chat_id, attacker_owner, f"гангстер {attacker['full_name']} выстрелил в {victim['full_name']} и убил его.")
            else:
                save_data(data)
                send_player_notice(chat_id, attacker_owner, f"гангстер {attacker['full_name']} выстрелил в {victim['full_name']}, но промахнулся.")
        return

    if lowered.startswith("ограбить"):
        parts = text.split()
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Используй: ограбить <id_атакующего> <id_жертвы>")
            return
        attacker_id, victim_id = parts[1], parts[2]
        with LOCK:
            data = load_data()
            att_owner_id, attacker_owner, attacker = find_gangster_in_chat(data, chat_id, attacker_id)
            vic_owner_id, victim_owner, victim = find_gangster_in_chat(data, chat_id, victim_id)
            if not attacker or not victim:
                bot.reply_to(message, "⚠️ Один из гангстеров не найден.")
                return
            if att_owner_id == vic_owner_id:
                bot.reply_to(message, "⚠️ Нельзя атаковать своего гангстера.")
                return
            if not attacker.get("alive", True) or not victim.get("alive", True):
                bot.reply_to(message, "⚠️ Один из гангстеров мёртв.")
                return
            if not has_item(attacker, "нож"):
                bot.reply_to(message, "⚠️ У атакующего нет ножа.")
                return
            if attacker.get("location") != victim.get("location") or attacker.get("location") is None:
                bot.reply_to(message, "⚠️ Гангстеры должны находиться в одном районе.")
                return

            success = random.random() < (attacker_power(attacker) / (attacker_power(attacker) + attacker_power(victim)))
            if success:
                loot = random.randint(50, 300)
                victim_owner["money"] = max(0, victim_owner.get("money", 0) - loot)
                attacker_owner["money"] = attacker_owner.get("money", 0) + loot
                save_data(data)
                send_player_notice(chat_id, attacker_owner, f"гангстер {attacker['full_name']} ограбил {victim['full_name']} и забрал {loot}$.")
            else:
                save_data(data)
                send_player_notice(chat_id, attacker_owner, f"гангстер {attacker['full_name']} попытался ограбить {victim['full_name']}, но потерпел неудачу.")
        return

    if lowered.startswith("захватить"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Используй: захватить <id_гангстера> <название района>")
            return
        gid = parts[1]
        district = parts[2]
        if district not in DISTRICTS:
            bot.reply_to(message, "⚠️ Такого района нет.")
            return
        with LOCK:
            data = load_data()
            group = get_group(data, chat_id)
            player = get_player(data, chat_id, user_id, message)
            gangster = player["gangsters"].get(gid)
            if not gangster or not gangster.get("alive", True):
                bot.reply_to(message, "⚠️ Гангстер не найден или мёртв.")
                return
            if gangster.get("location") != district:
                bot.reply_to(message, "⚠️ Гангстер должен находиться в этом районе.")
                return
            if district in group.get("districts", {}) and group["districts"].get(district):
                bot.reply_to(message, "⚠️ Район уже захвачен.")
                return
            group.setdefault("districts", {})[district] = {
                "owner_id": str(user_id),
                "gangster_id": gid,
                "owner_name": player_display_name(player),
                "gangster_name": gangster["full_name"]
            }
            if district not in player["districts_controlled"]:
                player["districts_controlled"].append(district)
            save_data(data)
        send_player_notice(chat_id, player, f"захватил район {district} гангстером {gangster['full_name']}.")
        return

    if lowered == "топ":
        with LOCK:
            data = load_data()
            group = data.get("groups", {}).get(str(chat_id))
            if not group:
                bot.reply_to(message, "Нет данных по этому чату.")
                return
            players = group.get("players", {})
            # Сортируем по деньгам и по убийствам
            top_money = sorted(players.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:5]
            top_kills = sorted(players.items(), key=lambda x: x[1].get("kills", 0), reverse=True)[:5]

            out = "💰 Топ по деньгам:\n"
            for i, (_, p) in enumerate(top_money, 1):
                out += f"{i}. {player_display_name(p)} — {p.get('money', 0)}$\n"

            out += "\n🔪 Топ по убийствам:\n"
            for i, (_, p) in enumerate(top_kills, 1):
                out += f"{i}. {player_display_name(p)} — {p.get('kills', 0)} убийств\n"

            bot.reply_to(message, out)
        return

def mission_watcher():
    while True:
        time.sleep(5)
        now = int(time.time())
        with LOCK:
            data = load_data()
            modified = False
            cleanup_dead_gangsters(data)

            for chat_id, group in data.get("groups", {}).items():
                for _, player in group.get("players", {}).items():
                    for gid, gangster in player.get("gangsters", {}).items():
                        if gangster.get("mission_status") == "active" and gangster.get("on_mission_until", 0) <= now:
                            if gangster.get("mission_result") is None:
                                if random.random() < 0.75:
                                    event, profit = random.choice(BANDIT_EVENTS)
                                    gangster["mission_result"] = {"success": True, "text": event, "profit": profit}
                                else:
                                    event, loss = random.choice(BANDIT_FAIL_EVENTS)
                                    gangster["mission_result"] = {"success": False, "text": event, "profit": loss}
                            result = gangster["mission_result"]
                            player["money"] += result["profit"]
                            gangster["mission_status"] = "none"
                            gangster["mission_result"] = None
                            gangster["location"] = None
                            gangster["on_mission_until"] = 0
                            modified = True
                            try:
                                bot.send_message(int(chat_id), f"📢 {player_display_name(player)}, гангстер {gangster['full_name']} вернулся с задания: {result['text']} {fmt_money(result['profit'])}")
                            except Exception:
                                pass

            if modified:
                save_data(data)

threading.Thread(target=mission_watcher, daemon=True).start()

print("Бот запущен")
bot.infinity_polling()