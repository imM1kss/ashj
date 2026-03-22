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
from difflib import SequenceMatcher
from pathlib import Path

#load tokens from .env
dotenv.load_dotenv()

#constatnts
TOKEN = os.getenv("VK_token")
GROUP_ID = os.getenv("group_id")

def command_hendler(command_text:Optional[str] = None) -> Tuple(str,bool):
    if command_text is None:
        return None
    else:
        command_text = command_text.lower()
    
    print(command_text)
    
    current_file = Path(__file__).resolve()

    json_path = current_file.parent.parent / "data" / "commands.json"
    
    with open(json_path, 'r', encoding="utf-8") as file:
        commands = json.load(file)
    
    print(commands)

    best_ratio = 0
    best_match = None

    for cmd_name, cmd_info in commands.items():
        cmd_text = cmd_info['text'].lower()
        print(cmd_text)
        ratio = SequenceMatcher(None,command_text,cmd_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = (cmd_name,cmd_info["admin"])
    print(best_ratio)
    if best_ratio > 0.8:
        return best_match
    else:
        return None
    



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
            attachments = attachments or []
            keyboard = keyboard or ""
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
                message_text = message['text'] # text message
                #filter: if mention bot -> send_message else -> None
                if ("@schedly_test" in message_text) or ("@SchedlyBot" in message_text):
                    command = message_text.split(" ", 1)[1]
                    command_text = command.split(":", 1)[0]
                    data = Database()




#testing if run directly
if __name__ == "__main__":
    try:
        asyncio.run(main_vk())
    except KeyboardInterrupt:
        print("Бот выключен")
