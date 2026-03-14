#imports
import asyncio
import dotenv
import os
import random
import json
from vk.vk_keyboard import VkKeyboard

from aiovk import TokenSession, API
from aiovk.longpoll import BotsLongPoll
from data.Datbase import Database
from typing import Optional,List,Tuple,Dict

#load tokens from .env
dotenv.load_dotenv()

#constatnts
TOKEN = os.getenv("VK_token")
GROUP_ID = os.getenv("group_id")

# send message func -> None
async def send_message(id: Optional[int] = None,
                       message: Optional[str] = None,) -> None:
    pass

#run function -> None
async def main_vk() -> None:
    #init vk session
    async with TokenSession(access_token=TOKEN) as session:
        api = API(session)
        # init longpoll
        long_poll = BotsLongPoll(api, group_id=GROUP_ID)

        print("Бот на aiovk погнал!")

        # Цикл прослушки событий
        async for event in long_poll.iter():
            # Проверяем, что это новое сообщение
            if event['type'] == 'message_new':
                message = event['object']['message']
                user_id = message['from_id']
                peer_id = message['peer_id']
                messagetext = message['text']

                # Отвечаем тем же текстом
                await api.messages.send(
                    peer_id=peer_id,
                    message=f"Эхо: {messagetext}",
                    random_id=0
                )

if __name__ == "__main__":
    try:
        asyncio.run(main_vk())
    except KeyboardInterrupt:
        print("Бот выключен")
