
import logging

logger = logging.getLogger("vk bot")

    #импортировал все методы для ВК
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload

#импортировал остальные методы
import random as rand
import os
import json
import re
from dotenv import load_dotenv
from typing import List, Tuple, Optional
from db.Datbase import Database
from rapidfuzz import process



#загружаю переменные среды
load_dotenv()

# #открываю data.json
# with open("data.json", 'r', encoding="utf-8") as file:
#     data = json.load(file)

#постоянные значения
TOKEN = os.getenv("VK_token")
GROUP_ID = os.getenv("group_id")
# PEER_ID = data['peer_id']

#переменные для пользователей
users = {}

#инициализация api
vk_session = VkApi(token = TOKEN)
vk_api = vk_session.get_api()
upload = VkUpload(vk_session)

#инициализация отслеживания событий для бота
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# #динамическая установка значения в словаре
# def set_value(data, tag_path, value):
#     for key in tag_path[-1]:
#         data = data[key]
#     data[tag_path[-1]] = value

# #обновление data.json
# def upload_data(tag_path, value):
#     #открываем data
#     with open("data.json", 'r', encoding='utf-8') as file:
#         data = json.load(file)

#     #ставим наше значение
#     set_value(data, tag_path, value)

#     #сохраняем изменения
#     with open('data.json', "w", encoding="utf-8") as file:
#         json.dump(data, file, ensure_ascii=False, indent=4)

# #получить дз
# def get_hw():
#     with open("data.json", 'r', encoding='utf-8') as file:
#         data = json.load(file)

#     #текст и вложения
#     text = ""
#     attachments = []
#     schedule = data["last_schedule"]

#     name2id = {
#         "математика": "math",
#         "физика": "phys",
#         "информатика": "infm",
#         "история": "hist",
#         "география": "geo",
#         "обществознание": "obsh",
#         "русский язык": "rus",
#         "литература": "lit",
#         "физическая культура": "pe",
#         "иностранный язык": "eng",
#         "химия": "chm",
#         "биология": "bio"
#     }

#     #строки в рассписании
#     cnt = 0
#     for row in schedule:
#         cnt += 1
#         subj_name = row[1].lower() #название предмета
#         subj_id = name2id.get(subj_name) #id предмета

#         #если нет id
#         if not subj_id:
#             continue
#         #дз
#         hw = data["home_work"][subj_id]

#         #добавляем текст
#         if hw["text"]:
#             text += f"\n[{cnt}] {subj_name.capitalize()} ---> {hw['text']}"
        

#         # добавляем фото
#         if hw["src"]:
#             attachments.extend(hw["src"])
        

#     return text, attachments

#написать сообщение
def send_message(peer_id:Optional[int] = None,
                message:Optional[str] = None,
                keyboard:Optional[str] = None,
                attachments:Optional[List[str]] = None) -> None:
    
    if attachments is not None:
        attachment = ",".join(
        f"photo{p['owner_id']}_{p['id']}"
        for p in upload.photo_messages(attachments)
    )
    else: attachment = None

    if peer_id is None:
        raise ValueError("peer_id не указан")
    if message is None and attachments is None:
        raise ValueError("Нужно хотя-бы сообщение или вложение!")

    vk_api.messages.send(
        peer_id = peer_id,
        message = message,
        keyboard = keyboard,
        attachment=attachment,
        random_id = rand.randint(0, 100000)
    )

# #изменить сообщение
# def edit_message(event, text="None", keyboard=None):
#     vk_api.messages.edit(
#         peer_id=event.object.peer_id,
#         conversation_message_id=event.object.conversation_message_id,
#         message=text,
#         keyboard=keyboard
#     )

# #написать новое дз
# def write_hw(name, text, src):
#     with open("data.json", 'r', encoding="utf-8") as file:
#         data = json.load(file)

#     data['home_work'][name]['text'] = text
#     data['home_work'][name]['src'] = src

#     with open("data.json", "w", encoding="utf-8") as file:
#         json.dump(data, file, ensure_ascii=False, indent=4)


# def menu_keyboard():
#     keyboard = VkKeyboard(inline=True)

