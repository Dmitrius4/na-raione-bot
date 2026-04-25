# na_raione.py — Часть 1

import telebot
from telebot import types
import json, os, random, threading, time, math

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "players.json"
WORK_DURATION = 3600       # 1 час — задание
PENALTY_SHORT = 1800       # 30 мин — штраф за проигрыш
PENALTY_LONG = 3600        # 1 час — штраф за «особый исход»
SPECIAL_CHANCE = 0.25      # 25% шанс на особый исход
SPECIAL_POWER_DIFF = 20    # разница силы для особого исхода

bot = telebot.TeleBot(TOKEN)
data_lock = threading.Lock()

# ===================== РАЙОНЫ (20 шт.) =====================
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

# ===================== ЗАДАНИЯ КОПА (49 шт.) =====================
COP_EVENTS = [
    ("Патрулировал район и предотвратил мелкое хулиганство", 5),
    ("Помог пожилому человеку, потерявшему документы", 5),
    ("Оштрафовал водителя за превышение скорости", 7),
    ("Задержал карманника в общественном транспорте", 10),
    ("Раскрыл кражу велосипеда по горячим следам", 12),
    ("Помог найти потерявшегося ребёнка", 15),
    ("Задержал пьяного дебошира", 10),
    ("Провёл профилактическую беседу с подростками", 5),
    ("Раскрыл серию краж из автомобилей", 20),
    ("Помог эвакуировать людей из задымлённого здания", 15),
    ("Задержал угонщика автомобиля", 20),
    ("Раскрыл дело о распространении наркотиков в районе", 25),
    ("Помог раскрыть мошенничество с банковскими картами", 20),
    ("Обезвредил агрессивную собаку на улице", 10),
    ("Помог вернуть украденный телефон владельцу", 12),
    ("Раскрыл дело о вандализме (разбитые остановки)", 15),
    ("Задержал группу подростков, портящих имущество", 15),
    ("Помог раскрыть квартирную кражу по камерам наблюдения", 20),
    ("Остановил драку в баре", 15),
    ("Раскрыл дело о незаконной торговле алкоголем", 20),
    ("Помог найти свидетелей ДТП", 10),
    ("Задержал рецидивиста, находящегося в розыске", 30),
    ("Раскрыл дело о мошенничестве с недвижимостью", 25),
    ("Помог раскрыть дело о домашнем насилии", 20),
    ("Провёл успешную операцию по задержанию группы автоугонщиков", 35),
    ("Раскрыл дело о подделке документов", 20),
    ("Помог раскрыть серию телефонных мошенничеств", 25),
    ("Задержал вооружённого грабителя магазина", 30),
    ("Раскрыл дело о незаконном обороте оружия", 35),
    ("Помог раскрыть дело о коррупции в мелкой организации", 30),
    ("Провёл успешное задержание наркоторговца", 40),
    ("Раскрыл дело о краже из банкомата", 35),
    ("Помог раскрыть дело о торговле запрещёнными веществами", 40),
    ("Задержал серийного вора, орудовавшего в районе", 45),
    ("Раскрыл дело о мошенничестве с пенсионными накоплениями", 40),
    ("Провёл операцию по освобождению заложников", 50),
    ("Помог раскрыть дело о заказном убийстве", 60),
    ("Раскрыл международную преступную схему", 70),
    ("Помог предотвратить теракт", 80),
    ("Задержал лидера крупной преступной группировки", 100),
    ("Провёл успешное расследование по делу о киберпреступности", 45),
    ("Помог раскрыть дело о торговле людьми", 60),
    ("Раскрыл дело о крупном мошенничестве с госзакупками", 70),
    ("Провёл операцию по задержанию банды фальшивомонетчиков", 50),
    ("Помог раскрыть дело о похищении человека", 60),
    ("Раскрыл дело о шпионаже", 80),
    ("Провёл успешное расследование по делу о коррупции в полиции", 70),
    ("Помог предотвратить покушение на высокопоставленное лицо", 90),
    ("Раскрыл заговор против государства", 100),
]

