import asyncio
import random
import sqlite3
import time
import html
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [6564196947]
SHOP_BANK_ID = 6564196947

START_COINS = 1000
DAILY_BONUS = 9000
BMW_BONUS = 2000
BMW_NEW_YEAR_BONUS = 2000

FIELD_SIZE = 25
BOMBS_COUNT = 14

COEF_STEP = 0.08
MAX_COEF = 30.00
MAX_COINS = 1_000_000_000_000

bmwpower_used = set()
bmwpower_new_year_used = set()


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


BLACKLIST = {}

BLOCK_TEXT = (
    "🚫 <b>ДОСТУП ЗАКРЫТ</b>\n\n"
    "Ты внесён в чёрный список.\n"
    "Бот для тебя недоступен.\n\n"
    "📩 По вопросам разблокировки обращайся к администратору."
)


@dp.message(F.from_user.id.in_(BLACKLIST))
async def blacklist_guard(message: Message):
    await message.reply(BLOCK_TEXT, parse_mode="HTML")


@dp.callback_query(F.from_user.id.in_(BLACKLIST))
async def blacklist_guard_callback(call: CallbackQuery):
    await call.answer("🚫 Ты в чёрном списке", show_alert=True)


@dp.message(F.text == "Блок", F.reply_to_message)
async def admin_block_user(message: Message):
    if message.from_user.id not in ADMINS:
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    BLACKLIST[user_id] = username

    await message.reply(
        f"✅ Пользователь {username} (<code>{user_id}</code>) заблокирован",
        parse_mode="HTML"
    )


@dp.message(F.text == "Разблок", F.reply_to_message)
async def admin_unblock_user(message: Message):
    if message.from_user.id not in ADMINS:
        return

    user = message.reply_to_message.from_user
    user_id = user.id
    username = BLACKLIST.pop(user_id, None)

    if username:
        await message.reply(
            f"♻️ Пользователь {username} разблокирован",
            parse_mode="HTML"
        )
    else:
        await message.reply("❌ Этот пользователь не в чёрном списке")


@dp.message(F.text == "Список блок")
async def admin_blacklist(message: Message):
    if message.from_user.id not in ADMINS:
        return

    if not BLACKLIST:
        await message.reply("📭 Чёрный список пуст")
    else:
        text = "🚫 <b>ЧЁРНЫЙ СПИСОК:</b>\n\n"
        for uid, uname in BLACKLIST.items():
            text += f"{uname} (<code>{uid}</code>)\n"
        await message.reply(text, parse_mode="HTML")


async def coins_transfer_guard(message: Message, target_user_id: int):
    if message.from_user.id in BLACKLIST:
        await message.reply("🚫 Ты в чёрном списке и не можешь переводить коины.")
        return False

    if target_user_id in BLACKLIST:
        await message.reply("🚫 Этому пользователю запрещено получать коины.")
        return False

    return True


SHOP_ITEMS = {
    # ===== ТИТУЛЫ =====
    1: {"name": "👑 Титул «Король» (+1 защита от бомбы)", "price": 400_000, "type": "title", "value": "👑 Король"},
    2: {"name": "⚔️ Титул «Воин» (+1 защита от бомбы)", "price": 700_000, "type": "title", "value": "⚔️ Воин"},
    3: {"name": "💰 Титул «Богатей» (+2 защиты от бомб)", "price": 25_000_000, "type": "title", "value": "💰 Богатей"},
    4: {"name": "⭐️ Титул «Легенда» (+2 защиты от бомб)", "price": 50_000_000, "type": "title", "value": "⭐️Легенда"},
    5: {"name": "☠️ Титул «Босс» (+5 защит от бомб)", "price": 250_000_000, "type": "title", "value": "☠️ Босс"},
    6: {"name": "🎮 Титул «Владелец» (+6 защит от бомб)", "price": 2_000_000_000, "type": "title", "value": "🎮 Владелец"},
    24: {"name": "🎮 Титул  «Рыцарь» ( +7 защит от бомб)", "price": 2_000_000_000, "type": "title", "value": "🎮 Рыцарь"},
    

    # ===== VIP =====
    7: {"name": "⭐ VIP на 7 дней (x1.35 к выигрышу + защита)", "price": 300_000_000, "type": "vip", "value": 7},
    8: {"name": "🔥 VIP на 30 дней (x1.35 к выигрышу + защита)", "price": 1_200_000_000, "type": "vip", "value": 30},
    9: {"name": "💎 VIP на 90 дней (x1.5 к выигрышу + защита)", "price": 3_000_000_000, "type": "vip", "value": 90},

    13: {"name": "🏅 +100 рейтинга", "price": 75_000_000, "type": "rating", "value": 100},
    14: {"name": "🏅 +500 рейтинга", "price": 300_000_000, "type": "rating", "value": 500},

    # ===== КЕЙСЫ =====
    15: {"name": "🎁 Малый кейс", "price": 10_000_000, "type": "case", "value": "small"},
    16: {"name": "🎁 Большой кейс", "price": 50_000_000, "type": "case", "value": "big"},
    17: {"name": "🎁 Легендарный кейс", "price": 250_000_000, "type": "case", "value": "legend"},
    18: {"name": "🎁 GOD кейс", "price": 1_000_000_000, "type": "case", "value": "god"},

    # ===== COINS =====
    19: {"name": "💰 +10.000.000 Coins", "price": 9_500_000, "type": "coins", "value": 10_000_000},
    20: {"name": "💰 +50.000.000 Coins", "price": 45_000_000, "type": "coins", "value": 50_000_000},
    21: {"name": "💰 +250.000.000 Coins", "price": 220_000_000, "type": "coins", "value": 250_000_000},

    # ===== ЭКСКЛЮЗИВ =====
    22: {"name": "👹 Титул «Император» (+8 защит от бомб)", "price": 10_000_000_000, "type": "title", "value": "👹 Император"},
    23: {"name": "👽 Титул «Бог Игры» (+10 защит от бомб)", "price": 50_000_000_000, "type": "title", "value": "👽 Бог Игры"},
}


