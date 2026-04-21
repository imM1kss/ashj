import asyncio
from services.config_vk import bot
from vkbottle import BaseStateGroup
from vkbottle.bot import Message, MessageEvent
import re
from services.Datbase import DataBase
from typing import Optional, List, Dict, Tuple
from docx import Document
from vkbottle import Keyboard, KeyboardButtonColor, Callback, GroupEventType
from math import ceil
from random import randint

data = DataBase()

#const
ITEMS_PER_PAGE = 6

def convert_group_name(group_name:str = None) -> str:
    if group_name is None:
        return None
    
    result = re.sub(r'\D', '', group_name)
    return result

class ServeyState(BaseStateGroup):
    JOIN = "join"

def get_groups() -> List:
    doc = Document("schedule.docx")
    groups = []

    if not doc.tables:
        return None
    
    table = doc.tables[0]
    data = DataBase()

    for row in table.rows:
        cells = clean([cell.text.strip() for cell in row.cells])

        if len(cells) == 4:
                groups.append(convert_group_name(cells[0]))
        elif len(cells) > 4:
            groups.append(convert_group_name(cells[1]))
    
    return clean(groups)


def clean(items:List) -> List:
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result

def join_kb(page:int) -> Keyboard:
    kb = Keyboard(inline=True)

    names = get_groups()

    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    length = len(names)

    if max([start_idx, end_idx, length-1]) != (length-1):
        return None
    
    cur_names = names[start_idx:end_idx]

    for i, name in enumerate(cur_names):
        kb.add(
            Callback(name, payload={"act":"select_name", "name":name}),
            color=KeyboardButtonColor.PRIMARY
        )

        if (i + 1) % 2 == 0 and (i + 1) != len(cur_names):
            kb.row()
        
    kb.row()

    total_page = ceil(length/ITEMS_PER_PAGE)
    if page > 0:
        kb.add(
            Callback("<- Назад", payload={"act":"change_page", "page":page-1}),
            color=KeyboardButtonColor.SECONDARY
        )
    
    if (page + 1) < total_page:
        kb.add(
            Callback("Вперёд ->", payload={"act":"change_page", "page":page+1}),
            color=KeyboardButtonColor.SECONDARY
        )
    
    kb.row()

    kb.add(
        Callback("Закрыть", payload={"act":"close"}),
        color=KeyboardButtonColor.NEGATIVE
    )
    
    return kb

def confirm_adm_kb(name:str, peer_id:int) -> Keyboard:
    kb = Keyboard(inline=True)

    kb.add(
        Callback("Нет", payload={"act":"rejected","name":name, "peer_id":peer_id}),
        color=KeyboardButtonColor.NEGATIVE
    )

    kb.add(
        Callback("Да", payload={"act":"accepted","name":name, "peer_id":peer_id}),
        color=KeyboardButtonColor.POSITIVE
    )

    return kb



@bot.on.chat_message(func=lambda m: m.text and "бот" in m.text.lower())
async def start_message(message: Message):
    
    if "привяжи" in message.text.lower():
        keyboard = join_kb(0)
        await bot.api.messages.send(peer_id=message.peer_id,
                                    random_id=randint(0,10000),
                                    keyboard=keyboard,
                                    message="Выберите группу")
        await bot.api.messages.delete(peer_id=message.peer_id,
                                      cmids=[message.conversation_message_id],
                                      delete_for_all=True)

@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def handle_keyboard_events(event: MessageEvent):
    payload = event.object.payload
    user_id = event.object.user_id

    users = await bot.api.users.get(user_ids=[user_id])
    user = users[0]
    user_link = f"[id{user_id}|{user.first_name}{user.last_name}]"

    peer_id = event.object.peer_id
    
    if not payload:
        return
        
    # 1. Если нажали на стрелочку
    if payload.get("act") == "change_page":
        new_page = payload.get("page")
        
        # Редактируем сообщение: подменяем старую клавиатуру на новую
        await event.edit_message(
            message=f"Страница {new_page + 1}",
            keyboard=join_kb(page=new_page)
        )
        
    # 2. Если нажали на само имя
    elif payload.get("act") == "select_name":
        name = payload.get("name")

        await bot.api.messages.delete(
            peer_id=event.object.peer_id,
            cmids=[event.object.conversation_message_id],
            delete_for_all=True
        )

        is_create = None

        if data.get_group_id(name=name) is not None:
            await event.show_snackbar("Извините, но данная группа уже зарегистрирована!")
            is_create = False
        else:
            is_create = True
            await event.show_snackbar(f"Группа {name} на рассмотрении у администратора")
        
        admins = data.get_admins()
        for Id in admins:
            vk_id = data.get_user_vk_id(user_id=Id)

            if vk_id:
                if is_create is False:
                    await bot.api.messages.send(
                        user_id=vk_id,
                        random_id=randint(0,10000),
                        message=f"Пользователь {user_link} пытался присоеденить группу {name} к peer_id: {peer_id}"
                    )
                elif is_create is True:
                    await bot.api.messages.send(
                        user_id=vk_id,
                        random_id = randint(0,10000),
                        message = f"Пользователь {user_link} хочет создать группу {name} с peer_id: {peer_id}",
                        keyboard=confirm_adm_kb(name=name, peer_id=peer_id)
                    )
    elif payload.get("act") == "rejected":
        pl_peer_id = payload.get("peer_id")
        name = payload.get("name")
        
        await bot.api.messages.send(peer_id=pl_peer_id,
                                    message=f"Вам отказано в привязке вашего чата к группе {name}",
                                    random_id=randint(0,100000))
        await bot.api.messages.delete(
            peer_id = peer_id,
            delete_for_all=True,
            cmids=[event.object.conversation_message_id]
        )



    
    elif payload.get("act") == "close":
        
        await bot.api.messages.delete(
            peer_id=event.object.peer_id,
            cmids=[event.object.conversation_message_id],
            delete_for_all=True
        )

        await event.show_snackbar("Меню закрыто")
        
        

bot.run_forever()