# ===================== ПРОВАЛЬНЫЕ ЗАДАНИЯ КОПА (30 шт.) =====================
COP_FAIL_EVENTS = [
    ("Упустил преступника во время погони", -5),
    ("Получил жалобу от гражданина за грубое обращение", -5),
    ("Напарник подставил под удар, пришлось отступить", -8),
    ("Улики оказались недействительными, дело закрыто", -10),
    ("Свидетель отказался давать показания, дело провалено", -8),
    ("Превысил полномочия при задержании, выговор от начальства", -10),
    ("Попал в засаду бандитов, еле выбрался", -12),
    ("Ошибся адресом при обыске, скандал с жильцами", -8),
    ("Потерял служебное удостоверение", -7),
    ("Сломал казённое оборудование при погоне", -6),
    ("Задержал не того человека, пришлось отпустить", -8),
    ("Бандиты подкупили свидетелей, дело рассыпалось", -12),
    ("Получил травму при задержании, отстранён от дежурства", -15),
    ("Допустил утечку информации о готовящейся операции", -15),
    ("Преступник сбежал прямо из-под стражи", -20),
    ("Нарушил процедуру при обыске, доказательства признаны незаконными", -12),
    ("Попался на взятке, служебное расследование", -20),
    ("Упустил крупного наркоторговца из-за бюрократических ошибок", -18),
    ("Засада провалилась — бандиты были предупреждены", -15),
    ("Потерял важного информатора из-за халатности", -15),
    ("Случайно раскрыл личность агента под прикрытием", -20),
    ("Обвиняемый вышел на свободу из-за ошибки в протоколе", -12),
    ("Во время рейда бандиты успели уничтожить улики", -10),
    ("Начальство урезало финансирование операции в последний момент", -8),
    ("Коллега оказался предателем, операция провалена", -25),
    ("Получил ранение при перестрелке", -18),
    ("Машина сломалась в погоне, преступник скрылся", -7),
    ("Камеры наблюдения оказались сломаны, улик нет", -8),
    ("Ордер на обыск отозвали в последний момент", -10),
    ("Провалил проверку на детекторе лжи при внутреннем расследовании", -22),
]

# ===================== ЗАДАНИЯ БАНДИТА (49 шт.) =====================
BANDIT_EVENTS = [
    ("Угнал оставленный без присмотра велосипед", 5),
    ("Вымогал деньги у прохожего", 7),
    ("Украл телефон из незапертой машины", 10),
    ("Разбил стекло в ларьке", 5),
    ("Украл продукты из магазина", 8),
    ("Угнал автомобиль (старый, дешёвый)", 15),
    ("Вымогал «дань» у мелкого торговца", 12),
    ("Украл кошелёк в толпе", 10),
    ("Продал поддельные сигареты", 10),
    ("Угнал мотоцикл", 15),
    ("Взял «заказ» на кражу дорогой техники из квартиры", 20),
    ("Ограбил небольшой магазин (без оружия)", 25),
    ("Украл катализатор с автомобиля", 15),
    ("Вымогал крупную сумму у предпринимателя", 30),
    ("Ограбил банкомат (вскрытие, без взлома)", 35),
    ("Украл партию алкоголя со склада", 25),
    ("Угнал грузовик с товаром", 30),
    ("Ограбил ломбард", 35),
    ("Взял «заказ» на угон дорогого автомобиля", 40),
    ("Организовал подпольный игорный клуб", 40),
    ("Ограбил ювелирный магазин (без жертв)", 50),
    ("Взял «заказ» на кражу ценной картины", 60),
    ("Ограбил инкассаторскую машину", 70),
    ("Организовал канал сбыта краденых запчастей", 50),
    ("Взял «заказ» на устранение конкурента", 60),
    ("Ограбил склад с электроникой", 60),
    ("Взял «заказ» на кражу секретных документов", 70),
    ("Ограбил казино", 80),
    ("Взял «заказ» на похищение человека", 90),
    ("Ограбил банк", 100),
    ("Организовал сеть по продаже поддельных документов", 50),
    ("Взял «заказ» на кражу оружия со склада", 70),
    ("Ограбил фуру с дорогими товарами", 60),
    ("Взял «заказ» на поджог бизнеса конкурента", 50),
    ("Организовал подпольный цех по производству алкоголя", 60),
    ("Взял «заказ» на кражу крупной партии наркотиков", 80),
    ("Ограбил склад с медикаментами", 60),
    ("Взял «заказ» на кражу данных с сервера компании", 70),
    ("Ограбил склад с оружием", 90),
    ("Взял «заказ» на убийство полицейского", 100),
    ("Организовал сеть по сбыту краденых телефонов", 40),
    ("Взял «заказ» на кражу дорогого антиквариата", 70),
    ("Ограбил склад с бытовой техникой", 50),
    ("Взял «заказ» на запугивание свидетеля", 40),
    ("Организовал подпольный тотализатор", 50),
    ("Взял «заказ» на кражу серверного оборудования", 70),
    ("Сорвал крупную сделку конкурентов", 60),
    ("Сжёг склад конкурирующей банды", 80),
    ("Сверг лидера другой банды и захватил территорию", 100),
]

