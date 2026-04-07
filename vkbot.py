#импортировал все методы для ВК
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

#импортировал остальные методы
import random as rand
import os
import json
import re
from dotenv import load_dotenv

#загружаю переменные среды
load_dotenv()

#открываю data.json
with open("data.json", 'r', encoding="utf-8") as file:
    data = json.load(file)

#постоянные значения
TOKEN = os.getenv("VK_token")
GROUP_ID = os.getenv("group_id")
PEER_ID = data['peer_id']

#переменные для пользователей
users = {}

#инициализация api
vk_session = VkApi(token = TOKEN)
vk_api = vk_session.get_api()

#инициализация отслеживания событий для бота
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

#динамическая установка значения в словаре
def set_value(data, tag_path, value):
    for key in tag_path[-1]:
        data = data[key]
    data[tag_path[-1]] = value

#обновление data.json
def upload_data(tag_path, value):
    #открываем data
    with open("data.json", 'r', encoding='utf-8') as file:
        data = json.load(file)

    #ставим наше значение
    set_value(data, tag_path, value)

    #сохраняем изменения
    with open('data.json', "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

#получить дз
def get_hw():
    with open("data.json", 'r', encoding='utf-8') as file:
        data = json.load(file)

    #текст и вложения
    text = ""
    attachments = []
    schedule = data["last_schedule"]

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
        "иностранный язык": "eng",
        "химия": "chm",
        "биология": "bio"
    }

    #строки в рассписании
    cnt = 0
    for row in schedule:
        cnt += 1
        subj_name = row[1].lower() #название предмета
        subj_id = name2id.get(subj_name) #id предмета

        #если нет id
        if not subj_id:
            continue
        #дз
        hw = data["home_work"][subj_id]

        #добавляем текст
        if hw["text"]:
            text += f"\n[{cnt}] {subj_name.capitalize()} ---> {hw['text']}"
        

        # добавляем фото
        if hw["src"]:
            attachments.extend(hw["src"])
        

    return text, attachments

#написать сообщение
def send_message(id = PEER_ID, msg="None", keyboard = None, attachment=None):
    vk_api.messages.send(
        peer_id = id,
        message = msg,
        keyboard = keyboard,
        attachment=attachment,
        random_id = rand.randint(0, 100000)
    )

#изменить сообщение
def edit_message(event, text="None", keyboard=None):
    vk_api.messages.edit(
        peer_id=event.object.peer_id,
        conversation_message_id=event.object.conversation_message_id,
        message=text,
        keyboard=keyboard
    )

#написать новое дз
def write_hw(name, text, src):
    with open("data.json", 'r', encoding="utf-8") as file:
        data = json.load(file)

    data['home_work'][name]['text'] = text
    data['home_work'][name]['src'] = src

    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


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

#получение фото из сообщения
def extract_photos(msg):
    photos = []

    #вложения в сообщении
    for att in msg.get('attachments', []):
        #только фото
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

# форматируем номер кабинета в нормальный вид
def get_cab(line):
    match = re.search(r'\d+', line)
    return match.group() if match else line

