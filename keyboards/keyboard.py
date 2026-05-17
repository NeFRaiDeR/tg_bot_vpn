from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text = "🧑‍💻Личный кабинет", style="success", callback_data = "account")],
            [InlineKeyboardButton (text='🤖 Скачать приложение android', callback_data='app', url='https://play.google.com/store/apps/details?id=com.v2raytun.android')],
            [InlineKeyboardButton (text='🍎 Скачать приложение iphone', callback_data='app', url='https://apps.apple.com/us/app/v2raytun/id6476628951')],
            [InlineKeyboardButton (text='Пробная подписка на 7 дней', callback_data='free_subscription')],
            [InlineKeyboardButton (text='Инструкция Активации', callback_data='info'),
             InlineKeyboardButton (text='Доп.Настройки', callback_data='info_setings')],
            [InlineKeyboardButton (text='Поддержка', callback_data='support')]
        ]
    )

def lk():
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='💰Пополнить баланс', style='success', callback_data = 'up_balance')],
            [InlineKeyboardButton(text='📆 Продлить подписку', callback_data = 'subscription')],
            [InlineKeyboardButton(text='📱 + Добавить устройство', callback_data='add_device')],
            [InlineKeyboardButton(text='🔑 Получить конфиг', callback_data = 'key')],#Прикрутить к панели и сделать проверку оплаты
            [InlineKeyboardButton(text='<< Назад', callback_data = 'back')]
        ]
    )

def credits():
    #Появляется после нажатия пополнить баланс
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='200₽', callback_data = 'credits_200')],
            [InlineKeyboardButton(text='400₽', callback_data = 'credits_400')],
            [InlineKeyboardButton(text='1200₽', callback_data = 'credits_1200')],
            [InlineKeyboardButton(text='2400₽', callback_data = 'credits_2400')],
            [InlineKeyboardButton(text='Другая сумма', callback_data = 'random_money')],
            [InlineKeyboardButton(text='🧑‍💻Вернуться в личный кабинет', callback_data = "account")]
        ]
    )

def new_device():
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='Добавить устройство', callback_data = 'end_date_device')],
            [InlineKeyboardButton(text='🧑‍💻Вернуться в личный кабинет', callback_data = "account")]
        ]
    )

def end_date_device_pay(prise):
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text=f'Оплатить {prise}₽', callback_data = f'{prise}')],
            [InlineKeyboardButton(text='🧑‍💻Вернуться в личный кабинет', callback_data = "account")]
        ]
    )
def subscription_up():
    #Появляется после нажатия Продлить подписку
    #Добавить функцию которая перед списанием средств будет спрашивать уверен ли пользователь в том что он не мискликнул
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='Оплатить 30 дней - 200₽', callback_data = 'thirty_days')],
            [InlineKeyboardButton(text='Оплатить 90 дней - 400₽', callback_data = 'ninety_days')],
            [InlineKeyboardButton(text='Оплатить 120 дней - 1200₽', callback_data = 'one_hundred_twenty_days')],
            [InlineKeyboardButton(text='Оплатить 365 дней - 2400₽', callback_data = 'year')],
            [InlineKeyboardButton(text='Цены за доп. устройства', callback_data = 'info_limit_ip')],
            [InlineKeyboardButton(text='🧑‍💻Вернуться в личный кабинет', callback_data = "account")]
        ]
    )

#кнопки для частого использования
def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text='Вернуться в личный кабинет', callback_data = "account")]
        ]
    )
