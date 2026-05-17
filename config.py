import os
from bd.db import *
from dotenv import load_dotenv

load_dotenv()

#Данные бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

#Данные БД
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))

database = DB(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
        min_size=5,
        max_size=20
        )

#Данные панели
panel_url = "http://127.0.0.1:46375/1ljOhOwjvxUpEn2FZq"
panel_login = os.getenv('PANEL_LOGIN')
panel_password = os.getenv('PANEL_PASSWORD')
server_ip = "109.120.183.151"
