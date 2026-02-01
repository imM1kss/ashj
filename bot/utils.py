from calendar import firstweekday
from unittest import findTestCases

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config


def kb_generator(buttons:list, user_telegram_id: int):
    """"
    Принимает на вход список buttons в котором лежит текст кнопки
    Создает обычную клавиатуру
    """
    kb_list = []
    for button in buttons:
        kb_list.append([KeyboardButton(text=button)])

    """if str(user_telegram_id) in config.config_bot.admin_id():
        kb_list.append([KeyboardButton(text="⚙️ Админ панель")])"""

    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard

def inline_generator(buttons:list[dict]):
    """"
    Принимает на вход список buttons в котором лежит callback_data:text в dict форме
    buttons = [
    {"text": "Да", "callback": "yes"},
    {"text": "Нет", "callback": "no"},
    ]
    создает инлайн клавиатуру
    """

    builder = InlineKeyboardBuilder()

    for button in buttons:
        builder.button(
            text=button["text"],
            callback_data=button["callback"]
        )

    builder.adjust(2)  # по кнопке в строке
    return builder.as_markup()