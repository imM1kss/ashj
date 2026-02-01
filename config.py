import aiogram
from aiogram import Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os
import logging

from db.database import Database

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        load_dotenv() # можешь указать путь к своему .env файлу как аргумент, если он не в корне проекта
        logger.debug('Конфиг инициализирован')

    def bot_token(self):
        return os.getenv('BOT_TOKEN')

    def admin_id(self):
        admins = '1015810336, 1015810336' # В последующем берем из бд при каждом обращении
        return [int(a) for a in admins.split(',')]

config_bot = Config()
db = Database('test.db')
print(config_bot.bot_token())
bot = aiogram.Bot(token=config_bot.bot_token(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
