from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram import F
from aiogram.types import CallbackQuery

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils import kb_generator, inline_generator
from config import dp, bot, router
from aiogram.types import Message

@router.message(CommandStart())
async def any_text_reply(message : Message) -> None:
    await message.answer(text=f"<strong>Привет!</strong>\nЯ бот -- дневник.\n<strong>Давай внесем твои оценки</strong>",
                         reply_markup=inline_generator([{'text' : 'Смотреть оценки', 'callback' : 'view_scors'},
                                        {'text' : 'Добавлять оценки', 'callback' : 'add_scors'}]))

@router.callback_query(F.data == "add_scors")
async def add_scors_user(callback : CallbackQuery):
    await callback.message.delete()
    await callback.message.answer('Добавляй оценки')


@router.callback_query(F.data == "view_scors")
async def view_scors_user(callback : CallbackQuery):
    await callback.message.delete()
    await callback.message.answer('Смоти оценки')