def escape_html_safe(text: str) -> str:
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")


    allowed = ["b", "i", "u", "s", "code", "pre"]
    for tag in allowed:
        text = text.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        text = text.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

    return text


_original_send_message = bot.send_message
_original_answer = Message.answer
_original_reply = Message.reply


async def safe_send_message(chat_id, text, *args, **kwargs):
    if kwargs.get("parse_mode") == "HTML":
        text = escape_html_safe(text)
    return await _original_send_message(chat_id, text, *args, **kwargs)


async def safe_answer(self, text, *args, **kwargs):
    if kwargs.get("parse_mode") == "HTML":
        text = escape_html_safe(text)
    return await _original_answer(self, text, *args, **kwargs)


async def safe_reply(self, text, *args, **kwargs):
    if kwargs.get("parse_mode") == "HTML":
        text = escape_html_safe(text)
    return await _original_reply(self, text, *args, **kwargs)



bot.send_message = safe_send_message
Message.answer = safe_answer
Message.reply = safe_reply

def update_coins(tg_id, amount):
    users_sql.execute("SELECT coins FROM users WHERE tg_id=?", (tg_id,))
    row = users_sql.fetchone()
    if not row:
        return False

    current = row[0]
    new_balance = current + amount

    reached_limit = False
    if new_balance < 0:
        new_balance = 0

    if new_balance > MAX_COINS:
        new_balance = MAX_COINS
        reached_limit = True

    users_sql.execute(
        "UPDATE users SET coins=? WHERE tg_id=?",
        (new_balance, tg_id)
    )
    users_db.commit()
    return reached_limit





users_db = sqlite3.connect("users.db")
users_sql = users_db.cursor()

