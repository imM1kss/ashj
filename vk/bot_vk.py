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



#run function -> None
async def main_vk() -> None:
    #init vk session
    async with TokenSession(access_token=TOKEN) as session:
        api = API(session)
        # init longpoll
        long_poll = BotsLongPoll(api, group_id=GROUP_ID)

        #send message func -> None
        async def send_message(id:Optional[int] = None,
                               message:Optional[str] = None,
                               keyboard:Optional[str] = None,
                               attachments:Optional[List] = None) -> None:
            #transform message to "" or don't transform it
            message = message or ""
            #if id is not defineded -> ValueError
            if id is None:
                raise ValueError("Id is not defineded")

            #await method vk api for send message (id,message_text,keyboard,attacments,random_id(0 -> 10000))
            await api.messages.send(
                    peer_id=id,
                    message=message,
                    keyboard = keyboard,
                    attachments = attachments,
                    random_id=random.randint(0,10000)
                )

        
        print("Бот на aiovk погнал!")

        # Cycle listenning events
        async for event in long_poll.iter():
            # evevnt is "new message"
            if event['type'] == 'message_new':
                message = event['object']['message'] # message object

                user_id = message['from_id'] # sender's user id
                peer_id = message['peer_id'] # sender's chat id 
                messagetext = message['text'] # text message

#testing if run directly
if __name__ == "__main__":
    try:
        asyncio.run(main_vk())
    except KeyboardInterrupt:
        print("Бот выключен")