# ===================== ПРОВАЛЬНЫЕ ЗАДАНИЯ БАНДИТА (30 шт.) =====================
BANDIT_FAIL_EVENTS = [
    ("Попался на краже, еле унёс ноги", -5),
    ("Заказчик отказался платить за работу", -8),
    ("Подельник сдал полиции, пришлось залечь на дно", -15),
    ("Облава, пришлось бросить всё и бежать", -12),
    ("Товар оказался палёным, потерял деньги", -8),
    ("Жертва оказала сопротивление, пришлось отступить", -7),
    ("Навёл на себя лишнее внимание полиции", -10),
    ("Конкуренты перехватили груз", -15),
    ("Сигнализация сработала раньше времени, пришлось бежать", -10),
    ("Камера зафиксировала лицо, пришлось срочно менять схему", -12),
    ("Свой же человек обокрал при дележе", -10),
    ("Покупатель оказался копом под прикрытием", -20),
    ("Машина для отхода сломалась в самый неподходящий момент", -8),
    ("Жертва опознала по голосу, пришлось залечь", -12),
    ("Охранник оказался крепче, чем казалось", -10),
    ("Полиция нашла схрон с товаром", -18),
    ("Попал под чужую разборку, потерял всё при себе", -12),
    ("Крыша потребовала увеличить долю под угрозой", -15),
    ("Ограбление сорвалось — внутри оказалось больше охраны", -15),
    ("Информатор оказался двойным агентом", -20),
    ("При отходе попал в ДТП, засветился перед свидетелями", -10),
    ("Конкурирующая банда поставила на счётчик", -18),
    ("Товар при перевозке конфисковали на посту", -15),
    ("Напарник струсил в последний момент, план рухнул", -10),
    ("Жертва оказалась связана с серьёзными людьми", -20),
    ("Сорвался с высоты при проникновении, получил травму", -12),
    ("Ложная наводка — в хранилище оказалось пусто", -8),
    ("Полиция устроила облаву именно в нужном районе", -15),
    ("Покупатель расплатился фальшивками", -10),
    ("Предал доверие смотрящего, репутация подмочена", -25),
]

# ===================== ЗВАНИЯ КОПА =====================
COP_RANKS = [
    (0,    "Кадет",        0),
    (50,   "Патрульный",   1),
    (150,  "Сержант",      3),
    (300,  "Детектив",     4),
    (600,  "Лейтенант",    5),
    (1000, "Капитан",      6),
    (1500, "Майор",        7),
    (2500, "Подполковник", 8),
    (4000, "Полковник",    9),
    (7000, "Генерал",      10),
]

# ===================== ЗВАНИЯ БАНДИТА =====================
BANDIT_RANKS = [
    (0,    "Шестёрка",              0),
    (50,   "Гопник",               1),
    (150,  "Боец",                 3),
    (300,  "Бригадир",             4),
    (600,  "Авторитет",            5),
    (1000, "Смотрящий",            6),
    (1500, "Положенец",            7),
    (2500, "Вор в законе",         8),
    (4000, "Смотрящий за городом", 9),
    (7000, "Крёстный отец",        10),
]
# na_raione.py — Часть 2

# ===================== РАБОТА С ДАННЫМИ =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_rank_info(side, exp):
    """Возвращает (название звания, rank_bonus)"""
    table = COP_RANKS if side == "cop" else BANDIT_RANKS
    rank_name = table[0][1]
    rank_bonus = table[0][2]
    for threshold, name, bonus in table:
        if exp >= threshold:
            rank_name = name
            rank_bonus = bonus
    return rank_name, rank_bonus

