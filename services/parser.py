#imports
import os
import requests
import glob
import logging
import re
import json

from docx import Document
from vk_api import VkApi
from dotenv import load_dotenv
from datetime import datetime, timedelta
from services.Datbase import DataBase
from typing import Optional, Dict, List, Tuple

#logger init
logger = logging.getLogger("parser")

#load values from .env
load_dotenv()

#const
TOKEN = os.getenv('access_token')
GROUP_ID = os.getenv('schedule_id')

#main function
def run_parser() -> bool:
    try:
        logger.info("Parser start")
        #DataBase init
        data = DataBase()
        #get dates
        last_date = data.get_last_schedule_date()
        last_date = last_date or ""
        new_date = get_next_day()


        if new_date > last_date:
            link = get_vk_doc_link()
            if download_file(link):
                schedule = get_schedule()
                if schedule:
                    for cell in schedule:
                        data.ensure_lesson(group_name=cell[0],
                                           subject_name=cell[2],
                                           lesson_num=cell[1],
                                           classroom=cell[3],
                                           date=new_date)
                    return True
        return False
    except Exception:
        logger.exception("Exception:")

# function converter mixed names to numbers
def convert_group_name(group_name:Optional[str] = None) -> str:
    if group_name is None:
        return None
    
    result = re.sub(r'\D', '', group_name)
    return result

#function for get str with next day date
def get_file_name() -> str:
    today = datetime.today() #get current date

    #if today is Sut -> Mon(+2)
    if today.weekday() == 5:
        next_day = today + timedelta(days=2)
    #else if today not Sut -> +1
    else:
        next_day = today + timedelta(days=1)

    ndd = next_day.strftime("%d.%m.%Y")
    file_name = f"{ndd}.docx"

    return file_name

def get_next_day() -> str:
    today = datetime.today() #get current date

    #if today is Sut -> Mon(+2)
    if today.weekday() == 5:
        next_day = today + timedelta(days=2)
    #else if today not Sut -> +1
    else:
        next_day = today + timedelta(days=1)

    new_date = next_day.strftime("%Y-%m-%d")

    return new_date

#get doc's link from vk group
def get_vk_doc_link() -> str:
    global TOKEN, GROUP_ID
    #vk session init
    vk_session = VkApi(token=TOKEN)
    vk_api = vk_session.get_api()

    group_id = vk_api.groups.getById(group_id=GROUP_ID)[0]["id"]

    #get 5 last posts from wall
    wall = vk_api.wall.get(
        owner_id=-group_id,
        count=5
    )

    #get file_name
    file_name = get_file_name()

    for post in wall.get("items", []):
        for att in post.get("attachments", []):
            att_type = att.get("type")
            if att_type == "doc":
                att_title = att.get("doc", {}).get("title")
                if att_title == file_name:
                    logger.info("Parser get download link %s", att["doc"]["url"])
                    att_url = att.get("doc", {}).get("url")
                    return att_url
    
    return None

def download_file(link:Optional[str] = None) -> bool:
    if link is None:
        return False

    #get file_name and file_path with schedule
    filename = "schedule.docx"
    file_path = os.path.join(os.getcwd(), filename)

    #request to link
    response = requests.get(link, stream=True)
    response.raise_for_status()

    logger.info("Parser take http request to %s. Status: %s", link, response.status_code)

    remove_all_schedule() # delete all *.docx

    #write schedule to schedule.docx
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info("File was downloaded. Path: %s", file_path)

    return True

#get schedule from schedule.docx
def get_schedule() -> List:
    doc = Document("schedule.docx")
    schedule = []

    if not doc.tables:
        return schedule

    table = doc.tables[0]
    data = DataBase()

    for row in table.rows:
        for name in data.get_group_names():
            cells = clean([cell.text.strip() for cell in row.cells])

            if len(cells) == 4:
                if name == convert_group_name(cells[0]):
                    schedule.append([
                        name,
                        cells[-3],
                        cells[-2],
                        cells[-1]
                    ])
            elif len(cells) > 4:
                if name == convert_group_name(cells[1]):
                    schedule.append([
                        name,
                        cells[-3],
                        cells[-2],
                        cells[-1]
                    ])

    return schedule


def clean(items):
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result

#delete all *.docx
def remove_all_schedule() -> None:
    for file_path in glob.glob(os.path.join(os.getcwd(), "*.docx")):
        os.remove(file_path)
    logger.info("All .docx removed")

def upload_data(data, tag, value):
    logger.info("Upload %s to %s", tag, value)
    data[tag] = value
    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    result = run_parser()
    print(result)