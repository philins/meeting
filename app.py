#!/home/philins/meeting/botenv8/bin/python
# -*- coding: utf-8 -*-


import logging
import os
import ssl

from aiohttp import web

import telebot
from telebot import types

import functions, db


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

WEBHOOK_HOST = '62.109.29.107'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = 'url_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = 'url_private.key'  # Path to the ssl private key

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

log = telebot.logger
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('bot.log')
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
#ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.addHandler(fh)
log.addHandler(ch)
log.info("Start Bot")                    

bot = telebot.TeleBot(API_TOKEN)

app = web.Application()


# Process webhook calls
async def handle(request):
    if request.match_info.get('token') == bot.token:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)


app.router.add_post('/{token}/', handle)


user_dict = {}

hideKeyboard = types.ReplyKeyboardRemove()


class User:
    def __init__(self, name):
        self.name = name
        self.age = None
        self.sex = None
        self.lat = None
        self.lng = None


# START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        """Здравствуйте, {username}!
Я подберу вам случайного собеседника. Все сообщения полностью анонимны, до тех пор, пока вы не отправите свой контакт. 
Используйте команду /new для регистрации. Всего 3 вопроса.
/help для дополнительной информации."""
        .format(username=message.from_user.first_name))
    log.info(f"New user: {message.chat.id}")


# HELP
@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id,
        """Используемые команды:
/new - Регистрация. Вы должны представиться и указать пол и возраст. Можно вымышленные. После регистрации вы сможете искать собеседника, равно как и другие пользователи смогут вас найти.
Вы можете неоднократно менять свои данные.
/go - Поиск собеседника и начало диалога. Вы можете общаться только с одним собеседником в одно время. В это время вы не сможете начать другой диалог. 
Кнопка *Завершить* завершает текущий диалог. Теперь вы открыты к новому диалогу. 
Кнопка *Контакт* отправляет ваши контактные данные собеседнику. Если вы получили контакт собеседника, вы сможете добавить его в свою записную книжку и общаться напрямую. Анонимность здесь, естественно, заканчивается.
/delme - Удаление аккаунта. Вы можете удаляться вечером и вновь регистрироваться утром."""
        .format(username=message.from_user.first_name), parse_mode = 'markdown')
    log.info(f"New user: {message.chat.id}")


# STAT
@bot.message_handler(commands=['stat'])
def send_statistic(message: types.Message):
    """
    Show statistic
    """
    print("stat")
    total_users = functions.get_total_users()
    bot.send_message(message.chat.id, total_users, parse_mode = 'markdown')


# GO
@bot.message_handler(commands=['go'])
def select_companion(message: types.Message):
    """
    Select companion
    """
    companion = db.get_companion(message.chat.id)
    if companion:
        bot.send_message(message.chat.id, f"У вас уже есть собеседник {companion[1]}")
        return
    companion = functions.select_companion(message.from_user.id)
    if companion:
        bot.send_message(message.chat.id, 
        f"""
        Ваш собеседник: {companion[1]}
