import asyncio
import aiofiles
import logging
import os

from aiogram import Bot, Dispatcher, types, md
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import exceptions, executor

from functions import broadcaster, save_new_user, get_total_users, select_companion


API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

logging.basicConfig(filename="bot.log", level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer("Hi!\nDo you want some sex, {username}?"
        .format(username=message.from_user.first_name))


@dp.message_handler(commands=['go'])
async def send_welcome(message: types.Message):
    """
    Select companion
    """
    companion = select_companion(message.from_user.id)
    if companion:
        await message.answer("We found for you: {name}, {age} years old, {gender}, {lang}"
            .format(name=companion[1],age=companion[2],gender=companion[3],lang=companion[4]))
    else:
        await message.answer("Companion not found")


@dp.message_handler(commands=['stat'])
async def send_welcome(message: types.Message):
    """
    Show statistic
    """
    total_users = get_total_users()
    await message.answer(md.text(
        md.text(md.bold('Count of users')),
        md.text('Total:', total_users['Total']),
        md.text('Male:', total_users['Male']),
        md.text('Female:', total_users['Female']),
        sep='\n',
    ))


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message, state: FSMContext):
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = await broadcaster()
    log.info(f"{answer_message} today statistic.")
    async with state.proxy() as proxy:
        await message.answer(f' {proxy}')

@dp.message_handler(state='*', commands=['log'])
async def view_log(message: types.Message, state: FSMContext):
    """
    Отправляет log file
    """
    async with aiofiles.open("bot.log", "r") as f:
        log_text = await f.read()
        await bot.send_message(
            message.chat.id,
            log_text
        )


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'
    location = State()


@dp.message_handler(commands='new')
async def cmd_start(message: types.Message):
    """
    Add or edit personal info
    """
    # Set state
    await Form.name.set()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(message.from_user.first_name)
    markup.add("Cancel")
    await message.answer("Hi there! What's your name?", reply_markup=markup)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.answer('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.answer("How old are you?", reply_markup=types.ReplyKeyboardRemove())


# Check age. Age gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """
    If age is invalid
    """
    return await message.answer("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if int(message.text) < 18:
        # Cancel state and inform user about it
        await state.finish()
        # And remove keyboard (just in case)
        return await message.answer('Only 18+.', reply_markup=types.ReplyKeyboardRemove())

    # Update state and data
    await Form.next()
    await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other")

    await message.answer("What is your gender?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Male", "Female", "Other"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.answer("Bad gender name. Choose your gender from the keyboard.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await Form.next()
    async with state.proxy() as data:
        data['gender'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Hi! Nice to meet you,', md.bold(data['name'])),
                md.text('Age:', md.code(data['age'])),
                md.text('Gender:', data['gender']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
        await save_new_user(message.from_user.id, data, message)


    # Finish conversation
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
