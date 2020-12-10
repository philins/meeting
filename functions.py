import asyncio
import datetime
import logging
import os

from aiogram import Bot, Dispatcher, types, md
from aiogram.utils import exceptions

import db


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

logging.basicConfig(filename="bot.log", level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)


async def select_companion(user_id: int):
    cursor = db.get_cursor()
    cursor.execute("""
        SELECT * FROM users
        WHERE id!=?
        AND companion_id is null
        ORDER BY RANDOM()
        LIMIT 1;""", (user_id,))
    companion = cursor.fetchone()
    if companion:
        log.info(f"Companion [ID:{companion[0]}]: found")
        db.set_companion(user_id, companion[0])
        db.set_companion(companion[0], user_id)
        cursor.execute("""
            SELECT * FROM users
            WHERE id=?
            LIMIT 1;""", (user_id,))
        user = cursor.fetchone()
        msg = "{name}, {age} years old, {gender}, {lang} want to talk with you"\
            .format(name=user[1],age=user[2],gender=user[3],lang=user[4])
        await send_message(companion[0], msg)
        return companion
    return False

def get_total_users():
    out = {}
    cursor = db.get_cursor()
    cursor.execute("SELECT count(*) FROM users;")
    out['Total'] = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM users WHERE gender='Male';")
    out['Male'] = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM users WHERE gender='Female';")
    out['Female'] = cursor.fetchone()[0]
    return out


async def save_new_user(id: int, data: dict, message: types.Message):
    try:
        db.insert("users", {
            "id": id,
            "name": data['name'],
            "age": data['age'],
            "gender": data['gender'],
            "lang": check_language(message),
            "created": _get_now_formatted()
        })
    except Exception as Argument:
        log.exception(f"Savind [ID:{id}]: error")
    else:
        log.info(f"Savind [ID:{id}]: success")
        await bot.send_message(
            message.chat.id,
            "Saved"
        )



def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_language(message: types.Message) -> str:
    return message.from_user.locale.language

def get_users():
    """
    Return users list
    In this example returns some random ID's
    """
    yield from (114012108, 123456789)

async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcaster() -> int:
    """
    Simple broadcaster
    :return: Count of messages
    """
    count = 0
    try:
        for user_id in get_users():
            if await send_message(user_id, '<b>Hello!</b>'):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        log.info(f"{count} messages successful sent.")

    return count