#     keyboard.add_callback_button('Добавить', color=VkKeyboardColor.POSITIVE, payload={'cmd':'add'})
#     keyboard.add_callback_button('Изменить', color=VkKeyboardColor.PRIMARY, payload={'cmd':'edit'})
#     keyboard.add_callback_button('Удалить', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'remove'})
#     keyboard.add_line()
    
#     keyboard.add_callback_button('Расписание', color=VkKeyboardColor.SECONDARY, payload={'cmd':'schedule'})
#     keyboard.add_callback_button('ДЗ', color=VkKeyboardColor.SECONDARY, payload={'cmd':'home_work'})

#     keyboard.add_line()

#     keyboard.add_callback_button('Закрыть', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

#     return keyboard.get_keyboard()

# def main_keyboard():
#     keyboard = VkKeyboard(inline=True)

#     # 1-я строка
#     keyboard.add_callback_button("Матем.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'math'})
#     keyboard.add_callback_button("Физика", color=VkKeyboardColor.PRIMARY, payload={'cmd':'phys'})

#     keyboard.add_line()

#     # 2-я строка
#     keyboard.add_callback_button("Информ.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'infm'})
#     keyboard.add_callback_button("История", color=VkKeyboardColor.PRIMARY, payload={'cmd':'hist'})

#     keyboard.add_line()

#     # 3-я строка
#     keyboard.add_callback_button("Геогр.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'geo'})
#     keyboard.add_callback_button("Общество", color=VkKeyboardColor.PRIMARY, payload={'cmd':'obsh'})

#     keyboard.add_line()
#     keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})
#     keyboard.add_callback_button("--->", color=VkKeyboardColor.POSITIVE, payload={'cmd':'next'})

#     return keyboard.get_keyboard()

# def next_keyboard():
#     keyboard = VkKeyboard(inline=True)

#     # 1-я строка
#     keyboard.add_callback_button("Русский", color=VkKeyboardColor.PRIMARY, payload={'cmd':'rus'})
#     keyboard.add_callback_button("Лит-ра", color=VkKeyboardColor.PRIMARY, payload={'cmd':'lit'})

#     keyboard.add_line()

#     # 2-я строка
#     keyboard.add_callback_button("Информ.", color=VkKeyboardColor.PRIMARY, payload={'cmd':'pe'})
#     keyboard.add_callback_button("Английский", color=VkKeyboardColor.PRIMARY, payload={'cmd':'eng'})

#     keyboard.add_callback_button("Химия", color=VkKeyboardColor.PRIMARY, payload={'cmd':'chm'})
#     keyboard.add_callback_button("Биология", color=VkKeyboardColor.PRIMARY, payload={'cmd':'bio'})

#     keyboard.add_line()
#     keyboard.add_callback_button("<---", color=VkKeyboardColor.POSITIVE, payload={'cmd':'back'})   
#     keyboard.add_callback_button("--->", color=VkKeyboardColor.POSITIVE, payload={'cmd':'next'})

#     keyboard.add_line()
#     keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

#     return keyboard.get_keyboard()

# def close_keyboard():
#     keyboard = VkKeyboard(inline=True)
#     keyboard.add_callback_button("Закрыть", color=VkKeyboardColor.NEGATIVE, payload={'cmd':'close'})

#     return keyboard.get_keyboard()

# def back_keyboard():
#     keyboard = VkKeyboard(inline=True)
#     keyboard.add_callback_button('В главное меню', color=VkKeyboardColor.NEGATIVE, payload={'cmd':'menu'})
#     return keyboard.get_keyboard()

# #получение фото из сообщения
# def extract_photos(msg):
#     photos = []

#     #вложения в сообщении
#     for att in msg.get('attachments', []):
#         #только фото
#         if att['type'] == 'photo':
#             photo = att['photo']
#             owner_id = photo['owner_id']
#             photo_id = photo['id']
#             access_key = photo.get('access_key')

#             if access_key:
#                 photos.append(f"photo{owner_id}_{photo_id}_{access_key}")
#             else:
#                 photos.append(f"photo{owner_id}_{photo_id}")
#     return photos

# # форматируем номер кабинета в нормальный вид
# def get_cab(line):
#     match = re.search(r'\d+', line)
#     return match.group() if match else line