def get_rank(side, exp):
    """Возвращает только название звания"""
    return get_rank_info(side, exp)[0]

def get_next_rank_info(side, exp):
    """Возвращает (следующее звание, сколько опыта осталось) или (None, 0)"""
    table = COP_RANKS if side == "cop" else BANDIT_RANKS
    for threshold, name, bonus in table:
        if exp < threshold:
            return name, threshold - exp
    return None, 0

def calc_power(exp, rank_bonus):
    """Power = Experience + (RankBonus × 10) + RandomFactor(-10..+10)"""
    random_factor = random.randint(-10, 10)
    return exp + (rank_bonus * 10) + random_factor

def pick_event_by_rank(side, exp):
    """Выбирает задание с учётом уровня игрока (взвешенный рандом)"""
    events = COP_EVENTS if side == "cop" else BANDIT_EVENTS
    sorted_events = sorted(events, key=lambda e: e[1])
    max_exp_threshold = 7000
    level = min(exp / max_exp_threshold, 1.0)
    max_event_exp = max(e[1] for e in sorted_events)

    weights = []
    for desc, ev_exp in sorted_events:
        event_level = ev_exp / max_event_exp
        diff = abs(event_level - level)
        weight = max(0.05, 1.0 - diff)
        weights.append(weight)

    return random.choices(sorted_events, weights=weights, k=1)[0]

def is_on_cooldown(player):
    """Проверяет, находится ли игрок на кулдауне (задержан/ранен/на задании)"""
    now = time.time()
    # На задании
    if player.get("working_until", 0) > now:
        return True, player["working_until"] - now, "задании"
    # Штрафной кулдаун
    if player.get("penalty_until", 0) > now:
        return True, player["penalty_until"] - now, "штрафе"
    return False, 0, ""

