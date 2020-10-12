import datetime
import time
import telebot
import config
import sqlite3
from telebot import types
from hashlib import sha256
import phrases
from math import sin, cos, sqrt, atan2, radians


def format_value(x, i=2):
    out = ''
    while x[i] != '\'':
        out += x[i]
        i += 1
    return out


def get_hash(string):
    return str(sha256(bytes(string, 'utf-8')).hexdigest())


def get_time():
    named_tuple = time.localtime()
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return time_string


def get_value_from_users(message, row):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT ' + row + ' FROM users WHERE Telegram_id=?'
    row = cursor.execute(query, [str(message.from_user.id)])
    row = row.fetchone()
    row = str(row)
    if row != '(None,)' and row != 'None':
        row = row[2:len(row) - 3]
    conn.close()
    return row


def get_value_from_tasks(id_of_task, row):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT ' + row + ' FROM tasks WHERE id=?'
    row = cursor.execute(query, [id_of_task])
    row = row.fetchone()
    row = str(row)
    if row != '(None,)' and row != 'None':
        row = row[2:len(row) - 3]
    conn.close()
    return row


def get_number_from_tasks(id_of_task, row):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT ' + row + ' FROM tasks WHERE id=?'
    row = cursor.execute(query, [id_of_task])
    row = row.fetchone()
    row = str(row)
    if row != '(None,)' and row != 'None':
        row = row[1:len(row) - 2]
    conn.close()
    return row


def does_user_exist(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    request = [user_id]
    exe = 'SELECT * FROM users WHERE Telegram_id = ?'
    cursor.execute(exe, request)
    exist = cursor.fetchone()
    if exist is None:
        return False
    else:
        return True
    conn.commit()
    conn.close()


def get_dif_of_time(t1, t2):
    date1, time1 = t1.split()
    date1 = date1.split('-')
    time1 = time1.split(':')

    t1 = datetime.datetime(int(date1[0]), int(date1[1]), int(date1[2]), int(time1[0]), int(time1[1]), 0, 0)
    time_dif = ((t2 - t1).total_seconds())/60/60
    return round(time_dif, 1)


def fill_phone(message):
    bot = telebot.TeleBot(config.token)
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    button_phone = types.KeyboardButton(text="Send phone number", request_contact=True)
    keyboard.add(button_phone)
    bot.send_message(message.chat.id, phrases.fill_phone,
                     reply_markup=keyboard)


def set_value(user_id, row, value):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'UPDATE users SET ' + row + '=? WHERE Telegram_id=?'
    cursor.execute(query, [value, user_id])
    conn.commit()
    conn.close()


def user_registration(phone_number, message):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    new_user = [message.from_user.id, message.chat.id, phone_number, 0]
    cursor.execute("insert into users('Telegram_id', 'CHAT_ID', 'Phone', 'Balance') values (?, ?, ?, ?)", new_user)
    conn.commit()
    conn.close()


def send_photo_to_admin(file_name, message, bot):
    img = open('users/' + file_name, 'rb')
    name = get_value_from_users(message, 'name')
    surname = get_value_from_users(message, 'surname')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT Age FROM users WHERE Telegram_id=?'
    age = cursor.execute(query, [str(message.from_user.id)])
    age = age.fetchone()
    age = str(age)
    age = age[1:(len(age)-2)]
    conn.close()
    data = name + ' ' + surname + ' ' + age
    markup = types.InlineKeyboardMarkup()
    user_and_chat = str(message.from_user.id) + '-' + str(message.chat.id)
    btn1 = types.InlineKeyboardButton(text='\u2705', callback_data='{0}-ACCEPT'.format(
        user_and_chat))
    btn2 = types.InlineKeyboardButton(text='\uE333', callback_data='{0}-DECLINE'.format(
        user_and_chat))
    markup.add(btn1, btn2)
    bot.send_photo(config.admin_chat, img)
    bot.send_message(config.admin_chat, data, reply_markup=markup)
    img.close()


def create_task(message, description, age_limit):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    values = [message.from_user.id, description, age_limit]
    query = "INSERT INTO tasks('Owner_telegram_id', 'Description', 'Age_limit') VALUES (?, ?, ?)"
    cursor.execute(query, values)
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return(task_id)


def success_of_money_reservation(task_id):
    user_id = float(get_number_from_tasks(task_id, 'Owner_telegram_id'))
    price_for_del = float(get_number_from_tasks(task_id, 'Price_for_delivery'))
    price_for_goods = float(get_number_from_tasks(task_id, 'Price_for_goods'))
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT Balance FROM users WHERE Telegram_id=?'
    row = cursor.execute(query, [user_id])
    row = row.fetchone()
    row = str(row)
    if row != '(None,)' and row != 'None':
        row = row[1:len(row) - 2]
    conn.close()
    balance = float(row)
    if balance < price_for_del + price_for_goods:
        return False
    else:
        balance -= price_for_goods
        balance -= price_for_del
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        query = 'UPDATE users SET Balance=? WHERE Telegram_id=?'
        cursor.execute(query, [balance, user_id])
        conn.commit()
        conn.close()
        return True


def calculate_distance(x1, y1, x2, y2):
    R = 6373.0
    lat1 = radians(x1)
    lon1 = radians(y1)
    lat2 = radians(x2)
    lon2 = radians(y2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def send_task_to_couriers(bot, task_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = 'SELECT * FROM users WHERE Courier=1'
    couriers = cursor.execute(query).fetchall()
    query = 'SELECT * FROM tasks WHERE id=?'
    task_data = cursor.execute(query, [task_id]).fetchone()
    for courier in couriers:
        distance = calculate_distance(float(task_data[7]), float(task_data[8]), float(courier[5]), float(courier[6]))
        if distance <= float(courier[7]) and (not(bool(task_data[5])) + (courier[3] < 18)):
            message = 'Новое задание\n'
            message = message + 'Расстояние до точки: ' + str(round(courier[7] - distance, 2)) + '\n'
            message = message + 'Описание: ' + task_data[2] + '\n'
            message = message + 'Стоимость продуктов: ' + str(task_data[4]) + '\n'
            message = message + 'Прибыль: ' + str(task_data[3])
            markup = types.InlineKeyboardMarkup()
            courier_data = str(courier[0]) + '-' + str(task_id)
            btn1 = types.InlineKeyboardButton(text='Принять \u2705', callback_data='{0}-ACCEPT_DELIVERY'.format(
                courier_data))
            markup.add(btn1)
            bot.send_message(courier[12], message, reply_markup=markup)
    conn.close()