def get_action_by_name(name:Optional[str] = None) -> Optional[str]:

    action_list = ["добавить","удалить","расписание","создай группу","кто я"]

    actions = {"добавить":"add","удалить":"delete","расписание":"schedule",
               "создай группу":"create_group","кто я":"who_am_i"}

    action_match = process.extractOne(name,action_list)

    if not action_match or action_match[1] < 65:
        return None
    return actions[action_match[0]]

def get_subjects_by_name(name:Optional[str] = None) -> Optional[int]:
    subjects_names = ["математика","русский","литература","физ-ра"]
    subjects = {"математика":0,"русский":1,"литература":2,"физ-ра":3}

    subject_match = process.extractOne(name,subjects_names)
    if not subject_match or subject_match[1] < 65:
        return None
    return subjects[subject_match[0]]

def get_action(command: Optional[str] = None) -> List:
    command = command.strip().lower()
    # убираем имя бота
    cmd_text = command.split(maxsplit=1)[1] if len(command.split()) > 1 else ""
    
    # пробуем найти действие
    action = get_action_by_name(cmd_text)
    
    # ищем предмет, если есть "дз по"
    if "дз по" in cmd_text:
        subject_text = cmd_text.split("дз по",1)[1].strip()
        subject = get_subjects_by_name(subject_text)
        return[action,subject]

    return [action]

# #запуск бота
def run_bot() -> None:
    global users #глобальные переменные
    logger.info("Bot start")

    #перебираем события
    for event in longpoll.listen():
            #новое сообщение
            if event.type == VkBotEventType.MESSAGE_NEW:

                msg = event.object['message'] #сообщение

                peer_id = msg['peer_id'] #id чата(для бота)
                usid = msg["from_id"] # id пользователя
                msg_text = msg.get('text', '') # текст сообщения

                data = Database()

                if msg_text.strip().lower().startswith(("шед","шэд","бот")):
                    action = get_action(msg_text)
                    send_message(peer_id=peer_id,message=f"{action}")
                    if action[0] == "create_group":
                        if data.is_admin(vk_id=usid):
                            users[usid] = {"action": action[0]}
                            send_message(peer_id=peer_id,message="Напишите пожалуйста название вашей группы:")
                        else:
                            send_message(peer_id=peer_id,message="У вас недостаточно прав!")
                    if action[0] == "who_am_i":
                        admin = data.is_admin(vk_id=usid)
                        if admin:
                            send_message(peer_id=peer_id,message="Вы администратор!")
                        else:
                            send_message(peer_id=peer_id, message="Вы пользователь!")
                elif users[usid]:
                    if users[usid]["action"] == "create_group":
                        group_name = "".join(re.findall(r'\d', msg_text))
                        group_create = data.ensure_group(name=group_name,vk_id=peer_id)
                        if group_create:
                            send_message(peer_id=peer_id,message="Группа успешно создана!")
                        else:
                            send_message(peer_id=peer_id,message="К сожалению не удалось создать группу!")
                
                
                     

                

#                 #сообщения только из нашего чата
#                 if peer_id in PEER_ID:
#                     #основная команда бота
#                     if (msg_text in ['/bot', '/start', '/ashj']) and (usid not in users):
#                         logger.info("User %s call menu %s in group %s", usid, msg_text, peer_id)
#                         send_message(peer_id, f"Выбери одно из действий:", menu_keyboard())#пишем сообщение с меню
#                         users[usid] = {"subject":None, "msid":None, "src":[], "act":None} #заносим пользователя в сессию

#                     #действия во время сессии
#                     elif usid in users:
#                         subject = users[usid]['subject']
#                         action = users[usid]["act"]

#                         #выбран предмет
#                         if subject != None:

#                             #действие "Новое"
#                             if  action == "add":
#                                 att = extract_photos(msg)
#                                 write_hw(subject, msg_text,att) # записиваем дз
#                                 send_message(peer_id, 'Домашнее задание успешно добавлено')
#                                 logger.info("User %s add home work for %s. text: %s, attacments: %s", usid, subject, msg_text, att)
                            
