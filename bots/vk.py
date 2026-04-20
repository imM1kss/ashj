import asyncio
from services.config_vk import bot
from vkbottle import BaseStateGroup
import re
from services.Datbase import DataBase

data = DataBase()

def convert_group_name(group_name:str = None) -> str:
    if group_name is None:
        return None
    
    result = re.sub(r'\D', '', group_name)
    return result

class ServeyState(BaseStateGroup):
    JOIN = "join"

@bot.on.chat_message(func=lambda m: m.text and "бот" in m.text.lower())
async def start_message(message):
    
    if "привяжи" in message.text.lower():
        await bot.state_dispenser.set(message.peer_id, ServeyState.JOIN)
        await message.answer("Напиши свою группу")

@bot.on.chat_message(state=ServeyState.JOIN)
async def join_message(message):
    group_name = convert_group_name(message.text)
    if data.ensure_group(name=group_name, vk_id=message.peer_id):
        await message.answer(f"Группа привязана {group_name}")
        await bot.state_dispenser.delete(message.peer_id)

bot.run_forever()