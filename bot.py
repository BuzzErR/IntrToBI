import telebot
import config
import logging
import functions
import datetime
import sqlite3
import phrases
from telebot import types
import time

logging.basicConfig(filename=config.log_file_name,level=logging.DEBUG)
bot = telebot.TeleBot(config.token, threaded=False)
logging.getLogger("requests").setLevel(logging.WARNING)

try:
    logging.info('Connected ' + functions.get_time())


    @bot.message_handler(commands=['start'])
    def start(message):
        if not functions.does_user_exist(str(message.from_user.id)):
            functions.fill_phone(message)
        else:
            bot.send_message(message.chat.id, 'Ты уже зарегестрирован')


    @bot.message_handler(commands=['balance'])
    def get_balance(message):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        query = 'SELECT Balance FROM users WHERE Telegram_id=?'
        row = cursor.execute(query, [message.from_user.id])
        row = row.fetchone()
        row = str(row)
        if row != '(None,)' and row != 'None':
            row = row[1:len(row) - 2]
        conn.close()
        bot.send_message(message.chat.id, row)


    @bot.message_handler(func=lambda message: not (functions.does_user_exist(str(message.from_user.id))))
    def reg_for_user(message):
        bot.send_message(message.chat.id, phrases.unknown_user)


    @bot.message_handler(func=lambda message: functions.get_value_from_users(message, 'status') == 'Waiting_for_name')
    def waiting_for_pass(message):
        functions.set_value(message.from_user.id, 'Name', message.text)
        functions.set_value(message.from_user.id, 'STATUS', 'Waiting_for_surname')
        bot.send_message(message.chat.id, phrases.name_completed)


    @bot.message_handler(func=lambda message: functions.get_value_from_users(message, 'status') == 'Waiting_for_surname')
    def waiting_for_pass(message):
        functions.set_value(message.from_user.id, 'Surname', message.text)
        functions.set_value(message.from_user.id, 'STATUS', 'Waiting_for_age')
        bot.send_message(message.chat.id, phrases.surname_completed)


    @bot.message_handler(func=lambda message: functions.get_value_from_users(message, 'status') == 'Waiting_for_age')
    def waiting_for_pass(message):
        try:
            age = int(message.text)
            if age > 13:
                functions.set_value(message.from_user.id, 'Age', age)
                functions.set_value(message.from_user.id, 'STATUS', 'Waiting_for_passport')
                bot.send_message(message.chat.id, phrases.age_completed)
            else:
                functions.set_value(message.from_user.id, 'STATUS', '')
                bot.send_message(message.chat.id, 'Прости, но сервис недоступен для людей младше 14 лет.')

        except Exception as e:
            bot.send_message(message.chat.id, phrases.not_int_age)


    @bot.message_handler(content_types=['photo'])
    def apply_pass(message):
        if functions.get_value_from_users(message, 'STATUS') == 'Waiting_for_passport':
            if functions.get_value_from_users(message, 'PASS_FILE') == '(None,)' or \
                    functions.get_dif_of_time(functions.get_value_from_users(message, 'PASS_FILE').split('_')[1], datetime.datetime.now()) > 24:
                file_id = message.photo[-1].file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_name = str(message.from_user.id) + '_' + str(datetime.datetime.now())
                functions.set_value(message.from_user.id, 'PASS_FILE', file_name)
                with open('users/' + file_name, 'wb') as new_file:
                    new_file.write(downloaded_file)
                functions.send_photo_to_admin(file_name, message, bot)
                bot.send_message(message.chat.id, phrases.pass_photo_received)
            else:
                estimated_time = 24 - functions.get_dif_of_time(functions.get_value_from_users(message, 'PASS_FILE').split('_')[1], datetime.datetime.now())
                bot.send_message(message.chat.id, phrases.wrong_time_of_photo + str(estimated_time) + ' часа')


    @bot.message_handler(func=lambda message: functions.get_value_from_users(message, 'status') == 'Waiting_for_passport')
    def waiting_for_pass(message):
        bot.send_message(message.chat.id, phrases.info_about_pass)


    @bot.message_handler(content_types=['contact'])
    def get_number(message):
        if not functions.does_user_exist(str(message.from_user.id)):
            if message.from_user.id == message.contact.user_id:
                functions.user_registration(message.contact.phone_number, message)
                functions.set_value(message.from_user.id, 'STATUS', 'Waiting_for_name')
                bot.send_message(message.chat.id, phrases.success_contact)
            else:
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
                button_phone = types.KeyboardButton(text="Send phone number", request_contact=True)
                keyboard.add(button_phone)
                bot.send_message(message.chat.id,
                                 'Прости, но мне требуется твой настоящий номер телефона, привязаныый к данному'
                                 ' аккаунту',
                                 reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, 'Не понял тебя')


    @bot.callback_query_handler(func=lambda call: True)
    def callback_inline(call):
        if call.message:
            data = call.data.split('-')
            if data[2] == 'ACCEPT':
                functions.set_value(data[0], 'Approved', 1)
                functions.set_value(data[0], 'STATUS', None)
                user_and_chat = data[0] + '-' + data[1]
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton(text='\U0001F3E0 Получать', callback_data='{0}-HOME'.format(
                    user_and_chat))
                btn2 = types.InlineKeyboardButton(text='\U0001F6F4 Доставлять', callback_data='{0}-COURIER'.format(
                    user_and_chat))
                markup.add(btn1, btn2)
                bot.send_message(int(data[1]), phrases.account_accepted, reply_markup=markup)
            elif data[2] == 'DECLINE':
                functions.set_value(data[0], 'Approved', 0)
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE Telegram_id=?', [data[1]])
                conn.commit()
                conn.close()
                bot.send_message(int(data[1]), phrases.account_declined)
            elif data[2] == 'HOME':
                functions.set_value(data[0], 'Courier', 0)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=False)
                button_phone = types.KeyboardButton(text="Разместить заказ")
                keyboard.add(button_phone)
                button_phone = types.KeyboardButton(text="Отменить")
                keyboard.add(button_phone)
                bot.send_message(int(data[1]), phrases.home_selected, reply_markup=keyboard)
            elif data[2] == 'COURIER':
                functions.set_value(data[0], 'Courier', 1)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=False)
                button_phone = types.KeyboardButton(text="Установить локацию по умолчанию")
                keyboard.add(button_phone)
                button_phone = types.KeyboardButton(text="Установить радиус доставки")
                keyboard.add(button_phone)
                button_phone = types.KeyboardButton(text="Отменить")
                keyboard.add(button_phone)
                bot.send_message(int(data[1]), phrases.courier_selected, reply_markup=keyboard)
            elif data[2] == 'ACCEPT_DELIVERY':
                courier_id = data[0]
                task_id = data[1]
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                query = 'SELECT id FROM tasks WHERE Is_completed="FALSE" AND Courier=?'
                num_of_courier_tasks = cursor.execute(query, [courier_id]).fetchall()
                if len(num_of_courier_tasks) == 0:
                    if functions.get_number_from_tasks(task_id, 'Courier') == '(None,)':
                        conn = sqlite3.connect('users.db')
                        cursor = conn.cursor()
                        query = 'UPDATE tasks SET Courier=? WHERE id=?'
                        cursor.execute(query, [courier_id, task_id])
                        conn.commit()
                        conn = sqlite3.connect('users.db')
                        cursor = conn.cursor()
                        query = 'SELECT * FROM users WHERE Telegram_id=?'
                        courier = cursor.execute(query, [courier_id]).fetchone()
                        query = 'SELECT Owner_telegram_id FROM tasks WHERE id=?'
                        owner = cursor.execute(query, [task_id])
                        owner = owner.fetchone()[0]
                        conn.close()
                        message_text = 'Курьер принял Ваш заказ №' + str(task_id) + '\n'
                        message_text = message_text + courier[1] + ' ' + courier[2] + '\n'
                        message_text += str(courier[4])
                        bot.send_message(owner, message_text)
                        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=False)
                        button_phone = types.KeyboardButton(text="Отправить фотографию товаров")
                        keyboard.add(button_phone)
                        bot.send_message(courier_id, 'Отлично, пришли фотографию товаров и чека, когда всё купишь',
                                         reply_markup=keyboard)
                    else:
                        bot.send_message(courier_id, 'Увы, данный заказ уже кто-то взял')
                else:
                    bot.send_message(courier_id, 'У тебя ещё есть невыполненный заказ, новый ты пока взять не можешь')
            else:
                pass


    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        if message.text == 'Разместить заказ':
            bot.send_message(message.chat.id, 'Что и где нужно купить?')
            bot.register_next_step_handler(message, enter_task_desc)
        elif message.text == 'Отменить':
            bot.send_message(message.chat.id, 'Ладно, как знаешь')
        elif message.text == 'Установить локацию по умолчанию':
            bot.register_next_step_handler(message, set_courier_home_loc)
            bot.send_message(message.chat.id, 'Отлично, просто отправьте геолокацию')
        elif message.text == 'Установить радиус доставки':
            bot.register_next_step_handler(message, set_courier_radius)
            bot.send_message(message.chat.id, 'Отлично, просто отправьте радиус в километрах '
                                              '(десятичную часть записывайте через точку)')
        elif message.text == 'Отправить фотографию товаров':
            conn = sqlite3.connect('users.db')
            bot.send_message(message.chat.id, 'Жду')
            bot.register_next_step_handler(message, get_photo_of_goods)
        else:
            bot.send_message(message.chat.id, phrases.unexpected_message)


    def get_photo_of_goods(message):
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'SELECT id FROM tasks WHERE Courier=?'
            task_id = cursor.execute(query, [message.from_user.id]).fetchone()[0]
            cursor = conn.cursor()
            query = 'SELECT Photo_of_products FROM tasks Where id=?'
            photo = cursor.execute(query, [task_id]).fetchone()[0]
            if photo == None:
                downloaded_file = bot.download_file(file_info.file_path)
                file_name = 'GOODS_' + str(task_id) + '_' + str(datetime.datetime.now())
                with open('goods/' + file_name, 'wb') as new_file:
                    new_file.write(downloaded_file)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
                button_phone = types.KeyboardButton(text="Отправить фотографию чека")
                keyboard.add(button_phone)
                bot.send_message(message.chat.id, 'Принял, осталось прислать фотографию чека', reply_markup=keyboard)
                img = open('goods/' + file_name, 'rb')
                query = 'SELECT Owner_telegram_id FROM tasks WHERE id=?'
                customer_id = cursor.execute(query, [task_id]).fetchone()[0]
                bot.send_photo(customer_id, img)
                bot.send_message(customer_id, 'Ваш заказ уже в пути, в скором времени перешлю фотографию чека.')
                bot.register_next_step_handler(message, get_photo_of_bill)
                query = 'UPDATE tasks SET Photo_of_products=? WHERE id=?'
                cursor.execute(query, [file_name, task_id])
                conn.commit()
                conn.close()
            else:
                bot.send_message(message.chat.id, 'Погоди, ты уже отправлял фотку товаров, так не пойдёт.')
        except Exception as e:
            bot.register_next_step_handler(message, get_photo_of_goods)
            bot.send_message(message.chat.id, 'Кажется, это не фоторафия, отправь ещё раз.')


    def get_photo_of_bill(message):
        try:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'SELECT id FROM tasks WHERE Courier=?'
            task_id = cursor.execute(query, [message.from_user.id]).fetchone()[0]
            cursor = conn.cursor()
            query = 'SELECT Photo_of_products FROM tasks Where id=?'
            photo = cursor.execute(query, [task_id]).fetchone()[0]
            if photo == None:
                downloaded_file = bot.download_file(file_info.file_path)
                file_name = 'GOODS_' + str(task_id) + '_' + str(datetime.datetime.now())
                with open('goods/' + file_name, 'wb') as new_file:
                    new_file.write(downloaded_file)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
                button_phone = types.KeyboardButton(text="Отправить фотографию чека")
                keyboard.add(button_phone)
                bot.send_message(message.chat.id, 'Принял, осталось прислать фотографию чека', reply_markup=keyboard)
                img = open('goods/' + file_name, 'rb')
                query = 'SELECT Owner_telegram_id FROM tasks WHERE id=?'
                customer_id = cursor.execute(query, [task_id]).fetchone()[0]
                bot.send_photo(customer_id, img)
                bot.send_message(customer_id, 'Ваш заказ уже в пути, в скором времени перешлю фотографию чека.')
                bot.register_next_step_handler(message, get_photo_of_bill)
                query = 'UPDATE tasks SET Photo_of_products=? WHERE id=?'
                cursor.execute(query, [file_name, task_id])
                conn.commit()
                conn.close()
            else:
                bot.send_message(message.chat.id, 'Погоди, ты уже отправлял фотку товаров, так не пойдёт.')
        except Exception as e:
            bot.register_next_step_handler(message, get_photo_of_goods)
            bot.send_message(message.chat.id, 'Кажется, это не фоторафия, отправь ещё раз.')


    def set_courier_home_loc(message):
        try:
            lat, lon = message.location.latitude, message.location.longitude
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'UPDATE users SET Home_lat=? WHERE Telegram_id=?'
            value = [lat, message.from_user.id]
            cursor.execute(query, value)
            conn.commit()
            query = 'UPDATE users SET Home_long=? WHERE Telegram_id=?'
            value = [lon, message.from_user.id]
            cursor.execute(query, value)
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, 'Теперь осталось установить радиус доставки')
        except Exception as e:
            if message.text == 'Отменить':
                bot.send_message(message.chat.id, 'Ладно, как знаешь')
            else:
                print(e)
                bot.send_message(message.chat.id, phrases.wrong_location)
                bot.register_next_step_handler(message, enter_point)


    def set_courier_radius(message):
        rad = message.text
        try:
            rad = float(rad)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'UPDATE users SET Radius_of_tasks=? WHERE Telegram_id=?'
            value = [rad, message.from_user.id]
            cursor.execute(query, value)
            conn.commit()
            bot.send_message(message.chat.id, 'Супер, как только будут задания - я оповещу. Не пропадай')
        except Exception as e:
            if message.text == 'Отменить':
                bot.send_message(message.chat.id, 'Ладно, как знаешь')
            else:
                bot.send_message(message.chat.id, phrases.not_number)
                bot.register_next_step_handler(message, set_courier_radius)


    def enter_task_desc(message):
        if message.text == 'Отменить':
            bot.send_message(message.chat.id, 'Ладно, как знаешь')
        else:
            desc = message.text.split()
            age_limit = False
            for word in desc:
                if word.lower() in config.adult_products:
                    age_limit = True
                    break
            task_id = functions.create_task(message, message.text, age_limit)
            functions.set_value(message.from_user.id, 'Status', str(task_id))
            bot.send_message(message.chat.id, 'Отлично, куда это всё нужно доставить? Пришли геометку')
            bot.register_next_step_handler(message, enter_point)


    def enter_point(message):
        try:
            task_id = int(functions.get_value_from_users(message, 'Status'))
            lat, lon = message.location.latitude, message.location.longitude
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'UPDATE tasks SET Home_lat=? WHERE id=?'
            value = [lat, task_id]
            cursor.execute(query, value)
            conn.commit()
            query = 'UPDATE tasks SET Home_long=? WHERE id=?'
            value = [lon, task_id]
            cursor.execute(query, value)
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, 'Сколько будет стоить набор продуктов? Не волнуйся, если будет неточно, '
                                              'разница вернётся')
            bot.register_next_step_handler(message, set_price_for_goods)
        except Exception as e:
            if message.text == 'Отменить':
                bot.send_message(message.chat.id, 'Ладно, как знаешь')
            else:
                bot.send_message(message.chat.id, phrases.wrong_location)
                bot.register_next_step_handler(message, enter_point)


    def set_price_for_goods(message):
        price = message.text
        try:
            task_id = int(functions.get_value_from_users(message, 'Status'))
            price = float(price)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'UPDATE tasks SET Price_for_goods=? WHERE id=?'
            value = [price, task_id]
            cursor.execute(query, value)
            conn.commit()
            bot.register_next_step_handler(message, set_price_for_delivery)
            bot.send_message(message.chat.id, 'Сколько ты готов заплатить за доставку?')
        except Exception as e:
            if message.text == 'Отменить':
                bot.send_message(message.chat.id, 'Ладно, как знаешь')
            else:
                bot.send_message(message.chat.id, phrases.not_number)
                bot.register_next_step_handler(message, set_price_for_goods)


    def set_price_for_delivery(message):
        price = message.text
        try:
            task_id = int(functions.get_value_from_users(message, 'Status'))
            price = int(price)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            query = 'UPDATE tasks SET Price_for_delivery=? WHERE id=?'
            value = [price, task_id]
            cursor.execute(query, value)
            conn.commit()
            conn.close()
            order_text = 'Ваш заказ размещён, деньги зарезервированы, как только курьер примет заказ, ' \
                         'мы Вам сообщим.\n'
            desc = functions.get_value_from_tasks(task_id, 'Description')
            goods_price = functions.get_number_from_tasks(task_id, 'Price_for_goods')
            order_text += 'Номер заказа: ' + str(task_id) + '\n'
            order_text += 'Описание: ' + desc + '\n'
            order_text += 'Цена товаров: ' + goods_price + '\n'
            order_text += 'Цена доставки: ' + str(price) + '.0' + '\n'
            order_text += 'Узнать баланс: /balance'
            bot.send_message(message.chat.id, order_text)
            if not functions.success_of_money_reservation(task_id):
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id=?', [task_id])
                conn.commit()
                conn.close()
                bot.send_message(message.chat.id, 'Кажется, у тебя не хватает денег. Узнать свой баланс можно по команде '
                                                  '/balance')
            else:
                functions.send_task_to_couriers(bot, task_id)
        except Exception as e:
            print(e)
            if message.text == 'Отменить':
                bot.send_message(message.chat.id, 'Ладно, как знаешь')
            else:
                bot.send_message(message.chat.id, phrases.not_number)
                bot.register_next_step_handler(message, set_price_for_delivery)


    if __name__ == '__main__':
        bot.polling(none_stop=True, timeout=123)()

except Exception as e:
    logging.error(e)
    time.sleep(3)
