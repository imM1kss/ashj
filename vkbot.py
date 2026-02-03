import json
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random as rand
from dotenv import load_dotenv
import os
from pathlib import Path
import sqlite3

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

users = {}

#vk bot api init
vk_session = VkApi(token = TOKEN)
vk_api = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

def get_hw(schedule):
    text = "\n\nДомашнее задание:"
    attachments = []

    name2id = {
        "математика": "math",
        "физика": "phys",
        "информатика": "infm",
        "история": "hist",
        "география": "geo",
        "обществознание": "obsh",
        "русский язык": "rus",
        "литература": "lit",
        "физическая культура": "pe",
        "английский язык": "eng",
        "химия": "chm",
        "биология": "bio"
    }

    for row in schedule:
        subj_name = row[1].lower()
        print(subj_name)
        subj_id = name2id.get(subj_name)
        print(subj_id)

        if not subj_id:
            continue

        hw = data["home_work"][subj_id]

        print(hw)

        if hw["text"]:
            text += f"\n{subj_name.capitalize()} — {hw['text']}"
            print(text)
        else:
            text += f"\n{subj_name.capitalize()} — нет данных"
            print(text)

        # добавляем фото
        if hw["src"]:
            attachments.extend(hw["src"])

    return text, attachments

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


def menu_keyboard():
    keyboard = VkKeyboard(inline=True)

    keyboard.add_callback_button('Добавить', color=VkKeyboardColor.POSITIVE, payload={'cmd':'add'})
    keyboard.add_callback_button('Изменить', color=VkKeyboardColor.PRIMARY, payload={'cmd':'edit'})
    keyboard.add_callback_button('Удалить', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'remove'})
    keyboard.add_line()
    
    keyboard.add_callback_button('Расписание', color=VkKeyboardColor.SECONDARY, payload={'cmd':'schedule'})
    keyboard.add_callback_button('ДЗ', color=VkKeyboardColor.SECONDARY, payload={'cmd':'home_work'})

    keyboard.add_line()

    keyboard.add_callback_button('Закрыть', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

    return keyboard.get_keyboard()

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
    keyboard.add_callback_button("Английский", color=VkKeyboardColor.PRIMARY, payload={'cmd':'eng'})

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

def back_keyboard():
    keyboard = VkKeyboard(inline=True)
    keyboard.add_callback_button('В главное меню', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'menu'})
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
    global users, data
    #listen events
    for event in longpoll.listen():
            #event message
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.object['message']
                peer_id = msg['peer_id']
                usid = msg["from_id"]
                #get events only in our group
                if peer_id == PEER_ID:
                    #message handler
                    if msg.get('text', '').lower() in ['/bot', '/start'] and usid not in users:
                        send_message(PEER_ID, "Выберите предмет", menu_keyboard())
                        users[usid] = {"subject":None, "msid":None, "src":[], "act":None}
                        print(users)
                    elif msg['from_id'] in users:
                        if users[usid]['subject'] != None:
                            if users[usid]["act"] == "add":
                                write_hw(users[usid]['subject'], msg.get('text', '').lower(), extract_photos(msg))
                                send_message(peer_id, 'Домашнее задание успешно добавлено', None)
                            elif users[usid]["act"] == "edit":
                                send_message(PEER_ID, "Эта функция недоступна, попробуйте позже")
                            elif users[usid]["act"] == "remove":
                                write_hw(users[usid]['subject'], "", [])
                                send_message(peer_id, 'Домашнее задание успешно удалено', None)
                            users[usid]["act"] = None
                            vk_api.messages.delete(
                                peer_id = peer_id,
                                conversation_message_ids=[users[usid]['msid']],
                                delete_for_all = True
                            )
                            users.pop(usid)
                            print(users)
                    elif msg.get('text', '').lower() == "/setid" and usid == data["admin_id"]:
                        send_message(PEER_ID, "ID успешно установлен")
            #event callback
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                cmd = event.object.payload['cmd']
                #the menu available to tha
                if event.object.user_id in users:
                    if cmd == "next":
                        text = "Выберите предмет:"
                        edit_message(event, text, next_keyboard())
                    elif cmd == "close":
                        users.pop(event.object.user_id)
                        print(users)
                        edit_message(event, "Действие завершено!", None)
                    elif cmd == 'back':
                        text = "Выберите предмет:"
                        users[event.object.user_id]['subject'] = None
                        edit_message(event, text, main_keyboard())
                    elif cmd == 'menu':
                        text = "Выберите предмет:"
                        edit_message(event, text, menu_keyboard())
                    elif cmd == "schedule":
                        text = "Расписание:"
                        for row in data['last_schedule']:
                            text += "\n"
                            for el in row:
                                text += f"{el} "
                        edit_message(event, text, None)
                        users.pop(event.object.user_id)
                    elif cmd == "home_work":
                        with open("data.json", 'r', encoding='utf-8') as file:
                            data = json.load(file)
                        print(data)
                        hw_text, att = get_hw(data["last_schedule"])
                        edit_message(event, hw_text, None)
                        if att:
                            send_message(PEER_ID, "Вложение к ДЗ", None, att)
                        users.pop(event.object.user_id)
                    elif cmd == "add":
                        users[event.object.user_id]["act"] = "add"
                        edit_message(event, "Выберите предмет:", main_keyboard())
                    elif cmd == "edit":
                        users[event.object.user_id]["act"] = "edit"
                    elif cmd == "remove":
                        users[event.object.user_id]["act"] = "remove"
                    else:
                        users[event.object.user_id]['subject'] = cmd
                        users[event.object.user_id]['msid'] = event.object.conversation_message_id
                        edit_message(event, 'Напишите Д/З и я его сразу добавлю:', back_keyboard())

                vk_api.messages.sendMessageEventAnswer(
                    event_id=event.object.event_id,
                    user_id=event.object.user_id,
                    peer_id=event.object.peer_id)