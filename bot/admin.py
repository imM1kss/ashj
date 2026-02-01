from tkinter.font import names

from aiogram.filters import CommandStart, ADMINISTRATOR
from aiogram.filters.callback_data import CallbackData
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.utils import kb_generator, inline_generator
from config import dp, bot, router, db
from aiogram.types import Message

from db.FCM import Subject


@router.message(Command('admin'))
async def any_text_reply(message : Message) -> None:
    if int(message.chat.id) not in config.config_bot.admin_id():
        await message.answer('атата')
        return
    text_message = "Выбери действие"
    reply_markup_admin = [{'text' : 'Добавить предметы', 'callback' : 'add_subject'},
                          {'text' : 'Смотреть предметы', 'callback' : 'view_subject'},
                          {'text': 'Удалить предмет', 'callback': 'del_subject'}
                          ]
    await message.answer(text=text_message,
                         reply_markup=inline_generator(reply_markup_admin))

@router.callback_query(F.data == "add_subject")
async def add_subject_admin(callback : CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('Напиши название предмета')
    await state.set_state(Subject.name)


@router.message(Subject.name)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(name=message.text)  # сохраняем временно
    id_subject = db.ensure_subject(message.text)
    await message.answer(f"Отлично, предмет {message.text} добавлен, его id {id_subject}\n\n\n/start\n\n\n/admin")
    await state.clear()


@router.callback_query(F.data == "view_subject")
async def view_subject_admin(callback: CallbackQuery):
    await callback.message.delete()
    subjects_list = db.get_subjects()  # теперь [(id, name), ...]

    if not subjects_list:
        await callback.message.answer("Список предметов пуст.")
        return

    # Формируем сообщение
    message_subjects = ""
    for sub_id, sub_name in subjects_list:
        message_subjects += f"{sub_id}: {sub_name}\n"

    await callback.message.answer(message_subjects)



@router.callback_query(F.data == "del_subject")
async def delete_subject_admin(callback : CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer('Напиши название предмета')
    await state.set_state(Subject.id)


@router.message(Subject.id)
async def delete_process_subject(message: Message, state: FSMContext):
    try:
        id_subject = int(message.text)
    except ValueError:
        await message.answer('Id может содержать только цифры')
        await state.set_state(Subject.id)
        return
    await state.update_data(name=id_subject)  # сохраняем временно
    db.delete_subject(id_subject)
    await message.answer(f"Отлично, предмет с id {id_subject} удален\n\n\n/start\n\n\n/admin")
    await state.clear()

