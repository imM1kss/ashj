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

def convert_group_name(group_name:Optional[str] = None) -> str:
    if group_name is None:
        return None
    
    result = re.sub(r'\D', '', group_name)
    return result

def close_keyboard() -> str:
    keyboard = VkKeyboard(inline=True)

    keyboard.add_callback_button(label="Закрыть", color="negative", payload={"call":"close"})

    return keyboard.get_keyboard()

class VkBot:
    global TOKEN, GROUP_ID
    def __init__(self, token=TOKEN, group_id=GROUP_ID):
        self.token = token
        self.group_id = group_id
        self.data = DataBase()
        self.actions = {}
        self.groups = {}
    
    async def _connect_api(self) -> API:
        session = TokenSession(access_token=self.token)
        vk = API(session=session)
        return vk, session
    
    async def run(self) -> None:
        try:
            vk, session = await self._connect_api()
            longpoll = BotsLongPoll(vk, group_id=self.group_id)

            async for event in longpoll.iter():
                if event.get("type") == "message_new":
                    message = event.get("object", {}).get("message", {})
                    peer_id = message.get('peer_id')
                    cmid = message.get('conversation_message_id')
                    text = message.get('text').strip().lower()
                    from_id = message.get('from_id')
                    
                    if self.groups.get(peer_id) is None:
                        self.groups[peer_id] = {'user_cmid':cmid,'bot_cmid':None}
                    
                    if cmid - self.groups.get(peer_id, {}).get('user_cmid') > 1:
                        self.groups[peer_id]['bot_cmid'] = cmid - 1
                    
                    self.groups[peer_id]['user_cmid'] = cmid

                    print(self.groups[peer_id]['user_cmid'])
                    print(self.groups[peer_id]['bot_cmid'])
                    
                    if any(word in text.lower() for word in ['@schedlybot','@schedly_test']):
                        text = text.split(" ",1)[1]
                        if "привязать" in text.lower():
                            self.actions[from_id] = "join"
                            await self.delete_message(peer_id=peer_id, cmids=cmid)
                            await self.send_message(peer_id=peer_id, text="Укажите название группы:",
                                                    keyboard=close_keyboard(), silent=True)
                    
                    elif self.actions.get(from_id):
                        if self.actions.get(from_id) == "join":
                            print(self.groups.get(peer_id,{}).get('bot_cmid'))
                            await self.delete_message(peer_id=peer_id, cmids=cmid)
                            # await vk.messages.edit(peer_id=peer_id, message = "Группа успешно привязана!",
                            #                        cmids = self.groups.get(peer_id,{}).get('bot_cmid'))
                            await self.delete_message(peer_id=peer_id, 
                                                      cmids=self.groups.get(peer_id,{}).get('bot_cmid'),
                                                      delay=30)
                            group_name = convert_group_name(text)
                            self.actions.pop(from_id, None)
                            print(group_name)



                elif event.get('type') == "message_event":
                    message = event.get("object",{})
                    call = message.get('payload', {}).get('call')
                    user_id = message.get('user_id')
                    cmid = message.get("conversation_message_id")
                    peer_id = message.get("peer_id")

                    if call == "close":
                        self.actions.pop(user_id, None)
                        await self.delete_message(peer_id=peer_id, cmids=cmid)




                    
        finally:
            await session.close()
    
    async def send_message(self,
                           peer_id: Optional[int] = None,
                           text:Optional[str] = None,
                           keyboard:Optional[str] = None,
                           attachments:Optional[List] = None,
                           silent:Optional[bool] = None) -> None:
        try:
            if peer_id is None:
                raise ValueError("peer_id не указано")

            text = text or ""
            keyboard = keyboard or ""
            attachments = attachments or []
            silent = silent or False

            vk, session = await self._connect_api()
            await vk.messages.send(peer_id = peer_id,
                                random_id = random.randint(0, 10000),
                                message = text,
                                attachments = attachments,
                                keyboard = keyboard,
                                disable_mentions = 1,
                                silent = silent)
        finally:
            await session.close()
    
    async def delete_message(self,
                     peer_id: Optional[int] = None,
                     cmids: Optional[List] = None,
                     delay: Optional[int] = 0):
        try:
            if (peer_id is None) or (cmids is None):
                raise ValueError("peer_id или cmids не указано")
            
            vk, session = await self._connect_api()
            await asyncio.sleep(delay=delay)
            await vk.messages.delete(peer_id=peer_id, cmids=cmids,
                                        delete_for_all = 1)
        finally:
            await session.close()


#testing if run directly
if __name__ == "__main__":
    while True:
        try:
            bot = VkBot()
            asyncio.run(bot.run())
        except KeyboardInterrupt:
            print("Бот выключен")
            break
        except asyncio.TimeoutError:
            print("timeout")
            continue