#запуск бота
def run_bot():
    global users #глобальные переменные

    #перебираем события
    for event in longpoll.listen():
            #новое сообщение
            if event.type == VkBotEventType.MESSAGE_NEW:

                msg = event.object['message'] #сообщение

                peer_id = msg['peer_id'] #id чата(для бота)
                usid = msg["from_id"] # id пользователя
                msg_text = msg.get('text', '') # текст сообщения

                #сообщения только из нашего чата
                if peer_id in PEER_ID:
                    #основная команда бота
                    if (msg_text in ['/bot', '/start', '/ashj']) and (usid not in users):
                        send_message(peer_id, f"Этот сервис временно недоступен, в связи  с техническими неполадками! Мы обязательно сообщим, как все уладится.")#пишем сообщение с меню
            #             users[usid] = {"subject":None, "msid":None, "src":[], "act":None} #заносим пользователя в сессию

            #         #действия во время сессии
            #         elif usid in users:
            #             subject = users[usid]['subject']
            #             action = users[usid]["act"]

            #             #выбран предмет
            #             if subject != None:

            #                 #действие "Новое"
            #                 if  action == "add":
            #                     write_hw(subject, msg_text, extract_photos(msg)) # записиваем дз
            #                     send_message(peer_id, 'Домашнее задание успешно добавлено')
                            
            #                 #действие "Дополнить"
            #                 elif action == "edit":
            #                     #получение нового текста
            #                     cur_text = data['home_work'][subject]['text']
            #                     new_text = f"{cur_text}\n{msg_text}"
            #                     #получение новых вложений
            #                     cur_att = data['home_work'][subject]['src']
            #                     att = extract_photos(msg)
            #                     new_att = cur_att + att
            #                     #запись дз
            #                     write_hw(subject, new_text, new_att)                               
            #                     send_message(PEER_ID, "Дз было успешно обновлено")
            #                 #завершение процесса
            #                 action = None
            #                 vk_api.messages.delete(
            #                     peer_id = peer_id,
            #                     conversation_message_ids=[users[usid]['msid']],
            #                     delete_for_all = True
            #                 )
            #                 users.pop(usid)
            
            # #нажатие кнопки
            # elif event.type == VkBotEventType.MESSAGE_EVENT:
            #     cmd = event.object.payload['cmd'] #определение callback
            #     peer_id = event.object['peer_id'] #id чата
            #     user_id = event.object['user_id'] # id пользователя

            #     #только тем кто в сессии
            #     if user_id in users:
            #         #следующая страница
            #         if cmd == "next":
            #             text = "Выберите предмет:"
            #             edit_message(event, text, next_keyboard())
                    
            #         #завершение
            #         elif cmd == "close":
            #             users.pop(user_id)
            #             edit_message(event, "Действие завершено!")
                    
            #         #назад
            #         elif cmd == 'back':
            #             text = "Выберите предмет:"
            #             users[user_id]['subject'] = None
            #             edit_message(event, text, main_keyboard())
                    
            #         #меню
            #         elif cmd == 'menu':
            #             text = "Выберите предмет:"
            #             edit_message(event, text, menu_keyboard())
                    
            #         #расписание
            #         elif cmd == "schedule":
            #             text = "Расписание:"
                        
            #             with open('data.json', 'r', encoding='utf-8') as file:
            #                 data = json.load(file)

            #             line = "-" *30
            #             text = "".join(line)
            #             for row in data['last_schedule']:
            #                 cab = get_cab(row[2])
            #                 text += f"\n({row[0][:1]}) {row[1]} [{cab}]"
            #             text += f"\n{line}"
                            
            #             edit_message(event, text)
            #             users.pop(user_id)
                    
            #         #домашнее задание
            #         elif cmd == "home_work":
            #             # получаем дз
            #             hw_text, att = get_hw()
            #             if hw_text == "":
            #                 if att:
            #                     hw_text = "Текст не добавили, но есть вложение."
            #                 else:
            #                     hw_text = "Не задано"
            #             edit_message(event, hw_text)

            #             #высылаем вложения
            #             if att:
            #                 send_message(peer_id, "Вложение к дз", attachment=att)
                        
            #             # закрываем сессию
            #             users.pop(user_id)

            #         #новое
            #         elif cmd == "add":
            #             users[user_id]["act"] = "add"
            #             edit_message(event, "Выберите предмет:", main_keyboard())
                    
            #         #дополнить
            #         elif cmd == "edit":
            #             edit_message(event, "Выберите предмет:", main_keyboard())
            #             users[user_id]["act"] = "edit"
                    
            #         #удалить
            #         elif cmd == "remove":
            #             edit_message(event, "Выберите предмет:", main_keyboard())
            #             users[user_id]["act"] = "remove"
                    
            #         #остальное
            #         else:
            #             users[user_id]['subject'] = cmd #получение предмета
            #             users[user_id]['msid'] = event.object.conversation_message_id #получение id сообщения

            #             #алгоритм удаления дз
            #             if users[user_id]["act"] == "remove":
            #                 write_hw(users[user_id]['subject'], "", [])
            #                 edit_message(event, 'Дз успешно удалено', None)
            #                 users.pop(user_id)

            #             #добавление дз
            #             else:
            #                 edit_message(event, 'Напиши дз и я его сразу добавлю:', back_keyboard())

            #     #важная штука
            #     vk_api.messages.sendMessageEventAnswer(
            #         event_id=event.object.event_id,
            #         user_id=user_id,
            #         peer_id=peer_id)