def format_time(seconds):
    """Форматирует секунды в 'X мин Y сек'"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m} мин {s} сек"
    return f"{s} сек"

def add_exp(player, amount):
    """Безопасное изменение опыта — никогда не уходит ниже 0"""
    player["exp"] = max(0, player["exp"] + amount)

# na_raione.py — Часть 3 (ПОЛНАЯ ЗАМЕНА)

FIGHT_DELAY = 10  # сек — окно ожидания других игроков перед стычкой

# Флаги запланированных стычек по району (чтобы не дублировать)
scheduled_fights = {}   # {district: True}
fight_lock = threading.Lock()


# ===================== /start =====================

@bot.message_handler(commands=['start'])
def cmd_start(message):
    # Если пишут в личку — отправляем на группу
    if message.chat.type == "private":
        bot.send_message(message.chat.id,
                         "❌ Эта игра работает только в группе!\n"
                         "👉 Перейди сюда: https://t.me/+GRs5jc8dQuZkZGVi"
                         )
        return

    with data_lock:
        data = load_data()
        pid = str(message.from_user.id)
        if pid in data:
            bot.reply_to(message, "Ты уже в игре! Напиши «работать» или «профиль».")
            return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("👮 Полицейский", callback_data="side_cop"))
    kb.add(types.InlineKeyboardButton("🔫 Бандит", callback_data="side_bandit"))
    bot.send_message(message.chat.id,
                     "🏙 <b>«На районе»</b>\n\n"
                     "Добро пожаловать в криминальный мир города!\n"
                     "Выбери свою сторону:",
                     reply_markup=kb, parse_mode="HTML")


# ===================== Выбор стороны =====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("side_"))
def choose_side(call):
    side = call.data.split("_")[1]
    pid = str(call.from_user.id)

    with data_lock:
        data = load_data()
        if pid in data:
            bot.answer_callback_query(call.id, "Ты уже выбрал сторону!")
            return
        name = (call.from_user.first_name or call.from_user.username or "Безымянный")
        data[pid] = {
            "name": name, "side": side, "exp": 0,
            "working_until": 0, "penalty_until": 0,
            "district": None, "chat_id": call.message.chat.id,
            "medals": 0,
        }
        save_data(data)

    role = "полицейский 👮" if side == "cop" else "бандит 🔫"
    rank = "Кадет" if side == "cop" else "Шестёрка"

    bot.edit_message_text(
        f"🏙 <b>«На районе»</b>\n\n"
        f"<b>{name}</b>, теперь ты — {role}.\n"
        f"Твоё звание: <b>{rank}</b>\n\n"
        f"Пиши «работать», чтобы выйти на дело!",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")


# ===================== Команда «работать» =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in
                     ["работать", "/работать", "/work"])
def cmd_work(message):
    pid = str(message.from_user.id)
    chat_id = message.chat.id
    triggered_district = None

    with data_lock:
        data = load_data()
        player = data.get(pid)
        if not player:
            bot.reply_to(message, "Сначала выбери сторону: /start")
            return

        now = time.time()

        # Штрафной кулдаун
        if player.get("penalty_until", 0) > now:
            left = player["penalty_until"] - now
            status = "🔒 Ты задержан" if player["side"] == "bandit" else "🏥 Ты на больничном"
            bot.reply_to(message,
                f"{status}! Выйдешь через <b>{format_time(left)}</b>.",
                parse_mode="HTML")
            return

        # Уже на задании
        if player["working_until"] > now:
            left = player["working_until"] - now
            bot.reply_to(message,
                f"⏳ Ты ещё не закончил предыдущее задание.\n"
                f"Осталось: <b>{format_time(left)}</b>",
                parse_mode="HTML")
            return

        # Выбор района
        district = random.choice(list(DISTRICTS.keys()))
        district_desc = DISTRICTS[district]

        player["working_until"] = now + WORK_DURATION
        player["district"] = district
        player["chat_id"] = chat_id
        save_data(data)

        # Проверка противников в этом районе
        enemies_exist = any(
            opid != pid and p["side"] != player["side"]
            and p.get("district") == district
            and p.get("working_until", 0) > now
            for opid, p in data.items()
        )

        if enemies_exist:
            triggered_district = district

    # Сообщение об отправке
    emoji = "👮" if player["side"] == "cop" else "🔫"
    task = "задание" if player["side"] == "cop" else "мокруху"
    bot.reply_to(message,
        f"{emoji} Ты отправился на {task}.\n"
        f"📍 Район: <b>«{district}»</b>\n"
        f"<i>{district_desc}</i>\n"
        f"⏱ Вернёшься через 1 час.",
        parse_mode="HTML")

    # Если в районе есть враги — планируем групповую стычку
    if triggered_district:
        with fight_lock:
            if triggered_district not in scheduled_fights:
                scheduled_fights[triggered_district] = True
                # Анонс
                bot.send_message(chat_id,
                    f"🚨 В районе <b>«{triggered_district}»</b> намечается разборка!\n"
                    f"⏳ Сбор участников... ({FIGHT_DELAY} сек)",
                    parse_mode="HTML")
                threading.Timer(FIGHT_DELAY, resolve_group_fight,
                                args=(triggered_district, chat_id)).start()
    else:
        # Одиночная миссия
        threading.Timer(WORK_DURATION, finish_mission, args=(pid,)).start()


# ===================== ГРУППОВАЯ СТЫЧКА =====================
def resolve_group_fight(district, chat_id):
    with fight_lock:
        scheduled_fights.pop(district, None)

    with data_lock:
        data = load_data()
        now = time.time()

        # Собираем участников, находящихся в этом районе прямо сейчас
        cops = []
        bandits = []
        for pid, p in data.items():
            if p.get("district") != district:
                continue
            if p.get("working_until", 0) <= now:
                continue
            if p["side"] == "cop":
                cops.append(pid)
            else:
                bandits.append(pid)

        # Если в каком-то лагере никого — стычки нет
        if not cops or not bandits:
            return

        # Расчёт силы фракций (RandomFactor один на фракцию)
        cop_random = random.randint(-10, 10)
        bandit_random = random.randint(-10, 10)

        cop_power = 0
        cop_info = []  # (pid, name, rank, exp, individual_power)
        for pid in cops:
            p = data[pid]
            rank_name, rb = get_rank_info("cop", p["exp"])
            ip = p["exp"] + rb * 10
            cop_power += ip
            cop_info.append((pid, p["name"], rank_name, p["exp"], ip))
        cop_power += cop_random

        bandit_power = 0
        bandit_info = []
        for pid in bandits:
            p = data[pid]
            rank_name, rb = get_rank_info("bandit", p["exp"])
            ip = p["exp"] + rb * 10
            bandit_power += ip
            bandit_info.append((pid, p["name"], rank_name, p["exp"], ip))
        bandit_power += bandit_random

        power_diff = abs(cop_power - bandit_power)

        # === Ничья ===
        if cop_power == bandit_power:
            for pid in cops + bandits:
                p = data[pid]
                add_exp(p, -5)
                p["working_until"] = 0
                p["district"] = None
            save_data(data)

            lines = [
                f"⚔️ <b>Разборка в районе «{district}»</b>",
                f"{'─' * 25}",
                f"👮 Копы ({len(cops)}): сила <b>{cop_power}</b>",
                f"🔫 Бандиты ({len(bandits)}): сила <b>{bandit_power}</b>",
                "",
                f"🤝 <b>НИЧЬЯ!</b>",
                f"Все участники потеряли по 5 ед. опыта."
            ]
            bot.send_message(chat_id, "\n".join(lines), parse_mode="HTML")
            return

        # === Определяем победителей ===
        if cop_power > bandit_power:
            winners_ids, losers_ids = cops, bandits
            winners_info, losers_info = cop_info, bandit_info
            winner_side = "cop"
        else:
            winners_ids, losers_ids = bandits, cops
            winners_info, losers_info = bandit_info, cop_info
            winner_side = "bandit"

        # Особый исход
        special = power_diff > SPECIAL_POWER_DIFF and random.random() < SPECIAL_CHANCE
        bonus_hero_id = random.choice(winners_ids) if special else None

        # Начисление опыта/штрафов
        exp_reward = 20
        exp_penalty = 15

        # Запоминаем звания ДО, чтобы увидеть повышения
        rank_ups = []  # (name, new_rank)

        for pid in winners_ids:
            p = data[pid]
            old_rank = get_rank(p["side"], p["exp"])
            p["exp"] += exp_reward
            if pid == bonus_hero_id:
                p["exp"] += 10
                p["medals"] = p.get("medals", 0) + 1
            new_rank = get_rank(p["side"], p["exp"])
            if old_rank != new_rank:
                rank_ups.append((p["name"], new_rank))
            p["working_until"] = 0
            p["district"] = None

        for pid in losers_ids:
            p = data[pid]
            add_exp(p, -exp_penalty)
            p["penalty_until"] = now + PENALTY_SHORT
            p["working_until"] = 0
            p["district"] = None

        save_data(data)

    # === Формируем отчёт ===
    if winner_side == "cop":
        w_emoji, l_emoji = "👮", "🔫"
        w_word, l_word = "Копы", "Бандиты"
        special_title = "🚔 УСПЕШНАЯ ОПЕРАЦИЯ!"
        loser_status = "Задержаны 🔒"
    else:
        w_emoji, l_emoji = "🔫", "👮"
        w_word, l_word = "Бандиты", "Копы"
        special_title = "💀 ПЕРЕСТРЕЛКА!"
        loser_status = "Ранены 🏥"

    lines = [
        f"⚔️ <b>Разборка в районе «{district}»</b>",
        f"{'─' * 25}",
        f"",
        f"👮 <b>Копы</b> ({len(cop_info)}):"
    ]
    for _, name, rank, exp, ip in cop_info:
        lines.append(f"   • {name} ({rank}, {exp} опыта)")
    lines.append(f"   ⚡ Общая сила: <b>{cop_power}</b>")
    lines.append("")
    lines.append(f"🔫 <b>Бандиты</b> ({len(bandit_info)}):")
    for _, name, rank, exp, ip in bandit_info:
        lines.append(f"   • {name} ({rank}, {exp} опыта)")
    lines.append(f"   ⚡ Общая сила: <b>{bandit_power}</b>")
    lines.append("")
    lines.append(f"🏆 <b>Победили: {w_word}!</b> {w_emoji}")
    lines.append(f"📈 Каждый победитель: <b>+{exp_reward}</b> опыта")
    lines.append(f"📉 Каждый проигравший: <b>-{exp_penalty}</b> опыта + штраф 30 мин ({loser_status})")

    if special and bonus_hero_id:
        with data_lock:
            data = load_data()
            hero_name = data[bonus_hero_id]["name"]
        lines.append("")
        lines.append(special_title)
        lines.append(f"🎖 <b>{hero_name}</b> отличился и получает дополнительно "
                     f"<b>+10</b> опыта и медаль!")

    if rank_ups:
        lines.append("")
        lines.append("🎖 <b>Повышения:</b>")
        for name, new_rank in rank_ups:
            lines.append(f"   • {name} → <b>{new_rank}</b>")

    bot.send_message(chat_id, "\n".join(lines), parse_mode="HTML")


# ===================== Завершение одиночной миссии =====================
def finish_mission(pid):
    with data_lock:
        data = load_data()
        player = data.get(pid)
        if not player:
            return
        if player["working_until"] == 0:
            return
        if player["working_until"] > time.time() + 5:
            return

        now = time.time()
        district = player["district"]

        # Проверка на врагов в последний момент
        for opid, p in data.items():
            if opid == pid: continue
            if (p["side"] != player["side"] and p.get("district") == district
                    and p.get("working_until", 0) > now):
                with fight_lock:
                    if district not in scheduled_fights:
                        scheduled_fights[district] = True
                        threading.Timer(2, resolve_group_fight,
                                        args=(district, player["chat_id"])).start()
                return

        # === Бросок кубика: 65% успех / 35% провал ===
        success = random.random() < 0.65

        old_rank = get_rank(player["side"], player["exp"])

        if success:
            desc, exp_change = pick_event_by_rank(player["side"], player["exp"])
            add_exp(player, exp_change)
        else:
            # Выбираем провальное задание
            fail_events = COP_FAIL_EVENTS if player["side"] == "cop" else BANDIT_FAIL_EVENTS
            desc, exp_change = random.choice(fail_events)
            add_exp(player, exp_change)  # exp_change отрицательный

        new_rank = get_rank(player["side"], player["exp"])
        chat_id = player["chat_id"]
        player["working_until"] = 0
        player["district"] = None
        save_data(data)

    emoji = "👮" if player["side"] == "cop" else "🔫"
    side_word = "Полицейский" if player["side"] == "cop" else "Бандит"

    if success:
        result_header = "✅ <b>Задание выполнено!</b>"
        reward_line = f"💰 Награда: <b>+{exp_change} опыта</b>"
    else:
        result_header = "❌ <b>Задание провалено!</b>"
        reward_line = f"💸 Потеря: <b>{exp_change} опыта</b>"

    text = (
        f"{result_header}\n"
        f"{'─'*25}\n"
        f"{emoji} <b>{player['name']}</b> | {side_word}\n"
        f"📍 Район: <b>«{district}»</b>\n\n"
        f"📋 <b>Что произошло:</b>\n"
        f"{desc}.\n\n"
        f"{reward_line}\n"
        f"⭐ Всего опыта: <b>{player['exp']}</b>\n"
        f"🎖 Звание: <b>{new_rank}</b>"
    )

    # Повышение звания
    if success and old_rank != new_rank:
        text += f"\n\n🎉 <b>ПОВЫШЕНИЕ!</b> {old_rank} → <b>{new_rank}</b>!"

    # Понижение звания
    if not success and old_rank != new_rank:
        text += f"\n\n📉 <b>ПОНИЖЕНИЕ!</b> {old_rank} → <b>{new_rank}</b>"

    text += "\n\nПиши «работать» чтобы выйти на следующее задание!"

    bot.send_message(chat_id, text, parse_mode="HTML")

# na_raione.py — Часть 4

# ===================== Профиль =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in
                     ["профиль", "/профиль", "/profile"])
def cmd_profile(message):
    pid = str(message.from_user.id)
    with data_lock:
        data = load_data()
        player = data.get(pid)

    if not player:
        bot.reply_to(message, "Ты ещё не в игре. Напиши /start")
        return

    side = player["side"]
    exp = player["exp"]
    rank, rank_bonus = get_rank_info(side, exp)
    next_rank, exp_left = get_next_rank_info(side, exp)
    medals = player.get("medals", 0)
    side_text = "👮 Полицейский" if side == "cop" else "🔫 Бандит"

    # Прогресс-бар
    progress_text = ""
    if next_rank:
        table = COP_RANKS if side == "cop" else BANDIT_RANKS
        cur_t = next_t = 0
        for i, row in enumerate(table):
            if row[1] == rank:
                cur_t = row[0]
                if i + 1 < len(table):
                    next_t = table[i + 1][0]
                break
        if next_t > cur_t:
            progress = (exp - cur_t) / (next_t - cur_t)
            filled = int(progress * 10)
            bar = "█" * filled + "░" * (10 - filled)
            progress_text = (
                f"\n📊 Прогресс: [{bar}] {int(progress*100)}%\n"
                f"⏭ Следующее звание: <b>{next_rank}</b> (ещё {exp_left} опыта)"
            )
    else:
        progress_text = "\n🏆 Максимальное звание достигнуто!"

    # Статус
    now = time.time()
    if player.get("penalty_until", 0) > now:
        left = player["penalty_until"] - now
        status = ("🔒 Задержан" if side == "bandit" else "🏥 На больничном") + \
                 f" ({format_time(left)})"
    elif player["working_until"] > now:
        left = player["working_until"] - now
        status = f"🔄 На задании в «{player['district']}» ({format_time(left)})"
    else:
        status = "💤 Свободен"

    medals_text = f"\n🎖 Медалей: <b>{medals}</b>" if medals else ""

    text = (
        f"📋 <b>ЛИЧНОЕ ДЕЛО</b>\n"
        f"{'─'*25}\n"
        f"👤 Имя: <b>{player['name']}</b>\n"
        f"🏷 Статус: {side_text}\n"
        f"🎖 Звание: <b>{rank}</b>\n"
        f"⭐ Опыт: <b>{exp}</b>"
        f"{medals_text}\n"
        f"📍 Состояние: {status}"
        f"{progress_text}"
    )
    bot.reply_to(message, text, parse_mode="HTML")


# ===================== Топ =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in
                     ["топ", "/топ", "/top"])
def cmd_top(message):
    with data_lock:
        data = load_data()
    if not data:
        bot.reply_to(message, "Пока нет игроков.")
        return
    players = sorted(data.values(), key=lambda p: p["exp"], reverse=True)
    text = "🏆 <b>ТОП ИГРОКОВ «На районе»</b>\n" + "─"*25 + "\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(players[:15]):
        mark = medals[i] if i < 3 else f"{i+1}."
        emoji = "👮" if p["side"] == "cop" else "🔫"
        rank = get_rank(p["side"], p["exp"])
        text += f"{mark} {emoji} <b>{p['name']}</b> — {rank} ({p['exp']} опыта)\n"
    bot.reply_to(message, text, parse_mode="HTML")


# ===================== Помощь =====================
@bot.message_handler(func=lambda m: m.text and m.text.lower().strip() in
                     ["помощь", "/помощь", "/help"])
def cmd_help(message):
    text = (
        "🏙 <b>«На районе» — Помощь</b>\n"
        f"{'─'*25}\n\n"
        "📌 <b>Команды:</b>\n"
        "• <b>работать</b> — выйти на задание (раз в час)\n"
        "• <b>профиль</b> — личное дело\n"
        "• <b>топ</b> — рейтинг игроков\n"
        "• <b>помощь</b> — это сообщение\n\n"
        "📌 <b>Правила:</b>\n"
        "• Выбери сторону: 👮 коп или 🔫 бандит\n"
        "• Пиши «работать» — бот отправит в случайный район на 1 час\n"
        "• Если в одном районе встретятся копы и бандиты — произойдёт разборка!\n"
        "• Сила фракции = сумма опыта + бонусы за звание + удача\n"
        "• Победители получают +20 опыта, проигравшие -15 и штраф 30 мин\n"
        "• При большом преимуществе возможен особый исход: +10 и медаль герою!\n"
    )
    bot.reply_to(message, text, parse_mode="HTML")


# ===================== Запуск =====================
if __name__ == "__main__":
    print("🏙 Бот «На районе» запущен!")
    bot.infinity_polling()

