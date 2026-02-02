from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import json
import os
import requests
from docx import Document
import glob

def run_parser():

    with open("data.json", 'r', encoding="utf-8") as file:
        data = json.load(file)

    ndd, ndf = get_next_day()
    schedule = None
    if ndd != data["last_date"]:
        download_link = get_file_link(ndd, data)
        download = download_file(download_link, ndf)
        if download:
            file_name = f"{ndf}.docx"
            schedule = get_schedule(file_name)
            upload_data(data, "last_date", ndd)
    return schedule




def get_next_day():
    today = datetime.today()

    if today.weekday() == 5:
        next_day = today + timedelta(days=2)
    elif today.weekday() == 6:
        next_day = today + timedelta(days=1)
    else:
        next_day = today + timedelta(days=1)

    ndd = next_day.strftime("%d.%m.%Y")
    ndf = next_day.strftime("%d_%m_%Y")

    return ndd,ndf

def get_file_link(ndd,data):

    url = data["url_schedule"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except:
            page.goto(url, wait_until="networkidle", timeout=60000)

        page.wait_for_selector(f"xpath=//span[contains(@title, '{ndd}')]")

        spans = page.query_selector_all(f"xpath=//span[contains(@title, '{ndd}')]")
        download_link = None

        for span in spans:
            container = span.query_selector("xpath=ancestor::div[2]")
            if not container:
                continue

            a_tag = container.query_selector("xpath=.//a[contains(@href, 'doc')]")
            if a_tag:
                 return a_tag.get_attribute("href")

        browser.close()
        return None

def download_file(download_link, ndf):
    if download_link:
        filename = f"{ndf}.docx"
        file_path = os.path.join(os.getcwd(), filename)

        response = requests.get(download_link, stream=True)
        response.raise_for_status()

        remove_all_schedule()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


def clean(items):
    new_list = []
    for el in items:
        if el not in new_list: 
            new_list.append(el)
    return new_list

def get_schedule(doc_name):
    doc = Document(doc_name)
    shedule = []
    if doc.tables:
        table = doc.tables[0]
        for i in range(len(table.rows)):
            row = clean([cell.text.strip() for cell in table.rows[i].cells])
            
            if "25-14" in row:
                cnt = len(row)
                shedule.append([row[cnt - 3],row[cnt - 2],row[cnt - 1]])
    return shedule

def remove_all_schedule():
    doc_files = glob.glob(os.path.join(os.getcwd(), "*.docx"))

    for file_path in doc_files:
        os.remove(file_path)
        print(f"remove {file_path}")

def upload_data(data, tag, value):
    data[tag] = value

    with open("data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
