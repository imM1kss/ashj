import os
from dotenv import load_dotenv
import sys
import io
from openai import OpenAI

load_dotenv()

#const
TOKEN = os.getenv("groq_token")


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = OpenAI(
    api_key=TOKEN, 
    base_url="https://api.groq.com/openai/v1"
)

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": "У тебя есть сообщение пользователя: 'Завтра по физике срезовая контрольная работа. Прошу проверить свой moodle'. Также у этой группы есть список предметов ['Математика','Физика','МДК']. Ответь это дз или нет? Какой это предмет из списка? Какое содержание дз? Ответ верни в формате: 'Предмет:содержание дз'"}
        ]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Ошибка: {e}")