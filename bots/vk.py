#imports
import asyncio
import dotenv
import random
import os
import re
from bots.vk_keyboard import VkKeyboard

from aiovk import TokenSession, API
from aiovk.longpoll import BotsLongPoll
from services.Datbase import DataBase
from typing import Optional,List,Tuple,Dict
from difflib import SequenceMatcher
from pathlib import Path

#load tokens from .env
dotenv.load_dotenv()

#const
TOKEN = os.getenv("VK_token")
GROUP_ID = os.getenv("group_id")

# function command handler
# async def command_hendler(command_text:Optional[str] = None) -> Dict:
#     # checking the command in the arg
#     if command_text is None:
#         return None
#     else:
#         # xommand_text to lower case
#         command_text = command_text.lower()
    
#     # building path to commands.json
#     current_file = Path(__file__).resolve()
#     json_path = current_file.parent.parent / "services" / "commands.json"
    
#     #getting commands from file
#     with open(json_path, 'r', encoding="utf-8") as file:
#         commands = json.load(file)

#     # necessary variables
#     best_ratio = 0
#     best_match = None

#     # circle for go throught all the names, info in the items
#     for cmd_name, cmd_info in commands.items():
#         cmd_text = cmd_info.get('text').lower() # writing a command
#         ratio = SequenceMatcher(None,command_text,cmd_text).ratio() #comparison
#         # search the best ratio
#         if ratio > best_ratio:
#             best_ratio = ratio
#             best_match = {"name":cmd_name, "admin":cmd_info['admin']}
#     # return the response
#     if best_ratio > 0.8:
#         return best_match
#     else:
#         return None

# function converter mixed names to numbers
def convert_group_name(group_name:Optional[str] = None) -> str:
    if group_name is None:
        return None
    
    result = re.sub(r'\D', '', group_name)
    return result


class VkBot:
    global TOKEN, GROUP_ID
    def __init__(self, token=TOKEN, group_id=GROUP_ID):
        self.token = token
        self.group_id = group_id
    
    async def _connect_api(self) -> API:
        self.session = TokenSession(access_token=self.token)
        vk = API(session=self.session)
        return vk
    
    async def main_vk(self) -> None:
        vk = await self._connect_api()
        longpoll = BotsLongPoll(vk, group_id=self.group_id)
        async for event in longpoll.iter():
            if event.get("type") == "message_new":
                message = event.get("object", {}).get("message", {})
                await self.send_message(message.get("peer_id"), "123")
    
    async def send_message(self,
                           peer_id: Optional[int] = None,
                           text:Optional[str] = None,
                           keyboard:Optional[str] = None,
                           attachments:Optional[List] = None) -> None:
        if peer_id is None:
            raise ValueError("peer_id не указано")

        text = text or ""
        keyboard = keyboard or ""
        attachments = attachments or []

        vk = await self._connect_api()
        vk.messages.send(peer_id = peer_id,
                            random_id = random.randint(0, 10000),
                            message = text,
                            attachments = attachments,
                            keyboard = keyboard)


#run function -> None
async def main_vk() -> None:
    global TOKEN, GROUP_ID

    session = TokenSession(access_token=TOKEN)
    api = API(session=session)

    longpoll = BotsLongPoll(api, group_id=GROUP_ID)

    async for event in longpoll.iter():
        if event.get("type") == "message_new":
            message = event.get("object", {}).get("message", {})
            mid = message.get("conversation_message_id")
            await api.messages.delete(delete_for_all=1, cmids=mid, peer_id=message.get("peer_id"))
            
    await session.close()



    #init vk session
    # async with TokenSession(access_token=TOKEN) as session:
    #     api = API(session)
    #     # init longpoll
    #     long_poll = BotsLongPoll(api, group_id=GROUP_ID)

    #     #send message func -> None
    #     async def send_message(id:Optional[int] = None,
    #                            message:Optional[str] = None,
    #                            keyboard:Optional[str] = None,
    #                            attachments:Optional[List] = None) -> None:
    #         #transform message to "" or don't transform it
    #         message = message or ""
    #         attachments = attachments or []
    #         keyboard = keyboard or ""
    #         #if id is not defineded -> ValueError
    #         if id is None:
    #             raise ValueError("Id is not defineded")

    #         #await method vk api for send message (id,message_text,keyboard,attacments,random_id(0 -> 10000))
    #         await api.messages.send(
    #                 peer_id=id,
    #                 message=message,
    #                 keyboard = keyboard,
    #                 attachments = attachments,
    #                 random_id=random.randint(0,10000)
    #             )
        
        

        
    #     print("Бот на aiovk погнал!")

    #     # Cycle listenning events
    #     async for event in long_poll.iter():
    #         # evevnt is "new message"
    #         if event['type'] == 'message_new':
    #             message = event['object']['message'] # message object

    #             user_id = message.get('from_id') # sender's user id
    #             peer_id = message.get('peer_id') # sender's chat id 
    #             message_text = message.get('text') # text message
    #             #filter: if mention bot -> send_message else -> None
    #             if ("@schedly_test" in message_text) or ("@SchedlyBot" in message_text):

    #                 command = message_text.strip().split(" ", 1)[1] #remove "@SchedlyBot" or others
    #                 command_parts = command.split(":", 1) # getting parts of command
                    
    #                 #command_text and command_args
    #                 command_text = command_parts[0]
    #                 command_args = ""

    #                 #checking for the presence of args
    #                 if len(command_parts) > 1:
    #                     command_args = command_parts[1]

    #                 cmd = command_hendler(command_text=command_text)
    #                 DataBase = DataBase()

    #                 if cmd is not None:

    #                     cmd_name = cmd.get("name")
    #                     cmd_admin = cmd.get("admin")

    #                     if DataBase.is_admin(vk_id=user_id) >=  cmd_admin:

    #                         if  cmd_name == "join_group" and command_args:
    #                             if DataBase.ensure_group(vk_id=peer_id,
    #                                                     name=convert_group_name(group_name=command_args)):
    #                                 await send_message(id=peer_id,
    #                                                     message="Группа успешно создана!")
    #                             else:
    #                                 await send_message(id=peer_id,
    #                                                     message="Извините, но похоже, что группа была уже создана, до вас!")





#testing if run directly
if __name__ == "__main__":
    while True:
        try:
            bot = VkBot()
            asyncio.run(bot.main_vk())
        except KeyboardInterrupt:
            print("Бот выключен")
            break
        except asyncio.TimeoutError:
            print("timeout")
            continue
