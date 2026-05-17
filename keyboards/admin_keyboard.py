import asyncio
import asyncpg
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'пароль бд',
    'database': 'users'
}

def start_keyboard_admin():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = "Панель", callback_data = "panel_admin")],
            [InlineKeyboardButton (text='База данных', callback_data='bd_admin')],
            [InlineKeyboardButton (text='Рассылка новых ключей', callback_data='spam_new_key')],
            [InlineKeyboardButton (text='Рассылка', callback_data='spam_admin')]
        ]
    )

def panel_work_admin():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = "Отключить пользователя", callback_data = "off_user")],
            [InlineKeyboardButton (text='Изменить дату окончания подписки', callback_data='subscription_date')],
            [InlineKeyboardButton (text='Удалить пользователя из панели', callback_data='delit_user_panel')],
            [InlineKeyboardButton (text='Вернуться в меню', callback_data='menu_admin')]
        ]
    )

def bd_admin():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = "Получить информацию пользователя", callback_data = "info_user_admin")],
            [InlineKeyboardButton (text='Изменить дату limit_ip', callback_data='limit_ip_date')],
            [InlineKeyboardButton (text='Удаление пользователя из БД', callback_data='delite_user_admin')],
            [InlineKeyboardButton (text='Удалить конфиг пользователя', callback_data='delit_config_user_admin')],
            [InlineKeyboardButton (text='Добавить деняг пользователю', callback_data='money_up')],
            [InlineKeyboardButton (text='Вернуться в меню', callback_data='menu_admin')]
        ]
    )