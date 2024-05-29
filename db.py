import datetime
import random
import sqlite3

KARMA_TIMEOUT = 5
# Время, через которое можно будет снова учавствовать в играх (в часах)
GAME_TIMEOUT = 24
BOT_USERNAME = ''

conn = sqlite3.connect('database.db')
cursor = conn.cursor()


async def create_tables():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    subscribe_until TEXT,
    karma INTEGER,
    last_karma TEXT DEFAULT '',
    banned INTEGER DEFAULT 0,
    ban_until TEXT DEFAULT '',
    referrer_id INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0, 
    vip TEXT DEFAULT '',
    spins INTEGER DEFAULT 0,
    anonim INTEGER DEFAULT 0, 
    game_timeout DATE DEFAULT NULL)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages(
    user_id INTEGER,
    username TEXT,
    date TEXT, 
    count INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games(
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_name TEXT,
    users_count INTEGER,
    winners_count INTEGER,
    active INTEGER DEFAULT 0,
    start_date TEXT,
    end_date TEXT)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_messages(
    game_id INTEGER,
    message_id INTEGER, 
    chat_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_users(
    game_id INTEGER,
    user_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_prizes(
    prize_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prize_text TEXT,
    game_id INTEGER,
    prize_count INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_winners(
    user_id INTEGER,
    prize_id INTEGER, 
    game_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS addresses(
    address_id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT,
    user_id INTEGER,
    active INTEGER DEFAULT 0)
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_loto(
    loto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT,
    end_date TEXT,
    active INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_loto(
    loto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT,
    end_date TEXT,
    active INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weekly_loto(
    loto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT,
    end_date TEXT,
    active INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_users(
    loto_id INTEGER,
    user_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_users(
    loto_id INTEGER,
    user_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weekly_users(
    loto_id INTEGER,
    user_id INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moment_loto(
    loto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    value INTEGER,
    result INTEGER DEFAULT 0,
    date TEXT, 
    start_value INTEGER)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sends(
    send_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    media TEXT,
    type TEXT,
    start_time TEXT DEFAULT '',
    end_time TEXT DEFAULT '')
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS send_buttons(
    button_id INTEGER PRIMARY KEY AUTOINCREMENT,
    send_id INTEGER,
    text TEXT,
    url TEXT)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scheduled_sends(
    send_id INTEGER,
    target TEXT,
    type TEXT,
    time TEXT,
    sched_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start DATE, 
    active INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats(
    chat_id INTEGER PRIMARY KEY,
    chat_name TEXT)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users_messages(
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    sender_id INTEGER,
    date DATE,
    text TEXT, 
    read INTEGER DEFAULT 0)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donates(
    donate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    value INTEGER,
    date DATE)
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings(
    time_limit INTEGER DEFAULT 0.5,
    antispam INTEGER DEFAULT 1,
    request INTEGER DEFAULT 1, 
    goodbye INTEGER DEFAULT 1)
    ''')
    conn.commit()
async def set_game_timeout(user_id):
    cursor.execute('UPDATE users SET game_timeout = ? WHERE user_id = ?',
                   (datetime.datetime.now() + datetime.timedelta(hours=GAME_TIMEOUT), user_id))
    conn.commit()
async def get_game_timeout(user_id) -> bool:
    timeout = cursor.execute('SELECT game_timeout FROM users WHERE user_id = ?', (user_id, )).fetchone()[0]
    if timeout:
        return datetime.datetime.fromisoformat(timeout) > datetime.datetime.now()
    return False

async def set_send_start_time(send_id, start_time):
    cursor.execute('UPDATE sends SET start_time = ? WHERE send_id = ?', (start_time, send_id))
    conn.commit()
async def set_send_end_time(send_id, end_time):
    cursor.execute('UPDATE sends SET end_time = ? WHERE send_id = ?', (end_time, send_id))
    conn.commit()
async def get_goodbye():
    return cursor.execute('SELECT goodbye FROM settings').fetchone()
async def edit_goodbye(value):
    cursor.execute('UPDATE settings SET goodbye = ?', (value, ))
    conn.commit()
async def edit_time_limit(time_limit):
    cursor.execute('UPDATE settings SET time_limit = ?', (time_limit, ))
async def get_settings():
    return cursor.execute('SELECT * FROM settings').fetchone()
async def edit_antispam(value):
    cursor.execute('UPDATE settings SET antispam = ?', (value, ))
    conn.commit()
async def get_time_limit():
    return cursor.execute('SELECT time_limit FROM settings').fetchone()
async def get_antispam():
    return cursor.execute('SELECT antispam FROM settings').fetchone()
async def get_request() -> list:
    return cursor.execute('SELECT request FROM settings').fetchone()
async def edit_request(value):
    cursor.execute('UPDATE settings SET request = ?', (value, ))
    conn.commit()
async def set_settings():
    cursor.execute('INSERT INTO settings(time_limit, antispam, request, goodbye) VALUES(?, ?, ?, ?)',
                   (0.5, 1, 1, 1))
    conn.commit()
async def add_donate(user_id, value):
    cursor.execute('INSERT INTO donates(user_id, value, date) VALUES(?, ?, ?)',
                   (user_id, value, datetime.datetime.now().date()))
    conn.commit()
async def get_donates():
    return cursor.execute('SELECT * FROM donates').fetchall()
async def get_unread_messages_from_user(user_id):
    return cursor.execute(
        'SELECT DISTINCT sender_id FROM users_messages WHERE user_id = ? AND read = 0',
        (user_id, )).fetchall()
async def get_messages_from_user(user_id):
    return cursor.execute('SELECT count(*), sender_id FROM users_messages WHERE user_id = ? GROUP BY sender_id LIMIT 19',
                          (user_id, )).fetchall()
async def get_messages_from_sender(user_id, sender_id):
    return cursor.execute('SELECT * FROM users_messages WHERE user_id = ? AND sender_id = ?',
                          (user_id, sender_id)).fetchall()
async def get_unread_messages_from_sender(user_id, sender_id):
    return cursor.execute('SELECT * FROM users_messages WHERE user_id = ? AND sender_id = ? AND read = 0',
                          (user_id, sender_id)).fetchall()
async def get_unread_messages_count_from_sender(user_id, sender_id):
    return cursor.execute('SELECT COUNT(*) FROM users_messages WHERE user_id = ? AND sender_id = ? AND read = 0 ORDER BY message_id DESC LIMIT 19',
                          (user_id, sender_id)).fetchone()[0]
async def get_unread_messages_count(user_id):
    return cursor.execute('SELECT COUNT(*) FROM users_messages WHERE user_id = ? AND read = 0',
                          (user_id, )).fetchone()[0]
async def get_message(message_id):
    return cursor.execute('SELECT * FROM users_messages WHERE message_id = ?',
                          (message_id, )).fetchone()
async def delete_message(message_id):
    cursor.execute('DELETE FROM users_messages WHERE message_id = ?', (message_id, ))
    conn.commit()
async def add_message_from_user(user_id, sender_id, text):
    cursor.execute('INSERT INTO users_messages(user_id, sender_id, date, text) VALUES(?, ?, ?, ?)',
                   (user_id, sender_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text))
    conn.commit()
    return cursor.execute('SELECT * FROM users_messages WHERE user_id = ? AND sender_id = ? AND text = ?',
                          (user_id, sender_id, text)).fetchone()
async def read_message(message_id):
    cursor.execute('UPDATE users_messages SET read = 1 WHERE message_id = ?', (message_id, ))
    conn.commit()
async def unread_message(message_id):
    cursor.execute('UPDATE users_messages SET read = 0 WHERE message_id = ?', (message_id, ))
    conn.commit()
async def deactivate_sends():
    cursor.execute('UPDATE scheduled_sends SET active = 0')
    conn.commit()
async def get_users_vip():
    return cursor.execute('SELECT * FROM users WHERE vip != ""').fetchall()
async def get_users_novip():
    return cursor.execute('SELECT * FROM users WHERE vip = ""').fetchall()
async def add_scheduled_send(send_id, target, type, time):
    cursor.execute('INSERT INTO scheduled_sends(send_id, target, type, time, start, active) VALUES(?, ?, ?, ?, ?, ?)',
                   (send_id, target, type, time, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1, ))
    conn.commit()
    return cursor.execute('SELECT * FROM scheduled_sends WHERE send_id = ? AND target = ? AND type = ? AND time = ?',
                          (send_id, target, type, time)).fetchone()
async def get_scheduled_send(send_id):
    return cursor.execute('SELECT * FROM scheduled_sends WHERE sched_id = ?', (send_id, )).fetchone()
async def get_scheduled_later():
    return cursor.execute('SELECT * FROM scheduled_sends WHERE type = ?', ('time', )).fetchall()
async def get_scheduled_interval():
    return cursor.execute('SELECT * FROM scheduled_sends WHERE type = "interval"').fetchall()

async def delete_scheduled_send(sched_id):
    cursor.execute('DELETE FROM scheduled_sends WHERE sched_id = ?', (sched_id, ))
    conn.commit()
async def deactivate_scheduled_send(send_id):
    cursor.execute('UPDATE scheduled_sends SET active = 0 WHERE sched_id = ?', (send_id, ))
    conn.commit()
async def activate_scheduled_send(sched_id):
    cursor.execute('UPDATE scheduled_sends SET active = 1 WHERE sched_id = ?', (sched_id, ))
    conn.commit()
async def get_users_no_admin(ADMINS_IDS):
    res = cursor.execute('SELECT * FROM users').fetchall()
    for el in res:
        if el[0] in ADMINS_IDS:
            res.remove(el)
    return res
async def get_chats():
    return cursor.execute('SELECT * FROM chats').fetchall()
async def get_chat(chat_id):
    return cursor.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id, )).fetchone()
async def add_chat(chat_id, chat_name):
    cursor.execute('INSERT INTO chats(chat_id, chat_name) VALUES(?, ?)', (chat_id, chat_name))
    conn.commit()
async def delete_chat(chat_id):
    cursor.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id, ))
    conn.commit()
async def get_sends():
    return cursor.execute('SELECT * FROM sends').fetchall()
async def add_send(text, media, type):
    cursor.execute('INSERT INTO sends(text, media, type) VALUES(?, ?, ?)', (text, media, type))
    conn.commit()
async def get_send(send_id):
    return cursor.execute('SELECT * FROM sends WHERE send_id = ?', (send_id, )).fetchone()
async def get_send_button(button_id):
    return cursor.execute('SELECT * FROM send_buttons WHERE button_id = ?', (button_id, )).fetchone()
async def get_send_buttons(send_id):
    return cursor.execute('SELECT * FROM send_buttons WHERE send_id = ?', (send_id, )).fetchall()
async def add_send_button(send_id, text, url):
    cursor.execute('INSERT INTO send_buttons(send_id, text, url) VALUES(?, ?, ?)', (send_id, text, url))
    conn.commit()
async def delete_button(button_id):
    cursor.execute('DELETE FROM send_buttons WHERE button_id = ?', (button_id, ))
    conn.commit()
async def edit_button_text(button_id, text):
    cursor.execute('UPDATE send_buttons SET text = ? WHERE button_id = ?', (text, button_id))
    conn.commit()
async def edit_button_url(button_id, url):
    cursor.execute('UPDATE send_buttons SET url = ? WHERE button_id = ?', (url, button_id))
    conn.commit()
async def delete_send(send_id):
    cursor.execute('DELETE FROM sends WHERE send_id = ?', (send_id, ))
    conn.commit()
async def edit_send_media(send_id, media, type):
    cursor.execute('UPDATE sends SET media = ?, type = ? WHERE send_id = ?', (media, type, send_id))
    conn.commit()
async def edit_send_text(send_id, text):
    cursor.execute('UPDATE sends SET text = ? WHERE send_id = ?', (text, send_id))
    conn.commit()
async def delete_send_media(send_id):
    cursor.execute('UPDATE sends SET media = ?, type = ? WHERE send_id = ?', ('', 'text', send_id))
    conn.commit()
async def get_all_winners():
    return cursor.execute('SELECT user_id, COUNT(*) as count FROM game_winners GROUP BY user_id ORDER BY count DESC').fetchall()
async def get_winner_prizes(user_id):
    return cursor.execute('SELECT * FROM game_winners WHERE user_id = ?', (user_id, )).fetchall()
async def get_all_prizes():
    return cursor.execute('SELECT * FROM game_prizes').fetchall()
async def update_username_name(user_id, username, first_name):
    cursor.execute('UPDATE users SET username = ?, first_name = ? WHERE user_id = ?', (username, first_name, user_id))
    conn.commit()
async def get_today_messages():
    return cursor.execute('SELECT * FROM messages WHERE date = ? AND username != ? ORDER BY count DESC LIMIT 3', (datetime.datetime.now().date(), BOT_USERNAME)).fetchall()
async def get_week_messages():
    return cursor.execute('SELECT * FROM messages WHERE date > ? AND username != ? ORDER BY count DESC LIMIT 3',
                          (datetime.datetime.now().date() - datetime.timedelta(days=7), BOT_USERNAME)).fetchall()
async def get_month_messages():
    return cursor.execute('SELECT * FROM messages WHERE date > ? AND username != ? ORDER BY count DESC LIMIT 3',
                          (datetime.datetime.now().date() - datetime.timedelta(days=30), BOT_USERNAME)).fetchall()
async def get_usernames():
    return cursor.execute('SELECT username FROM users').fetchall()
async def get_user_anonim(user_id):
    return cursor.execute('SELECT anonim FROM users WHERE user_id = ?', (user_id, )).fetchone()
async def set_user_anonim(user_id, value):
    cursor.execute('UPDATE users SET anonim = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
async def get_daily_moment_loto_by_user_id(user_id):
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE user_id = ? AND date = ?',
                          (user_id, datetime.datetime.now().date())).fetchall()[0]
async def get_monthly_moment_loto_by_user_id(user_id):
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE user_id = ? AND date = ?',
                          (user_id, datetime.datetime.now().date())).fetchall()[0]
async def get_weekly_moment_loto_by_user_id(user_id):
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE user_id = ? AND date = ?',
                          (user_id, datetime.datetime.now().date())).fetchall()[0]
async def get_daily_moment_loto():
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()[0]
async def get_monthly_moment_loto():
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()[0]
async def get_weekly_moment_loto():
    return cursor.execute('SELECT COUNT(*) FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()[0]
async def get_daily_moment_loto_db():
    return cursor.execute('SELECT * FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()
async def get_monthly_moment_loto_db():
    return cursor.execute('SELECT * FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()
async def get_weekly_moment_loto_db():
    return cursor.execute('SELECT * FROM moment_loto WHERE date = ?',
                          (datetime.datetime.now().date(), )).fetchall()
async def add_moment_loto(user_id, value, result, start_value):
    cursor.execute('INSERT INTO moment_loto(user_id, value, result, date, start_value) VALUES(?, ?, ?, ?, ?)',
                   (user_id, value, result, datetime.datetime.now().date(), start_value, ))
    conn.commit()
async def get_moment_loto(user_id):
    return cursor.execute('SELECT * FROM moment_loto WHERE user_id = ?', (user_id, )).fetchall()
async def get_all_moment_loto():
    return cursor.execute('SELECT * FROM moment_loto').fetchall()
async def add_pin(game_id, message_id, chat_id):
    cursor.execute('INSERT INTO game_messages(game_id, message_id, chat_id) VALUES(?, ?, ?)',
                   (game_id, message_id, chat_id, ))
    conn.commit()
async def delete_pin(game_id):
    cursor.execute('DELETE FROM game_messages WHERE game_id = ?', (game_id, ))
    conn.commit()
async def get_pins(game_id):
    return cursor.execute('SELECT * FROM game_messages WHERE game_id = ?', (game_id, )).fetchall()
async def get_pin(chat_id):
    return cursor.execute('SELECT * FROM game_messages WHERE chat_id = ?', (chat_id, )).fetchone()
async def check_user(username):
    return cursor.execute('SELECT * FROM users WHERE username = ?', (username, )).fetchone()
async def check_user_name(name):
    return cursor.execute('SELECT * FROM users WHERE first_name = ?', (name, )).fetchone()
async def add_balance(user_id, value):
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (value, user_id))
    conn.commit()
async def check_vip(user_id):
    return cursor.execute('SELECT vip FROM users WHERE user_id = ?', (user_id, )).fetchone()
async def add_vip(user_id, value):
    date = datetime.datetime.now().date() + datetime.timedelta(days=value)
    cursor.execute('UPDATE users SET vip = ? WHERE user_id = ?', (date, user_id))
async def set_daily_loto():
    cursor.execute('INSERT INTO daily_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def set_monthly_loto():
    cursor.execute('INSERT INTO monthly_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def set_weekly_loto():
    cursor.execute('INSERT INTO weekly_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def daily_winner():
    loto = cursor.execute('SELECT * FROM daily_loto WHERE active = 1').fetchone()
    users = cursor.execute('SELECT user_id FROM daily_users WHERE loto_id = ?', (loto[0], )).fetchall()
    if users:
        winner = random.choice(users)
        return await get_user(winner[0])
async def monthly_winner():
    loto = cursor.execute('SELECT * FROM monthly_loto WHERE active = 1').fetchone()
    users = cursor.execute('SELECT user_id FROM monthly_users WHERE loto_id = ?', (loto[0], )).fetchall()
    if users:
        winner = random.choice(users)
        return await get_user(winner[0])
async def weekly_winner():
    loto = cursor.execute('SELECT * FROM weekly_loto WHERE active = 1').fetchone()
    users = cursor.execute('SELECT user_id FROM weekly_users WHERE loto_id = ?', (loto[0], )).fetchall()
    if users:
        winner = random.choice(users)
        return await get_user(winner[0])
async def set_new_daily_loto():
    cursor.execute('UPDATE daily_loto SET active = 0, end_date = ? WHERE active = 1',
                   (datetime.datetime.now().date(), ))
    cursor.execute('INSERT INTO daily_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def set_new_monthly_loto():
    cursor.execute('UPDATE monthly_loto SET active = 0, end_date = ? WHERE active = 1',
                   (datetime.datetime.now().date(), ))
    cursor.execute('INSERT INTO monthly_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def set_new_weekly_loto():
    cursor.execute('UPDATE weekly_loto SET active = 0, end_date = ? WHERE active = 1',
                   (datetime.datetime.now().date(), ))
    cursor.execute('INSERT INTO weekly_loto(start_date, end_date, active) VALUES(?, ?, ?)',
                   (datetime.datetime.now().date(), '', 1, ))
    conn.commit()
async def check_daily_user(user_id):
    loto = await get_active_daily_loto()
    return cursor.execute('SELECT user_id FROM daily_users WHERE loto_id = ? AND user_id = ?',
                          (loto[0], user_id)).fetchone()
async def check_monthly_user(user_id):
    loto = await get_active_monthly_loto()
    return cursor.execute('SELECT user_id FROM monthly_users WHERE loto_id = ? AND user_id = ?',
                          (loto[0], user_id)).fetchone()
async def check_weekly_user(user_id):
    loto = await get_active_weekly_loto()
    return cursor.execute('SELECT user_id FROM weekly_users WHERE loto_id = ? AND user_id = ?',
                          (loto[0], user_id)).fetchone()
async def get_daily_users_count():
    loto = await get_active_daily_loto()
    return cursor.execute('SELECT COUNT(user_id) FROM daily_users WHERE loto_id = ?', (loto[0], )).fetchall()[0]
async def get_monthly_users_count():
    loto = await get_active_monthly_loto()
    return cursor.execute('SELECT COUNT(user_id) FROM monthly_users WHERE loto_id = ?', (loto[0], )).fetchall()[0]
async def get_weekly_users_count():
    loto = await get_active_weekly_loto()
    return cursor.execute('SELECT COUNT(user_id) FROM weekly_users WHERE loto_id = ?', (loto[0], )).fetchall()[0]
async def add_spin(user_id):
    cursor.execute('UPDATE users SET spins = spins + 1 WHERE user_id = ?', (user_id, ))
    conn.commit()
async def get_daily_users():
    loto = await get_active_daily_loto()
    return cursor.execute('SELECT user_id FROM daily_users WHERE loto_id = ?', (loto[0], )).fetchall()[0]
async def get_monthly_users():
    loto = await get_active_monthly_loto()
    return cursor.execute('SELECT user_id FROM monthly_users WHERE loto_id = ?', (loto[0], )).fetchall()
async def get_weekly_users():
    loto = await get_active_weekly_loto()
    return cursor.execute('SELECT user_id FROM weekly_users WHERE loto_id = ?', (loto[0], )).fetchall()[0]
async def get_active_weekly_loto():
    return cursor.execute('SELECT * FROM weekly_loto WHERE active = 1').fetchone()
async def get_weekly_ticket(user_id):
    loto = await get_active_weekly_loto()
    cursor.execute('INSERT INTO weekly_users(loto_id, user_id) VALUES(?, ?)', (loto[0], user_id))
    conn.commit()
async def get_active_monthly_loto():
    return cursor.execute('SELECT * FROM daily_loto WHERE active = 1').fetchone()
async def get_monthly_ticket(user_id):
    loto = await get_active_monthly_loto()
    cursor.execute('INSERT INTO monthly_users(loto_id, user_id) VALUES(?, ?)', (loto[0], user_id))
    conn.commit()
async def get_active_daily_loto():
    return cursor.execute('SELECT * FROM daily_loto WHERE active = 1').fetchone()
async def get_daily_ticket(user_id):
    loto = await get_active_daily_loto()
    cursor.execute('INSERT INTO daily_users(loto_id, user_id) VALUES(?, ?)', (loto[0], user_id))
    conn.commit()
async def update_balance(user_id, value):
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (value, user_id))
    conn.commit()
async def get_game_history():
    return cursor.execute("SELECT * FROM games WHERE end_date != ''").fetchall()
async def get_game_users_count(game_id):
    return cursor.execute('SELECT COUNT(user_id) FROM game_users WHERE game_id = ?', (game_id, )).fetchone()[0]
async def get_game_winners_count(game_id):
    return cursor.execute('SELECT COUNT(user_id) FROM game_winners WHERE game_id = ?', (game_id, )).fetchone()[0]
async def get_game_winners(game_id):
    return cursor.execute('SELECT * FROM game_winners WHERE game_id = ?', (game_id, )).fetchall()
async def get_prize(prize_id):
    return cursor.execute('SELECT * FROM game_prizes WHERE prize_id = ?', (prize_id, )).fetchone()
async def add_prize(prize_text, game_id, count):
    cursor.execute('INSERT INTO game_prizes(prize_text, game_id, prize_count) VALUES(?, ?, ?)',
                   (prize_text, game_id, count))
    conn.commit()
async def get_game_user(game_id, user_id):
    return cursor.execute('SELECT * FROM game_users WHERE game_id = ? AND user_id = ?', (game_id, user_id)).fetchone()
async def get_game_users(game_id):
    return cursor.execute('SELECT user_id FROM game_users WHERE game_id = ?', (game_id, )).fetchall()
async def add_winner(user_id, prize_id, game_id):
    cursor.execute('INSERT INTO game_winners(user_id, prize_id, game_id) VALUES(?, ?, ?)',
                   (user_id, prize_id, game_id, ))
    conn.commit()
async def get_user(user_id):
    return cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id, )).fetchone()
async def end_game(game_id):
    cursor.execute('UPDATE games SET active = 0, end_date = ? WHERE game_id = ?',
                   (datetime.datetime.now().date(), game_id, ))
    conn.commit()
async def number_of_users(game_id):
    return cursor.execute('SELECT COUNT(user_id) FROM game_users WHERE game_id = ?',
                          (game_id, )).fetchone()[0]
async def prize_update_count(prize_id, count):
    cursor.execute('UPDATE game_prizes SET prize_count = ? WHERE prize_id = ?', (count, prize_id,))
    conn.commit()
async def prize_update_text(prize_id, text):
    cursor.execute('UPDATE game_prizes SET prize_text = ? WHERE prize_id = ?', (text, prize_id, ))
    conn.commit()
async def get_free_address(user_id):
    check = cursor.execute('SELECT COUNT(*) FROM addresses WHERE user_id = ?', (user_id, )).fetchone()[0]
    if check >= 1:
        return None
    else:
        address = cursor.execute('SELECT address_id FROM addresses WHERE active = 1 AND user_id = 0').fetchone()
        cursor.execute('UPDATE addresses SET user_id = ?, active = 0 WHERE address_id = ?',
                       (user_id, address[0], ))
        conn.commit()
        address = cursor.execute('SELECT address FROM addresses WHERE user_id = ?', (user_id, )).fetchone()
        return address
async def get_prizes(game_id):
    return cursor.execute('SELECT * FROM game_prizes WHERE game_id = ?', (game_id, )).fetchall()
async def get_prizes_count(game_id):
    return cursor.execute('SELECT COUNT(prize_id) FROM game_prizes WHERE game_id = ?', (game_id,)).fetchone()[0]
async def add_prizes(text, count, game_id):
    cursor.execute('INSERT INTO game_prizes(prize_text, game_id, prize_count) VALUES (?, ?, ?)', (text, game_id, count))
    conn.commit()
async def del_prize(prize_id: int):
    cursor.execute('DELETE FROM game_prizes WHERE prize_id = ?', (prize_id, ))
    conn.commit()
async def register_user(user_id, username, first_name, referrer):
    if cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id, )).fetchone():
        return False
    cursor.execute('INSERT INTO users(user_id, username, first_name, subscribe_until, karma, referrer_id, balance) VALUES(?, ?, ?, ?, ?, ?, ?)',
                   (user_id, username, first_name, str(datetime.datetime.now().date() + datetime.timedelta(days=7)), 0, referrer, 0, ))
    conn.commit()
    return True
async def check_subscribe_db(user_id) -> list:
    subscribe = cursor.execute('SELECT subscribe_until FROM users WHERE user_id = ?',
                               (user_id, )).fetchone()[0]
    if datetime.datetime.now().date() > datetime.datetime.fromisoformat(subscribe).date():
        return [False, subscribe]
    return [True, subscribe]
async def get_user_by_username(username):
    return cursor.execute('SELECT user_id FROM users WHERE username = ? or first_name = ?',
                          (username, username, )).fetchone()
async def update_subscribe(user_id, subscribe_left):
    cursor.execute('UPDATE users SET subscribe_until = ? WHERE user_id = ?',
                   (str((datetime.datetime.now() + datetime.timedelta(days=subscribe_left)).date()), user_id))
    conn.commit()
async def add_message(user_id, username):
    check = cursor.execute('SELECT count FROM messages WHERE user_id = ? AND date = ?',
                           (user_id, datetime.datetime.now().date())).fetchone()
    if not check:
        cursor.execute('INSERT INTO messages(user_id, username, date, count) VALUES(?, ?, ?, ?)',
                       (user_id, username, datetime.datetime.now().date(), 1))
    else:
        cursor.execute('UPDATE messages SET count = count + 1 WHERE user_id = ? AND date = ?',
                       (user_id, datetime.datetime.now().date()))
    conn.commit()
async def get_messages():
    return cursor.execute('SELECT user_id, username, date, count FROM messages').fetchall()
async def add_game(users_count, winners_count, game_name):
    cursor.execute('INSERT INTO games(users_count, winners_count, start_date, end_date, active, game_name) '
                   'VALUES(?, ?, ?, ?, ?, ?)',
                   (users_count, winners_count, '', '', 0, game_name, ))
    conn.commit()
async def get_last_game():
    return cursor.execute('SELECT * FROM games WHERE end_date = ? ORDER BY game_id DESC',
                          ('', )).fetchone()
async def get_games_history():
    return cursor.execute('SELECT * FROM games WHERE end_date != ?',
                          ('', )).fetchall()
async def get_games_month():
    return cursor.execute('SELECT * FROM games WHERE start_date > ?', (datetime.datetime.now().date() - datetime.timedelta(days=30), )).fetchall()
async def get_prizes_month():
    return cursor.execute('SELECT * FROM game_prizes WHERE game_id IN (SELECT game_id FROM games WHERE start_date > ?)',
                          (datetime.datetime.now().date() - datetime.timedelta(days=30), )).fetchall()
async def get_prizes_all():
    return cursor.execute('SELECT * FROM game_prizes').fetchall()


async def delete_game(game_id):
    cursor.execute('DELETE FROM games WHERE game_id = ?', (game_id, ))
    conn.commit()
async def set_balance(user_id, value):
    cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
async def start_game(game_id):
    cursor.execute('UPDATE games SET active = 1, start_date = ? WHERE game_id = ?',
                   (datetime.datetime.now().date(), game_id, ))
    conn.commit()
async def get_users():
    return cursor.execute('SELECT user_id FROM users').fetchall()
async def get_game(game_id):
    return cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id, )).fetchone()
async def join_game(game_id, user_id):
    count_users = cursor.execute('SELECT COUNT(*) FROM game_users WHERE game_id = ? AND user_id = ?',
                           (game_id, user_id)).fetchone()[0]
    max_users = cursor.execute('SELECT users_count FROM games WHERE game_id = ?',
                               (game_id, )).fetchone()[0]
    if count_users >= max_users:
        return False
    else:
        cursor.execute('INSERT INTO game_users(game_id, user_id) VALUES(?, ?)', (game_id, user_id))
        conn.commit()
        return True
async def get_active_addresses_count():
    return cursor.execute('SELECT COUNT(address) FROM addresses WHERE active = 1').fetchall()[0]
async def get_addresses():
    return cursor.execute('SELECT * FROM addresses').fetchall()
async def get_active_game():
    return cursor.execute('SELECT * FROM games WHERE active = 1').fetchone()
async def get_address(address_id):
    return cursor.execute('SELECT * FROM addresses WHERE address_id = ?', (address_id, )).fetchone()
async def get_user_address(user_id):
    return cursor.execute('SELECT address FROM addresses WHERE user_id = ?', (user_id, )).fetchall()
async def get_referrers_count(user_id):
    return cursor.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id, )).fetchone()[0]
async def deactivate_address(address_id):
    cursor.execute('UPDATE addresses SET active = 0 WHERE address_id = ?', (address_id, ))
    conn.commit()
async def activate_address(address_id):
    cursor.execute('UPDATE addresses SET active = 1 WHERE address_id = ?', (address_id, ))
    conn.commit()
async def delete_address(address_id):
    cursor.execute('DELETE FROM addresses WHERE address_id = ?', (address_id, ))
    conn.commit()
async def add_address(address):
    cursor.execute('INSERT INTO addresses(address, user_id) VALUES(?, ?)', (address, 0, ))
    conn.commit()
async def is_banned(user_id):
    ban_until = cursor.execute('SELECT ban_until FROM users WHERE user_id = ?',
                               (user_id, )).fetchone()[0]
    if ban_until == '':
        return False
    if datetime.datetime.fromisoformat(ban_until) > datetime.datetime.now():
        cursor.execute('UPDATE users SET banned = 0, ban_until = ? WHERE user_id = ?',
                       ('', user_id, ))
        conn.commit()
        return False
    return (cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id, )).fetchone()) == 1
async def ban_user_db(user_id, time):
    cursor.execute('UPDATE users SET banned = 1, ban_until = ? WHERE user_id = ?',
                   (time, user_id,))
    conn.commit()
async def unban_user_db(user_id):
    cursor.execute('UPDATE users SET banned = 0, ban_until = ? WHERE user_id = ?',
                   ('', user_id, ))
    conn.commit()
async def add_karma_db(target_id, user_id):
    last_karma = cursor.execute('SELECT last_karma FROM users WHERE user_id = ?', (user_id, )).fetchone()
    if last_karma[0]:
        if datetime.datetime.strptime(last_karma[0], '%Y-%m-%d %H:%M:%S.%f') >= (datetime.datetime.now() + datetime.timedelta(minutes=KARMA_TIMEOUT)):
            cursor.execute('UPDATE users SET last_karma = ? WHERE user_id = ?', (datetime.datetime.now(), user_id))
            karma = cursor.execute('SELECT karma FROM users WHERE user_id = ?', (target_id, )).fetchone()[0]
            cursor.execute('UPDATE users SET karma = ? + 1 WHERE user_id = ?', (karma, target_id,))
            conn.commit()
            return True
        else:
            return False
    else:
        cursor.execute('UPDATE users SET last_karma = ? WHERE user_id = ?', (datetime.datetime.now(), user_id))
        karma = cursor.execute('SELECT karma FROM users WHERE user_id = ?', (target_id, )).fetchone()[0]
        cursor.execute('UPDATE users SET karma = ? + 1 WHERE user_id = ?', (karma, target_id,))
        conn.commit()
        return True


