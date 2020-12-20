import asyncio
import datetime
import logging
import os
import sqlite3
import telebot
#from aiogram import Bot, Dispatcher, types, md
#from aiogram.utils import exceptions

import db


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
ADMIN = 114012108

#logging.basicConfig(filename="bot.log", level=logging.INFO)
#log = logging.getLogger(__name__)
log = telebot.logger

bot = telebot.TeleBot(API_TOKEN)


def select_companion(user_id: int):
    """
    Рукопожатие
    """
    companion = db.find_companion(user_id)
    if companion:
        log.info(f"Companion [ID:{companion[0]}]: found")
        db.set_companion(user_id, companion[0])
        db.set_companion(companion[0], user_id)
        user = db.get_user_data(user_id)
        bot.send_message(companion[0], 
                f"""
С вами хочет пообщаться: {user[1]}
Возраст: {user[2]}
Пол {user[3]}
Язык {user[4]}""")

        return companion
    return False

def get_total_users() -> str:
    total_users = db.get_total_users()
    print(total_users)
    data = ''
    for key, val in total_users.items():
        if key == 'total': continue
        data += f'{key}: {val}\n'
    return f"*Count of users: {total_users['total']}*\n" + data


def save_new_user(user, message) -> bool:
    try:
        db.insert("users", {
            "id": message.from_user.id,
            "name": user.name,
            "age": user.age,
            "gender": user.sex,
            "lat": user.lat,
            "lng": user.lng,
            "lang": check_language(message),
            "created": _get_now_formatted()
        })
    except Exception as e:
        call_admin(e)
        log.exception(f"Savind error")
        return False
    else:
        log.info(f"Savind success")
        return True



def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_language(message) -> str:
    return message.from_user.language_code


def call_admin(e):
    bot.send_message(ADMIN, e)