Возраст: {companion[2]}
Пол {companion[3]}
Язык {companion[4]}""")
    else:
        bot.send_message(message.chat.id, "Собеседник не найден.")


# DELME
@bot.message_handler(commands=['delme'])
def select_companion(message: types.Message):
    """
    Delete user
    """
    db.del_me(message.chat.id)
    bot.send_message(message.chat.id, "Ваша учётная запись удалена.", reply_markup = hideKeyboard)
    

# NEW
@bot.message_handler(commands=['new'])
def registration(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(message.from_user.first_name)
    markup.add("Cancel")
    msg = bot.send_message(message.chat.id,
        "Как вас зовут?"
        , reply_markup=markup)
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    try:
        chat_id = message.chat.id
        name = message.text
        if name == "Cancel":
            return
        user = User(name)
        user_dict[chat_id] = user
        msg = bot.send_message(message.chat.id, 'Сколько вам лет?', reply_markup = hideKeyboard)
        bot.register_next_step_handler(msg, process_age_step)
    except Exception as e:
        log.error(e)
        functions.call_admin(e)
        bot.reply_to(message, 'Что-то пошло не так. Уже чиним.')


def process_age_step(message):
    try:
        chat_id = message.chat.id
        age = message.text
        if not age.isdigit():
            msg = bot.send_message(message.chat.id, 'В ответе должны быть цифры. Сколько вам лет??')
            bot.register_next_step_handler(msg, process_age_step)
            return
        if int(age) < 18:
            msg = bot.send_message(message.chat.id, 'Доступ только для лиц старше 18 лет. \nВы должны удалить этот бот.')
            return
        user = user_dict[chat_id]
        user.age = age
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add('Мужской', 'Женский')
        markup.add("Другой")
        msg = bot.send_message(message.chat.id, 'Укажите ваш пол.', reply_markup=markup)
        bot.register_next_step_handler(msg, process_sex_step)
    except Exception as e:
        log.error(e)
        functions.call_admin(e)
        bot.reply_to(message, 'Что-то пошло не так. Уже чиним.')


def process_sex_step(message):
    try:
        chat_id = message.chat.id
        sex = message.text
        user = user_dict[chat_id]
        user.sex = sex
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Отправить', request_location = True), types.KeyboardButton('Отмена'))
        msg = bot.send_message(message.chat.id, 'Отправьте вашу геопозицию.', reply_markup=markup)
        bot.register_next_step_handler(msg, process_geo_step)
    except Exception as e:
        functions.call_admin(e)
        log.error(e)
        bot.reply_to(message, 'Что-то пошло не так. Уже чиним.')


def process_geo_step(message):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        if message.text != "Отмена":
            lat = message.location.latitude
            lng = message.location.longitude
            user.lat = lat
            user.lng = lng
        if functions.save_new_user(user, message):
            bot.send_message(chat_id, 
                f"""
Имя: {user.name}
Возраст: {str(user.age)}
Пол: {user.sex}
Вы зарегистрированы. Используйте команду /go для поиска собеседника.
                """,
                reply_markup = hideKeyboard)
            log.info(f"Registration: {chat_id} {user.name} {str(user.age)} {user.sex} ")
    except Exception as e:
        functions.call_admin(e)
        log.error(e)
        bot.reply_to(message, 'Что-то пошло не так. Уже чиним.')


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    companion = db.get_companion(message.chat.id)
    print(f'co:{companion}')
    user = db.get_user_data(message.chat.id)
    print(f'user:{user}')
    if not user:
        bot.send_message(message.chat.id, 
            f'Используйте /new для регистрации. Всего 3 вопроса.', 
            reply_markup = hideKeyboard)
    if message.text == 'Отказ':
        db.drop_companion(user[0])
        db.drop_companion(companion[0])
        bot.send_message(companion[0], 
            f'{user[1]} прекратил общение с вами. Найдите нового собеседника командой /go', 
            reply_markup = hideKeyboard)
        bot.send_message(user[0], 
            f'Вы больше не сможете общаться с {companion[1]}. Найдите нового собеседника командой /go', 
            reply_markup = hideKeyboard)
        return
    if companion:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton('Контакт', request_contact = True), types.KeyboardButton('Завершить'))
        bot.send_message(companion[0], f'*{user[1]}*:\n{message.text}', reply_markup = markup, parse_mode = 'markdown')
        #bot.send_message(user[0], f'*{user[1]}*:\n{message.text}', reply_markup = markup, parse_mode = 'markdown')
        log.info(f'From: {user[0]} To: {companion[0]} Msg: {message.text}')
    else:
        bot.send_message(message.chat.id, "Вы не выбрали собеседника. Используйте /go команду.")


# CONTACT
@bot.message_handler(content_types=['contact'])
def contact(message):
    if message.contact is not None:
        companion = db.get_companion(message.chat.id)
        log.info(f'From: {message.chat.id} To: {companion[0]} Co: {message.contact}')
        bot.send_contact(chat_id = companion[0], phone_number = message.contact.phone_number, first_name = message.contact.first_name)


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Build ssl context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

# Start aiohttp server
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)