#                             #действие "Дополнить"
#                             elif action == "edit":
#                                 #получение нового текста
#                                 cur_text = data['home_work'][subject]['text']
#                                 new_text = f"{cur_text}\n{msg_text}"
#                                 #получение новых вложений
#                                 cur_att = data['home_work'][subject]['src']
#                                 att = extract_photos(msg)
#                                 new_att = cur_att + att
#                                 #запись дз
#                                 write_hw(subject, new_text, new_att)                               
#                                 send_message(PEER_ID, "Дз было успешно обновлено")
#                                 logger.info("User %s edit home work for %s. Text %s -> %s. Att %s -> %s", usid, subject, cur_text, new_text, cur_att, new_att)
#                             #завершение процесса
#                             action = None
#                             vk_api.messages.delete(
#                                 peer_id = peer_id,
#                                 conversation_message_ids=[users[usid]['msid']],
#                                 delete_for_all = True
#                             )
#                             users.pop(usid)
            
#             #нажатие кнопки
#             elif event.type == VkBotEventType.MESSAGE_EVENT:
#                 cmd = event.object.payload['cmd'] #определение callback
#                 peer_id = event.object['peer_id'] #id чата
#                 user_id = event.object['user_id'] # id пользователя

#                 logger.info("User %s tap key %s in group %s", user_id, cmd, peer_id)

#                 #только тем кто в сессии
#                 if user_id in users:
#                     #следующая страница
#                     if cmd == "next":
#                         text = "Выберите предмет:"
#                         edit_message(event, text, next_keyboard())
                    
#                     #завершение
#                     elif cmd == "close":
#                         users.pop(user_id)
#                         edit_message(event, "Действие завершено!")
                    
#                     #назад
#                     elif cmd == 'back':
#                         text = "Выберите предмет:"
#                         users[user_id]['subject'] = None
#                         edit_message(event, text, main_keyboard())
                    
#                     #меню
#                     elif cmd == 'menu':
#                         text = "Выберите предмет:"
#                         edit_message(event, text, menu_keyboard())
                    
#                     #расписание
#                     elif cmd == "schedule":
#                         text = "Расписание:"
                        
#                         with open('data.json', 'r', encoding='utf-8') as file:
#                             data = json.load(file)

#                         line = "-" *30
#                         text = "".join(line)
#                         for row in data['last_schedule']:
#                             cab = get_cab(row[2])
#                             text += f"\n({row[0][:1]}) {row[1]} [{cab}]"
#                         text += f"\n{line}"
                            
#                         edit_message(event, text)
#                         logger.info("User %s get schedule: %s", user_id, text)
#                         users.pop(user_id)
                    
#                     #домашнее задание
#                     elif cmd == "home_work":
#                         # получаем дз
#                         hw_text, att = get_hw()
#                         if hw_text == "":
#                             if att:
#                                 hw_text = "Текст не добавили, но есть вложение."
#                             else:
#                                 hw_text = "Не задано"
#                         edit_message(event, hw_text)
#                         logger.info("user %s get homework: text -> %s. att -> %s", user_id, hw_text, att)

#                         #высылаем вложения
#                         if att:
#                             send_message(peer_id, "Вложение к дз", attachment=att)
                        
#                         # закрываем сессию
#                         users.pop(user_id)

#                     #новое
#                     elif cmd == "add":
#                         users[user_id]["act"] = "add"
#                         edit_message(event, "Выберите предмет:", main_keyboard())
                    
#                     #дополнить
#                     elif cmd == "edit":
#                         edit_message(event, "Выберите предмет:", main_keyboard())
#                         users[user_id]["act"] = "edit"
                    
#                     #удалить
#                     elif cmd == "remove":
#                         edit_message(event, "Выберите предмет:", main_keyboard())
#                         users[user_id]["act"] = "remove"
                    
#                     #остальное
#                     else:
#                         users[user_id]['subject'] = cmd #получение предмета
#                         users[user_id]['msid'] = event.object.conversation_message_id #получение id сообщения

#                         #алгоритм удаления дз
#                         if users[user_id]["act"] == "remove":
#                             logger.info("Homework for %s was removed by %s in group %s", users[user_id]['subject'], user_id, peer_id)
#                             write_hw(users[user_id]['subject'], "", [])
#                             edit_message(event, 'Дз успешно удалено', None)
#                             users.pop(user_id)

#                         #добавление дз
#                         else:
#                             edit_message(event, 'Напиши дз и я его сразу добавлю:', back_keyboard())

#                 #важная штука
#                 vk_api.messages.sendMessageEventAnswer(
#                     event_id=event.object.event_id,
#                     user_id=user_id,
#                     peer_id=peer_id)