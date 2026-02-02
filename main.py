
import threading
import time
import json

from parser import run_parser, get_next_day
from vkbot import run_bot, send_message


def get_hw(schedule):
    with open('data.json', 'r', encoding="utf-8") as file:
        data = json.load(file)

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
        subj_id = name2id.get(subj_name)

        if not subj_id:
            continue

        hw = data["home_work"][subj_id]

        if hw["text"]:
            text += f"\n{subj_name.capitalize()} — {hw['text']}"
        else:
            text += f"\n{subj_name.capitalize()} — нет данных"

        # добавляем фото
        if hw["src"]:
            attachments.extend(hw["src"])

    return text, attachments


def parser_pool():
    while True:
        res = run_parser()
        ndd, ndf = get_next_day()

        if res:
            text = f"РАСПИСАНИЕ на {ndd}:"

            for el in res:
                text += "\n"
                for i in el:
                    text += f"{i} "

            hw_text, hw_attachments = get_hw(res)
            text += hw_text

            send_message(
                msg=text,
                attachment=",".join(hw_attachments) if hw_attachments else None
            )

        time.sleep(600)


bot_thread = threading.Thread(target=run_bot, daemon=True)
parser_thread = threading.Thread(target=parser_pool, daemon=True)

bot_thread.start()
parser_thread.start()

bot_thread.join()
parser_thread.join()