users_sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER,
    last_bonus INTEGER
)
""")
users_db.commit()



games_db = sqlite3.connect("bot.db")
games_sql = games_db.cursor()

games_sql.execute("""
CREATE TABLE IF NOT EXISTS games (
    tg_id INTEGER,
    chat_id INTEGER,
    bet INTEGER,
    bombs TEXT,
    opened TEXT,
    coef REAL,
    active INTEGER
)
""")


games_db.commit()


users_sql.execute("""
CREATE TABLE IF NOT EXISTS shop_purchases (
    tg_id INTEGER,
    item_id INTEGER,
    buy_time INTEGER
)
""")

users_sql.execute("""
CREATE TABLE IF NOT EXISTS user_titles (
    tg_id INTEGER,
    title TEXT
)
""")

users_sql.execute("""
CREATE TABLE IF NOT EXISTS user_vip (
    tg_id INTEGER,
    vip_until INTEGER
)
""")

users_sql.execute("""
CREATE TABLE IF NOT EXISTS vip_mines_free (
    tg_id INTEGER PRIMARY KEY,
    used INTEGER
)
""")
users_db.commit()


users_sql.execute("""
CREATE TABLE IF NOT EXISTS user_rating (
    tg_id INTEGER PRIMARY KEY,
    rating INTEGER
)
""")
users_db.commit()

users_sql.execute("""
CREATE TABLE IF NOT EXISTS user_insurance (
    tg_id INTEGER PRIMARY KEY,
    count INTEGER
)
""")
users_db.commit()


# ===== RATING SYSTEM =====
def ensure_rating(tg_id):
    users_sql.execute("SELECT rating FROM user_rating WHERE tg_id=?", (tg_id,))
    if not users_sql.fetchone():
        users_sql.execute(
            "INSERT INTO user_rating VALUES (?, ?)",
            (tg_id, 1000)  # стартовый рейтинг
        )
        users_db.commit()


def get_rating(tg_id):
    ensure_rating(tg_id)
    users_sql.execute("SELECT rating FROM user_rating WHERE tg_id=?", (tg_id,))
    return users_sql.fetchone()[0]


def update_rating(tg_id, amount):
    ensure_rating(tg_id)
    users_sql.execute(
        "UPDATE user_rating SET rating = rating + ? WHERE tg_id=?",
        (amount, tg_id)
    )
    users_db.commit()




def vip_can_save(tg_id):
    if not is_vip(tg_id):
        return False

    users_sql.execute("SELECT used FROM vip_mines_free WHERE tg_id=?", (tg_id,))
    row = users_sql.fetchone()

    if not row:
        users_sql.execute(
            "INSERT INTO vip_mines_free VALUES (?,0)",
            (tg_id,)
        )
        users_db.commit()
        return True

    return row[0] == 0


def vip_use_save(tg_id):
    users_sql.execute(
        "UPDATE vip_mines_free SET used=1 WHERE tg_id=?",
        (tg_id,)
    )
    users_db.commit()
    
def get_top_users(limit=10):
    users_sql.execute(
        "SELECT tg_id, username, coins FROM users ORDER BY coins DESC LIMIT ?",
        (limit,)
    )
    return users_sql.fetchall()

def get_top_rating(limit=10):
    users_sql.execute("""
        SELECT u.tg_id, u.username, r.rating
        FROM user_rating r
        JOIN users u ON u.tg_id = r.tg_id
        ORDER BY r.rating DESC
        LIMIT ?
    """, (limit,))
    return users_sql.fetchall()


@dp.message(F.text.lower().in_(["топ", "топ участники", "топ10"]))
async def top_users(message: Message):
    top = get_top_users(10)

    if not top:
        return await message.answer("❌ Топ пока пуст")

    text = "🏆 <b>ТОП 10 УЧАСТНИКОВ ПО COINS</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top, start=1):
        tg_id, username, coins = user
        name = f"@{username}" if username else f"ID:{tg_id}"

        medal = medals[i-1] if i <= 3 else f"{i}."

        text += (
            f"{medal} <b>{name}</b>\n"
            f"💰 {fmt(coins)} Coins\n\n"
        )

    await message.answer(text, parse_mode="HTML")
    
    
@dp.message(F.text.lower().in_(["рейтинг", "мой рейтинг"]))
async def my_rating(message: Message):
    ensure_user(message.from_user)
    rating = get_rating(message.from_user.id)

    await message.answer(
        f"🏅 <b>Твой рейтинг</b>\n\n"
        f"📊 Очки: <b>{rating}</b>",
        parse_mode="HTML"
    )


    
@dp.message(F.text.lower().in_(["топрейтинг", "топ рейтинг", "топ скилл"]))
async def top_rating(message: Message):
    top = get_top_rating(10)

    if not top:
        return await message.answer("❌ Топ пока пуст")

    text = "🏆 <b>ТОП 10 ПО СКИЛЛУ</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top, start=1):
        tg_id, username, rating = user
        name = f"@{username}" if username else f"ID:{tg_id}"
        medal = medals[i-1] if i <= 3 else f"{i}."

        text += (
            f"{medal} <b>{name}</b>\n"
            f"🏅 Рейтинг: <b>{rating}</b>\n\n"
        )

    await message.answer(text, parse_mode="HTML")






# ================= ВСПОМОГАТЕЛЬНО ============
def is_group(message: Message):
    return message.chat.type in ("group", "supergroup")

def fmt(num: int) -> str:
    return f"{num:,}".replace(",", ".")

def ensure_user(user):
    users_sql.execute("SELECT tg_id FROM users WHERE tg_id=?", (user.id,))
    if users_sql.fetchone():
        users_sql.execute(
            "UPDATE users SET username=? WHERE tg_id=?",
            (user.username, user.id)
        )
    else:
        users_sql.execute(
            "INSERT INTO users VALUES (?,?,?,?)",
            (user.id, user.username, START_COINS, 0)
        )
    users_db.commit()


def get_user(tg_id):
    users_sql.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    return users_sql.fetchone()

def get_user_by_username(username):
    users_sql.execute(
        "SELECT * FROM users WHERE username=?",
        (username.replace("@", ""),)
    )
    return users_sql.fetchone()



def get_game(tg_id):
    games_sql.execute(
        "SELECT * FROM games WHERE tg_id=? AND active=1",
        (tg_id,)
    )
    return games_sql.fetchone()

def get_insurance(tg_id):
    users_sql.execute("SELECT count FROM user_insurance WHERE tg_id=?", (tg_id,))
    row = users_sql.fetchone()
    return row[0] if row else 0


def add_insurance(tg_id, amount):
    current = get_insurance(tg_id)
    if current == 0:
        users_sql.execute(
            "INSERT OR REPLACE INTO user_insurance VALUES (?,?)",
            (tg_id, amount)
        )
    else:
        users_sql.execute(
            "UPDATE user_insurance SET count=? WHERE tg_id=?",
            (current + amount, tg_id)
        )
    users_db.commit()


def use_insurance(tg_id):
    current = get_insurance(tg_id)
    if current > 0:
        users_sql.execute(
            "UPDATE user_insurance SET count=? WHERE tg_id=?",
            (current - 1, tg_id)
        )
        users_db.commit()
        return True
    return False



def generate_bombs():
    return random.sample(range(FIELD_SIZE), BOMBS_COUNT)

def mines_keyboard(opened):
    keyboard = []
    for r in range(5):
        row = []
        for c in range(5):
            i = r * 5 + c
            emoji = "✅" if i in opened else "❓"
            row.append(
                InlineKeyboardButton(
                    text=emoji,
                    callback_data=f"cell_{i}"
                )
            )
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="💰 Забрать", callback_data="take"),
        InlineKeyboardButton(text="❌ Выйти", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)   
        

def reveal_result_keyboard(bombs, opened):
    keyboard = []
    for r in range(5):
        row = []
        for c in range(5):
            i = r * 5 + c
            if i in opened:
                emoji = "⬛"
            elif i in bombs:
                emoji = "💣"
            else:
                emoji = "⬜"

            row.append(
                InlineKeyboardButton(
                    text=emoji,
                    callback_data="end"
                )
            )
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    ensure_user(message.from_user)
    await message.reply(
        "🎮 Coins Bot\n\n"
        "• Б — баланс\n"
        "• Мины 200 — игра\n"
        "• СП — перевод Coins\n"
        "• Магазин - открыть магазин",
        parse_mode="HTML"
    )
    
def is_vip(tg_id: int) -> bool:
    users_sql.execute("SELECT vip_until FROM user_vip WHERE tg_id=?", (tg_id,))
    row = users_sql.fetchone()
    if not row:
        return False
    return row[0] > int(time.time())


def get_vip_left(tg_id: int):
    users_sql.execute("SELECT vip_until FROM user_vip WHERE tg_id=?", (tg_id,))
    row = users_sql.fetchone()
    if not row:
        return 0
    left = row[0] - int(time.time())
    return max(0, left // 86400)

    
def get_user_title(tg_id):
    # 🛡 Админ имеет приоритет всегда
    if tg_id in ADMINS:
        return "🛡 Админ"

    users_sql.execute(
        "SELECT title FROM user_titles WHERE tg_id=? ORDER BY ROWID DESC LIMIT 1",
        (tg_id,)
    )
    row = users_sql.fetchone()
    return row[0] if row else "Без титула"


@dp.message(F.text.lower().in_(["б", "баланс"]))
async def balance(message: Message):
    ensure_user(message.from_user)
    data = get_user(message.from_user.id)
    title = get_user_title(message.from_user.id)

    if is_vip(message.from_user.id):
        vip_days = get_vip_left(message.from_user.id)
        vip_status = f"⭐ Активен ({vip_days} дн.)"
    else:
        vip_status = "❌ Нет"

    await message.answer(
        f"👤 {message.from_user.first_name}\n"
        f"🏷 Титул: <b>{title}</b>\n"
        f"⭐ VIP: <b>{vip_status}</b>\n"
        f"💰 Баланс: <b>{fmt(data[2])} Coins</b>",
        parse_mode="HTML"
    )

    

@dp.message(F.text.lower() == "мой профиль")
async def user_profile(message: Message):
    user = message.from_user
    ensure_user(user)

    data = get_user(user.id)
    title = get_user_title(user.id)

    if is_vip(user.id):
        vip_days = get_vip_left(user.id)
        vip_status = f"⭐ Активен ({vip_days} дн.)"
    else:
        vip_status = "❌ Нет"

    await message.answer(
        f"👤 <b>ТВОЙ ПРОФИЛЬ</b>\n\n"
        f"🏷 Титул: <b>{title}</b>\n"
        f"⭐ VIP: <b>{vip_status}</b>\n"
        f"💰 Coins: <b>{fmt(data[2])}</b>",
        parse_mode="HTML"
    )


# ================= PAY ======================
@dp.message(F.text.startswith("СП"))
async def pay(message: Message):

    # если отправитель заблокирован
    if message.from_user.id in BLACKLIST:
        return await message.reply(BLOCK_TEXT, parse_mode="HTML")

    ensure_user(message.from_user)
    sender = get_user(message.from_user.id)
    parts = message.text.split()

    if message.reply_to_message:
        if len(parts) != 2 or not parts[1].isdigit():
            return await message.reply("❌ СП 500 ответом")
        amount = int(parts[1])
        target_user = message.reply_to_message.from_user
        ensure_user(target_user)
        target = get_user(target_user.id)

    elif len(parts) == 3 and parts[1].startswith("@"):
        if not parts[2].isdigit():
            return await message.reply("❌ Пример: СП @user 500")
        amount = int(parts[2])
        target = get_user_by_username(parts[1])
        if not target:
            return await message.reply("❌ Пользователь не найден")
    else:
        return await message.reply("❌ СП @user 500 или ответом")

    # если получатель в чёрном списке
    if target[0] in BLACKLIST:
        return await message.reply(
            "⛔ Этому пользователю запрещены любые операции.\n"
            "Переводы ему недоступны.",
            parse_mode="HTML"
        )

    if amount <= 0:
        return await message.reply("❌ Неверная сумма")

    if sender[0] == target[0]:
        return await message.reply("❌ Нельзя переводить себе")

    if sender[0] not in ADMINS and sender[2] < amount:
        return await message.reply("❌ Недостаточно Coins")

    if sender[0] not in ADMINS:
        update_coins(sender[0], -amount)

    update_coins(target[0], amount)

    sender_user = message.from_user
    receiver_user = message.reply_to_message.from_user if message.reply_to_message else None

    text = (
        f"━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Чек перевода</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👤 Отправитель: {sender_user.full_name}\n"
        f"👥 Получатель: {receiver_user.full_name if receiver_user else target[1]}\n"
        f"💰 Сумма: <b>{fmt(amount)} Coins</b>\n\n"
        f"✔️ Выполнено"
    )

    await message.reply(text, parse_mode="HTML")

    try:
        await bot.send_message(
            target[0],
            f"💸 <b>Вам перевели Coins!</b>\n\n"
            f"👤 Отправитель: @{message.from_user.username}\n"
            f"💰 Сумма: <b>{fmt(amount)} Coins</b>",
            parse_mode="HTML"
        )
    except:
        pass
    
    
@dp.message(F.text.lower().startswith("мины"))
async def start_game(message: Message):
    if not is_group(message):
        return await message.answer("❌ Игра только в группе")

    ensure_user(message.from_user)
    users_sql.execute("""
    INSERT INTO vip_mines_free (tg_id, used)
    VALUES (?, 0)
    ON CONFLICT(tg_id) DO UPDATE SET used=0
    """, (message.from_user.id,))
    users_db.commit()



    if get_game(message.from_user.id):
        return await message.answer("⚠️ Заверши текущую игру")

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("❌ Пример: Мины 500")

    bet = int(parts[1])
    coins = get_user(message.from_user.id)[2]

    if bet <= 0 or coins < bet:
        return await message.answer("❌ Недостаточно Coins")

    update_coins(message.from_user.id, -bet)

    
    bombs = generate_bombs()

    remove_count = get_title_bomb_remove(message.from_user.id)
    for _ in range(remove_count):
        if bombs:
            bombs.pop(random.randrange(len(bombs)))

    if remove_count > 0:
        await message.answer(
            f"🏷 Титул убрал <b>{remove_count}</b> 💣",
            parse_mode="HTML"
        )


    games_sql.execute(
        "INSERT INTO games VALUES (?,?,?,?,?,?,?)",
        (
            message.from_user.id,
            message.chat.id,
            bet,
            ",".join(map(str, bombs)),  
            "",
            1.0,
            1
        )
    )
    games_db.commit()

    await message.reply(
        f"💣 Минное поле\n💰 Ставка: {fmt(bet)} Coins",
        reply_markup=mines_keyboard([]),
        parse_mode="HTML"
    )

        
def get_title_bomb_remove(tg_id):
    if tg_id in ADMINS:
        return 8

    title = get_user_title(tg_id).strip()

    bomb_remove = {
        "👑 Король": 1,
        "⚔️ Воин": 1,
        "💰 Богатей": 2,
        "⭐️Легенда": 2,
        "☠️ Босс": 5,
        "🎮 Владелец": 6,
        "🎮 Рыцарь": 7,
        "👹 Император": 8,
        "👽 Бог Игры": 10,
    }

    return bomb_remove.get(title, 0)




@dp.callback_query(F.data.startswith("cell_"))
async def open_cell(call: CallbackQuery):
    game = get_game(call.from_user.id)
    if not game:
        return

    index = int(call.data.split("_")[1])
    bombs = list(map(int, game[3].split(",")))
    opened = list(map(int, game[4].split(","))) if game[4] else []
    coef = game[5]

    if index in opened:
        return


    if index in bombs:


        if vip_can_save(call.from_user.id):
            vip_use_save(call.from_user.id)
            bombs.remove(index)

            games_sql.execute(
                "UPDATE games SET bombs=? WHERE tg_id=?",
                (",".join(map(str, bombs)), call.from_user.id)
            )
            games_db.commit()

            return await call.message.answer(
                "⭐ <b>VIP защита!</b>\n"
                "💣 Бомба удалена. Игра продолжается.",
                parse_mode="HTML"
            )


        update_rating(call.from_user.id, -25)

        games_sql.execute(
            "UPDATE games SET active=0 WHERE tg_id=?",
            (call.from_user.id,)
        )
        games_db.commit()

        return await call.message.edit_text(
            "💥 <b>БОМБА! Вы проиграли</b>",
            reply_markup=reveal_result_keyboard(bombs, opened),
            parse_mode="HTML"
        )


    opened.append(index)
    coef = min(coef + COEF_STEP, MAX_COEF)

    games_sql.execute(
        "UPDATE games SET opened=?, coef=? WHERE tg_id=?",
        (",".join(map(str, opened)), coef, call.from_user.id)
    )
    games_db.commit()

    win = int(game[2] * coef)

    if call.from_user.id in ADMINS:
        win *= 2
    elif is_vip(call.from_user.id):
        win = int(win * 1.00)

    text = (
        f"💣 Минное поле\n"
        f"📈 x{coef:.2f}\n"
        f"🏆 {fmt(win)} Coins"
    )

    await call.message.edit_text(
        text,
        reply_markup=mines_keyboard(opened),
        parse_mode="HTML"
    )
    
@dp.callback_query(F.data == "take")
async def take(call: CallbackQuery):
    game = get_game(call.from_user.id)
    

    if not game:
        return await call.answer(
            "❌ Это не твоя игра",
            show_alert=True
        )

    win = int(game[2] * game[5])

    admin_bonus = False
    if call.from_user.id in ADMINS:
        win *= 2
        admin_bonus = True
    elif is_vip(call.from_user.id):
        win = int(win * 1.35)

    reached_limit = update_coins(call.from_user.id, win)
    update_rating(call.from_user.id, +20)

    games_sql.execute(
        "UPDATE games SET active=0 WHERE tg_id=?",
        (call.from_user.id,)
    )
    games_db.commit()

    text = f"🏆 <b>Вы забрали {fmt(win)} Coins</b>"
    if admin_bonus:
        text += "\n🛡 Админ-бонус: x2"

    await call.message.edit_text(
        text,
        reply_markup=reveal_result_keyboard(
            list(map(int, game[3].split(","))),
            list(map(int, game[4].split(","))) if game[4] else []
        ),
        parse_mode="HTML"
    )


    if reached_limit:
        await call.message.reply(
            "⚠️ Ты достиг максимального лимита Coins.\n"
            "Дальше деньги не начисляются, пока ты не потратишь часть баланса.",
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):
    game = get_game(call.from_user.id)

    # если кнопку нажал не игрок
    if not game:
        return await call.answer(
            "❌ Это не твоя игра",
            show_alert=True
        )

    games_sql.execute(
        "UPDATE games SET active=0 WHERE tg_id=?",
        (call.from_user.id,)
    )
    games_db.commit()

    await call.message.edit_text("❌ Игра завершена")

# ================= ADMIN ====================

def admin_only(message: Message):
    return message.from_user.id in ADMINS


# 🔍 Профиль игрока
@dp.message(F.text.lower() == "профиль")
async def admin_profile(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя")

    user = message.reply_to_message.from_user
    ensure_user(user)
    
    if is_vip(user.id):
        vip_days = get_vip_left(user.id)
        vip_status = f"⭐ Активен ({vip_days} дн.)"
    else:
        vip_status = "❌ Нет"


    data = get_user(user.id)
    title = get_user_title(user.id)  # ВОТ ЭТОГО НЕ ХВАТАЛО

    await message.answer(
        f"👤 <b>Профиль игрока</b>\n\n"
        f"🏷 Титул: <b>{title}</b>\n"
        f"🆔 ID: <code>{data[0]}</code>\n"
        f"⭐ VIP: <b>{vip_status}</b>\n"
        f"👤 Username: @{data[1]}\n"
        f"💰 Coins: <b>{fmt(data[2])}</b>",
        parse_mode="HTML"
    )


# ➕ Добавить Coins
@dp.message(F.text.startswith("Добавить"))
async def addcoins(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Используй команду ответом\nПример: Добавить 1000")

    try:
        amount = int(message.text.split()[1])
    except:
        return await message.answer("❌ Укажи сумму")

    target = message.reply_to_message.from_user
    ensure_user(target)
    update_coins(target.id, amount)

    await message.answer(
        f"✅ <b>{target.first_name}</b> получил <b>{fmt(amount)} Coins</b>",
        parse_mode="HTML"
    )


# ➖ Снять Coins (с защитой от минуса)
@dp.message(F.text.startswith("Снять"))
async def removecoins(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Используй команду ответом\nПример: Снять 500")

    try:
        amount = int(message.text.split()[1])
    except:
        return await message.answer("❌ Укажи сумму")

    target = message.reply_to_message.from_user
    ensure_user(target)

    current = get_user(target.id)[2]
    if current - amount < 0:
        return await message.answer("❌ Баланс не может быть отрицательным")

    update_coins(target.id, -amount)

    await message.answer(
        f"➖ У <b>{target.first_name}</b> списано <b>{fmt(amount)} Coins</b>",
        parse_mode="HTML"
    )


# ⚙ Установить точный баланс
@dp.message(F.text.startswith("Баланс"))
async def admin_set_balance(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя\nПример: Баланс 100000")

    try:
        amount = int(message.text.split()[1])
    except:
        return await message.answer("❌ Пример: Баланс 100000")

    user = message.reply_to_message.from_user
    ensure_user(user)

    users_sql.execute(
        "UPDATE users SET coins=? WHERE tg_id=?",
        (amount, user.id)
    )
    users_db.commit()

    await message.answer(
        f"⚙ Баланс <b>{user.first_name}</b> установлен: <b>{fmt(amount)} Coins</b>",
        parse_mode="HTML"
    )


# 🗑 Обнулить баланс
@dp.message(F.text.lower() == "обнулить")
async def admin_reset_balance(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя")

    user = message.reply_to_message.from_user
    ensure_user(user)

    users_sql.execute(
        "UPDATE users SET coins=0 WHERE tg_id=?",
        (user.id,)
    )
    users_db.commit()

    await message.answer(
        f"🗑 Баланс <b>{user.first_name}</b> обнулён",
        parse_mode="HTML"
    )


# ♻ Сброс активной игры
@dp.message(F.text.lower() == "сброс")
async def admin_reset_game(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя")

    user = message.reply_to_message.from_user

    games_sql.execute(
        "UPDATE games SET active=0 WHERE tg_id=?",
        (user.id,)
    )
    games_db.commit()

    await message.answer(
        f"♻ Игра пользователя <b>{user.first_name}</b> была сброшена",
        parse_mode="HTML"
    )
    
@dp.message(F.text.lower().startswith("дать титул"))
async def admin_give_title(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя")

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("❌ Пример: Дать титул Король")

    title = parts[2]

    user = message.reply_to_message.from_user
    ensure_user(user)

    users_sql.execute(
        "INSERT INTO user_titles VALUES (?,?)",
        (user.id, title)
    )
    users_db.commit()

    await message.answer(
        f"🏷 Пользователю <b>{user.first_name}</b> выдан титул: <b>{title}</b>",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            user.id,
            f"🏷 Тебе выдали титул: <b>{title}</b>",
            parse_mode="HTML"
        )
    except:
        pass

@dp.message(F.text.lower() == "снять титул")
async def admin_remove_title(message: Message):
    if not admin_only(message):
        return

    if not message.reply_to_message:
        return await message.answer("❌ Ответь на сообщение пользователя")

    user = message.reply_to_message.from_user
    ensure_user(user)

    users_sql.execute(
        "DELETE FROM user_titles WHERE tg_id=?",
        (user.id,)
    )
    users_db.commit()

    await message.answer(
        f"❌ У пользователя <b>{user.first_name}</b> удалён титул",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            user.id,
            "❌ Твой титул был снят администратором",
            parse_mode="HTML"
        )
    except:
        pass
    
@dp.message(F.text.lower().startswith("рейтинг"))
async def admin_change_rating(message: Message):
    if message.from_user.id not in ADMINS:
        return

    if not message.reply_to_message:
        return await message.answer("❌ Используй ответом на сообщение игрока\nПример: Рейтинг +50")

    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("❌ Пример: Рейтинг +50 или Рейтинг -25")

    value = parts[1]

    if not (value.startswith("+") or value.startswith("-")):
        return await message.answer("❌ Используй + или -\nПример: Рейтинг +50")

    try:
        amount = int(value)
    except:
        return await message.answer("❌ Неверное число")

    target = message.reply_to_message.from_user
    ensure_user(target)
    ensure_rating(target.id)

    update_rating(target.id, amount)
    new_rating = get_rating(target.id)

    sign = "повышен" if amount > 0 else "понижен"

    await message.answer(
        f"🏅 Рейтинг игрока <b>{target.first_name}</b> {sign}\n"
        f"Изменение: <b>{amount}</b>\n"
        f"Текущий рейтинг: <b>{new_rating}</b>",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            target.id,
            f"🏅 Твой рейтинг был изменён администратором\n"
            f"Изменение: <b>{amount}</b>\n"
            f"Теперь у тебя: <b>{new_rating}</b>",
            parse_mode="HTML"
        )
    except:
        pass




@dp.message(F.text == "BMWPOWER")
async def bonus_bmwpower(message: Message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if user_id in bmwpower_used:
        return await message.answer("❌ Промокод BMWPOWER уже был активирован")

    bmwpower_used.add(user_id)
    update_coins(user_id, BMW_BONUS)

    await message.answer(
        f"🎁 Вы получили <b>{fmt(BMW_BONUS)} Coins</b> за BMWPOWER",
        parse_mode="HTML"
    )


@dp.message(F.text == "BMWPOWER_NEW_YEAR")
async def bonus_new_year(message: Message):
    ensure_user(message.from_user)
    user_id = message.from_user.id

    if user_id in bmwpower_new_year_used:
        return await message.answer("❌ Промокод BMWPOWER_NEW_YEAR уже был активирован")

    bmwpower_new_year_used.add(user_id)
    update_coins(user_id, BMW_NEW_YEAR_BONUS)

    await message.answer(
        f"🎁 Вы получили <b>{fmt(BMW_NEW_YEAR_BONUS)} Coins</b> за BMWPOWER_NEW_YEAR",
        parse_mode="HTML"
    )
    
def is_private(message: Message):
    return message.chat.type == "private"


@dp.message(F.text.lower().startswith("магазин"))
async def shop(message: Message):
    if not is_private(message):
        return await message.answer("❌ Магазин доступен только в личных сообщениях с ботом")

    text = "🛒 <b>МАГАЗИН</b>\n\n"
    for i, item in SHOP_ITEMS.items():
        text += f"{i}. {item['name']} — <b>{fmt(item['price'])} Coins</b>\n"

    text += "\n🧾 Покупка: <b>Купить номер</b>\nПример: <code>Купить 18</code>"
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.lower().startswith("купить"))
async def buy_item(message: Message):
    if not is_private(message):
        return await message.answer("❌ Покупки доступны только в личных сообщениях с ботом")

    ensure_user(message.from_user)

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("❌ Пример: <code>Купить 3</code>", parse_mode="HTML")

    item_id = int(parts[1])
    if item_id not in SHOP_ITEMS:
        return await message.answer("❌ Такого товара нет")

    item = SHOP_ITEMS[item_id]
    user = get_user(message.from_user.id)

    if user[2] < item["price"]:
        return await message.answer("❌ Недостаточно Coins")

    # 💸 СПИСАНИЕ COINS У ПОКУПАТЕЛЯ
    update_coins(message.from_user.id, -item["price"])

    # 💰 ЗАЧИСЛЕНИЕ COINS В БАНК МАГАЗИНА
    update_coins(SHOP_BANK_ID, item["price"])

    # 🎁 ВЫДАЧА НАГРАДЫ
    if item["type"] == "title":
        users_sql.execute(
            "INSERT INTO user_titles VALUES (?,?)",
            (message.from_user.id, item["value"])
        )
        users_db.commit()
        await message.answer(
            f"👑 Ты получил титул: <b>{item['value']}</b>",
            parse_mode="HTML"
        )

    elif item["type"] == "vip":
        days = item["value"]
        now = int(time.time())

        users_sql.execute(
            "SELECT vip_until FROM user_vip WHERE tg_id=?",
            (message.from_user.id,)
        )
        row = users_sql.fetchone()

        if row:
            vip_until = max(row[0], now) + days * 86400
            users_sql.execute(
                "UPDATE user_vip SET vip_until=? WHERE tg_id=?",
                (vip_until, message.from_user.id)
            )
        else:
            vip_until = now + days * 86400
            users_sql.execute(
                "INSERT INTO user_vip VALUES (?,?)",
                (message.from_user.id, vip_until)
            )

        users_db.commit()
        await message.answer(
            f"⭐ VIP активирован на {days} дней",
            parse_mode="HTML"
        )

    elif item["type"] == "coins":
        amount = item["value"]
        update_coins(message.from_user.id, amount)
        await message.answer(
            f"💰 Ты получил <b>{fmt(amount)} Coins</b>",
            parse_mode="HTML"
        )

    elif item["type"] == "case":
        await open_case(message, item["value"])

    else:
        await message.answer("🛒 Покупка успешно выполнена", parse_mode="HTML")

    # 🧾 ЗАПИСЬ ПОКУПКИ В БАЗУ
    users_sql.execute(
        "INSERT INTO shop_purchases VALUES (?,?,?)",
        (message.from_user.id, item_id, int(time.time()))
    )
    users_db.commit()

    # 📢 УВЕДОМЛЕНИЕ ТОЛЬКО SHOP_BANK_ID
    buyer = message.from_user
    notify_text = (
        f"🏦 <b>Поступление в банк магазина</b>\n\n"
        f"👤 Покупатель: {buyer.full_name}\n"
        f"🆔 ID: <code>{buyer.id}</code>\n"
        f"📦 Товар: <b>{item['name']}</b>\n"
        f"💰 Сумма: <b>{fmt(item['price'])} Coins</b>"
    )

    try:
        await bot.send_message(SHOP_BANK_ID, notify_text, parse_mode="HTML")
    except:
        pass



async def open_case(message, case_type):
    # Экономика под миллионы
    if case_type == "small":
        rewards = [
            (2_000_000, 50),     # 2M
            (5_000_000, 35),     # 5M
            (10_000_000, 15),    # 10M
        ]

    elif case_type == "big":
        rewards = [
            (50_000_000, 50),     # 5M
            (80_000_000, 35),    # 10M
            (120_000_000, 15),    # 20M
        ]

    elif case_type == "legend":
        rewards = [
            (39_000_000, 40),    # 10M
            (50_000_000, 35),    # 25M
            (200_000_000, 25),    # 50M
        ]

    elif case_type == "god":
        rewards = [
            (90_000_000, 40),    # 25M
            (125_000_000, 35),    # 75M
            (150_000_000, 20),   # 150M
            (300_000_000, 5),    # 300M ультра-дроп
        ]

    else:
        return await message.answer("❌ Неизвестный тип кейса")

    pool = []
    for coins, chance in rewards:
        pool.extend([coins] * chance)

    # VIP реально чувствуется
    if is_vip(message.from_user.id):
        pool.extend(pool)  # x2 шанс на дорогие награды

    win = random.choice(pool)
    update_coins(message.from_user.id, win)

    await message.answer(
        f"🎁 Ты открыл кейс!\n"
        f"🏆 Выпало: <b>{fmt(win)} Coins</b>",
        parse_mode="HTML"
    )


# ================= ЗАПУСК =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())


