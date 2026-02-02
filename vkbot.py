import json
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random as rand
from dotenv import load_dotenv
import os

load_dotenv()

#open data.json
with open("data.json", 'r', encoding="utf-8") as file:
    data = json.load(file)

#constant values
TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = data['group_id']
PEER_ID = data['peer_id']

#standart values
msid = None
usid = None
subject = None
src = []

#vk bot api init
vk_session = VkApi(token = TOKEN)
vk_api = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

def send_message(id = PEER_ID, msg = "Void", keyboard = None, attachment=None):
    vk_api.messages.send(
        peer_id = id,
        message = msg,
        keyboard = keyboard,
        attachment=attachment,
        random_id = rand.randint(0, 100000)
    )

def edit_message(event, text, keyboard):
    vk_api.messages.edit(
        peer_id=event.object.peer_id,
        conversation_message_id=event.object.conversation_message_id,
        message=text,
        keyboard=keyboard
    )

def write_hw(name, text, src):
    with open("data.json", 'r', encoding="utf-8") as file:
        data = json.load(file)

    data['home_work'][name]['text'] = text
    data['home_work'][name]['src'] = src

    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main_keyboard():
    keyboard = VkKeyboard(inline=True)

    # 1-я строка
    keyboard.add_callback_button("Матем.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'math'})
    keyboard.add_callback_button("Физика", color=VkKeyboardColor.PRIMARY, payload={'cmd':'phys'})

    keyboard.add_line()

    # 2-я строка
    keyboard.add_callback_button("Информ.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'infm'})
    keyboard.add_callback_button("История", color=VkKeyboardColor.PRIMARY, payload={'cmd':'hist'})

    keyboard.add_line()

    # 3-я строка
    keyboard.add_callback_button("Геогр.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'geo'})
    keyboard.add_callback_button("Общество", color=VkKeyboardColor.PRIMARY, payload={'cmd':'obsh'})

    keyboard.add_line()
    keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})
    keyboard.add_callback_button("--->", color=VkKeyboardColor.POSITIVE, payload={'cmd':'next'})

    return keyboard.get_keyboard()

def next_keyboard():
    keyboard = VkKeyboard(inline=True)

    # 1-я строка
    keyboard.add_callback_button("Русский", color=VkKeyboardColor.PRIMARY, payload={'cmd':'rus'})
    keyboard.add_callback_button("Лит-ра", color=VkKeyboardColor.PRIMARY, payload={'cmd':'lit'})

    keyboard.add_line()

    # 2-я строка
    keyboard.add_callback_button("Информ.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'pe'})
    keyboard.add_callback_button("История", color=VkKeyboardColor.PRIMARY, payload={'cmd':'eng'})

    keyboard.add_callback_button("Химия", color=VkKeyboardColor.PRIMARY, payload={'cmd':'chm'})
    keyboard.add_callback_button("Биология", color=VkKeyboardColor.PRIMARY, payload={'cmd':'bio'})

    keyboard.add_line()
    keyboard.add_callback_button("<---", color=VkKeyboardColor.POSITIVE, payload={'cmd':'back'})   
    keyboard.add_callback_button("--->", color=VkKeyboardColor.POSITIVE, payload={'cmd':'next'})

    keyboard.add_line()
    keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

    return keyboard.get_keyboard()

def close_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

    return keyboard.get_keyboard()

def extract_photos(msg):
    photos = []

    for att in msg.get('attachments', []):
        if att['type'] == 'photo':
            photo = att['photo']
            owner_id = photo['owner_id']
            photo_id = photo['id']
            access_key = photo.get('access_key')

            if access_key:
                photos.append(f"photo{owner_id}_{photo_id}_{access_key}")
            else:
                photos.append(f"photo{owner_id}_{photo_id}")

    return photos

def run_bot():
    global msid, subject, usid, src
    #listen events
    for event in longpoll.listen():
            #event message
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.object['message']
                peer_id = msg['peer_id']
                print(peer_id)
                #get events only in our group
                if peer_id == PEER_ID:
                    #message handler
                    if msg.get('text', '').lower() == '/bot' and usid == None:
                        send_message(PEER_ID, "Выберите предмет", main_keyboard())
                        usid = msg['from_id']
                    elif subject != None and usid == msg["from_id"]:
                        write_hw(subject, msg.get('text', '').lower(), extract_photos(msg))
                        send_message(peer_id, 'Домашнее задание успешно добавлено', None)
                        subject = None
                        src = []
                        usid = None
                        vk_api.messages.delete(
                            peer_id = peer_id,
                            conversation_message_ids=[msid],
                            delete_for_all = True
                        )
                        msid = None
            #event callback
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                cmd = event.object.payload['cmd']
                #the menu available to tha
                if event.object.user_id == usid:
                    if cmd == "next":
                        text = "Выберите предмет:"
                        edit_message(event, text, next_keyboard())
                    elif cmd == "close":
                        usid = None
                        src = []
                        subject = None
                        edit_message(event, "Действие завершено!", None)
                    elif cmd == 'back':
                        text = "Выберите предмет:"
                        edit_message(event, text, main_keyboard())
                    else:
                        subject = cmd
                        msid = event.object.conversation_message_id
                        edit_message(event, 'Напишите Д/З и я его сразу добавлю:', close_keyboard())

                vk_api.messages.sendMessageEventAnswer(
                    event_id=event.object.event_id,
                    user_id=event.object.user_id,
                    peer_id=event.object.peer_id)