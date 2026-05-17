import asyncio
import math
import datetime
from servers.server import *
from time import timezone
from config import *
from pathlib import Path
from aiogram.types import *
from aiogram import Router, F, types, Bot
from text.message import *
from keyboards.keyboard import *
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from plategaio import (
    PlategaAsyncClient,
    CreateTransactionRequest,
    PaymentDetails,
    PlategaAPIError,
)
import os


bot = Bot(token=BOT_TOKEN)
router = Router()
storage = MemoryStorage()

panel = XUIAPIManager(panel_url, panel_login, panel_password)

class SumMoney(StatesGroup):
    money_coin = State()
    end_date_device_state = State()

class User_States(StatesGroup):
    f_support = State()


@router.message(Command("start"))
async def start_message(message: Message, state: FSMContext):
    await state.clear()
    try:
        user_name = message.from_user.username
        user_id = message.from_user.id
        if user_name == None:
            await message.answer("Для того что бы наш сервис мог создать ваш конфиг у вас должен быть username(имя которое всегда начинается с @)")
        else:
            try:
                await database.add_user(user_id, user_name)
            except Exception as e:
                await bot.send_message(chat_id = ADMIN_ID, text = f'🚫Ошибка:\n{e}')

            await message.answer(f"{start_text(message.from_user.full_name)}", reply_markup = start_keyboard())

    except Exception as e:
        await bot.send_message(chat_id = ADMIN_ID, text = f'🚫Ошибка:\n{e}')

@router.callback_query(F.data == 'account')
#ОБЯЗАТЕЛЬНО ПРОРАБОТАЙ ОБРАБОТКУ ДАТЫ ЧТОБЫ ОНА НОРМАЛЬНО ПОКАЗЫВАЛАСЬ
async def account(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user_data = await database.get_user_full_info(user_id)
    if not user_data:
        await callback.message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    #Проверка наличия конца действия конфига
    if user_data['config_end_date']:
        end_date_bd = user_data['config_end_date']
        end_date = end_date_bd + timedelta(hours=3)
    else:
        end_date = None
    
    if user_data['limit_ip_end_date']:
        end_date_limit = user_data['limit_ip_end_date']
        end_date_limit_ip = end_date_limit + timedelta(hours=3)
    else:
        end_date_limit_ip = None

    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    
    try:
        day_status = (end_date - now).days
    except:
        day_status = -1


    if end_date == None:
        sub_status = "❌ Подписка не активна"
    elif end_date_bd > now:
        sub_status = f"✅ Подписка активна"
    elif end_date_bd < now:
        sub_status = "❌ Подписка не активна"
    else:
        sub_status = "❌ Подписка не активна"


    if day_status == 1:
        day_status_text = 'день'

    elif day_status > 1 and day_status < 5:
        day_status_text = 'дня'

    elif day_status > 4:
        day_status_text = 'дней'
    
    elif day_status < 0:
        day_status = 0
        day_status_text = 'дней'
    
    else:
        day_status = 0
        day_status_text = 'дней'

    end_date_limit_ip_str = end_date_limit_ip.strftime('%d.%m.%Y') if end_date_limit_ip else "❌ Доп. устройства не найдены"
    end_date_str = end_date.strftime('%d.%m.%Y') if end_date else "Не указана"
    text = f"""🧑‍💻Личный кабинет пользователя {callback.from_user.full_name}

Статус: {sub_status}

📲 Доступно устройств: {user_data['limit_ip']}

📆📲 Дата действия дополнительных устройств: {end_date_limit_ip_str}

📆 Дата конца подписки: {end_date_str} (Осталось: {day_status} {day_status_text})

    
💰 Баланс: {user_data['balance']} ₽"""
    await callback.message.edit_text(f'{text}', reply_markup = lk())

@router.callback_query(F.data == 'free_subscription')
async def free_subscription(callback: CallbackQuery):
    email = callback.from_user.username
    user_id = callback.from_user.id
    limit_ip = await database.get_username_full_info(callback.from_user.username)
    if await database.check_free_trial(user_id) == True:
        await database.date_status(callback.from_user.id, 7, 0)
        await panel.find_or_create_client(email, 1)
        await panel.extend_client(email, 7, limit_ip['limit_ip'], 1)
        await database.set_free_trial_true(user_id)
        await callback.message.answer('Зайдите в личный кабинет для того что бы получить ключ для активации')
    else:
        await callback.message.answer('Вы уже использовали бесплатную подписку')


@router.callback_query(F.data == 'back')
async def start_message_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"{start_text(callback.from_user.full_name)}", reply_markup = start_keyboard())

@router.callback_query(F.data == 'up_balance')
async def money(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Выберете сумму пополнения', reply_markup = credits())

@router.callback_query(F.data == 'subscription')
async def subscription(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("📆Укажите срок на который вы хотите продлить подписку\n (Перед покупкой подписки советуем ознакомиться с образованием цены на дополнительные устройства)", reply_markup = subscription_up())
    await panel.find_or_create_client(callback.from_user.username, 1)

@router.callback_query(F.data == 'info_limit_ip')
async def info_user_limit_ip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"{info_limit_ip()}", reply_markup = back_menu())
#С этого момента пойдут ответы на кнопки которые отвечают, за продление подписки

@router.callback_query(F.data == 'thirty_days')
#При выборе на 30 дней
async def subscription_thirty_days(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #Проверка баланса
    balans_check = await database.date_status(callback.from_user.id, 30, 200)#Проверить потом продлевается ли подписка если на счету нет денег
    limit_ip = await database.get_username_full_info(callback.from_user.username)#Проверка на кол-во устройств
    if balans_check == True:
        await panel.extend_client(callback.from_user.username, 30, limit_ip['limit_ip'], 1)
        await callback.message.edit_text('✅ Ваша подписка продлена на 30 дней', reply_markup = back_menu())
    elif balans_check == False:
        await callback.message.edit_text('❌ К сожалению на вашем счету недостаточно средств, вернитесь в личный кабинет для пополнения баланса', reply_markup = back_menu())

@router.callback_query(F.data == 'ninety_days')
#При выборе на 90 дней
async def subscription_ninety_days(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #Проверка баланса
    balans_check = await database.date_status(callback.from_user.id, 90, 400)#Проверить потом продлевается ли подписка если на счету нет денег
    limit_ip = await database.get_username_full_info(callback.from_user.username)#Проверка на кол-во устройств
    if balans_check == True:
        await panel.extend_client(callback.from_user.username, 90, limit_ip['limit_ip'], 1)
        await callback.message.edit_text('✅ Ваша подписка продлена на 90 дней', reply_markup = back_menu())
    elif balans_check == False:
        await callback.message.edit_text('❌ К сожалению на вашем счету недостаточно средств, вернитесь в личный кабинет для пополнения баланса', reply_markup = back_menu())

@router.callback_query(F.data == 'one_hundred_twenty_days')
#При выборе на 120 дней
async def subscription_one_hundred_twenty_days(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #Проверка баланса
    balans_check = await database.date_status(callback.from_user.id, 120, 1200)#Проверить потом продлевается ли подписка если на счету нет денег
    limit_ip = await database.get_username_full_info(callback.from_user.username)#Проверка на кол-во устройств
    if balans_check == True:
        await panel.extend_client(callback.from_user.username, 120, limit_ip['limit_ip'], 1)
        await callback.message.edit_text('✅ Ваша подписка продлена на 120 дней', reply_markup = back_menu())
    elif balans_check == False:
        await callback.message.edit_text('❌ К сожалению на вашем счету недостаточно средств, вернитесь в личный кабинет для пополнения баланса', reply_markup = back_menu())

@router.callback_query(F.data == 'year')
#При выборе на 365 дней
async def subscription_year(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    #Проверка баланса
    balans_check = await database.date_status(callback.from_user.id, 365, 2400)#Проверить потом продлевается ли подписка если на счету нет денег
    limit_ip = await database.get_username_full_info(callback.from_user.username)#Проверка на кол-во устройств
    if balans_check == True:
        await panel.extend_client(callback.from_user.username, 365, limit_ip['limit_ip'], 1)
        await callback.message.edit_text('✅ Ваша подписка продлена на 365 дней', reply_markup = back_menu())
    elif balans_check == False:
        await callback.message.edit_text('❌ К сожалению на вашем счету недостаточно средств, вернитесь в личный кабинет для пополнения баланса', reply_markup = back_menu())

#От сюда идет реакция на кнопки оплаты
@router.callback_query(F.data == 'random_money')
async def random_money(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Введите сумму пополнения', reply_markup = back_menu())
    await state.set_state(SumMoney.money_coin)

@router.message(SumMoney.money_coin)
async def money_dep(message: Message, state: FSMContext):
    #Сюда подключать платегу
    text = message.text
    new_text = text.replace(',', '.')
    try:
        if float(new_text) < 50:
            await message.answer('Введите сумму от 50руб', reply_markup = back_menu())

        elif float(new_text) >= 50:
            async with database.get_connection() as conn:
                await conn.execute("""
                                    UPDATE users
                                    SET balance = balance + $1
                                    WHERE user_id = $2
                                    """, float(new_text), message.from_user.id)
                await message.answer(f'Счет успешно пополнен на {new_text}руб', reply_markup = back_menu())
            await state.clear()
    except Exception as e:
        await message.answer('Пожалуйста вводите число', reply_markup = back_menu())

@router.callback_query(F.data == 'credits_200')
async def money_dep_credits_200(callback: CallbackQuery, state: FSMContext):
    #Вполне вероятно что нужно будет исправить отправляемое сообщение где указанна сумма пополнения
    await state.clear()
    async with database.get_connection() as conn:
        await conn.execute("""
                            UPDATE users
                            SET balance = balance + $1
                            WHERE user_id = $2
                            """, 200, callback.from_user.id)
    await callback.message.edit_text(f'Счет успешно пополнен на 200 руб', reply_markup = back_menu())

@router.callback_query(F.data == 'credits_400')
async def money_dep_credits_400(callback: CallbackQuery, state: FSMContext):
    #Вполне вероятно что нужно будет исправить отправляемое сообщение где указанна сумма пополнения
    await state.clear()
    async with database.get_connection() as conn:
        await conn.execute("""
                            UPDATE users
                            SET balance = balance + $1
                            WHERE user_id = $2
                            """, 400, callback.from_user.id)
    await callback.message.edit_text(f'Счет успешно пополнен на 400 руб', reply_markup = back_menu())

@router.callback_query(F.data == 'credits_1200')
async def money_dep_credits_1200(callback: CallbackQuery, state: FSMContext):
    #Вполне вероятно что нужно будет исправить отправляемое сообщение где указанна сумма пополнения
    await state.clear()
    async with database.get_connection() as conn:
        await conn.execute("""
                            UPDATE users
                            SET balance = balance + $1
                            WHERE user_id = $2
                            """, 1200, callback.from_user.id)
    await callback.message.edit_text(f'Счет успешно пополнен на 1200 руб', reply_markup = back_menu())

@router.callback_query(F.data == 'credits_2400')
async def money_dep_credits_2400(callback: CallbackQuery, state: FSMContext):
    #Вполне вероятно что нужно будет исправить отправляемое сообщение где указанна сумма пополнения
    await state.clear()
    async with database.get_connection() as conn:
        await conn.execute("""
                            UPDATE users
                            SET balance = balance + $1
                            WHERE user_id = $2
                            """, 2400, callback.from_user.id)
    await callback.message.edit_text(f'Счет успешно пополнен на 2400 руб', reply_markup = back_menu())

#Дополнительные устройства
@router.callback_query(F.data == 'add_device')
async def additional_seats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user_data = await database.get_user_full_info(user_id)

    if user_data['limit_ip_end_date']:
        end_date_bd = user_data['limit_ip_end_date']
        end_date = end_date_bd + timedelta(hours=3)
    elif user_data['limit_ip_end_date'] == None:
        end_date_bd = user_data['config_end_date']
        end_date = end_date_bd + timedelta(hours=3)
    else:
        end_date = None

    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)

    if end_date < now:
        await callback.message.answer('Для подключения дополнительного устройства вам нужно оформить подписку это вы можете сделать в личном кабинете нажав на кнопку "Продлить подписку"')
    elif end_date > now or end_date == None:
        time_device = ((end_date - now).days) / 30
        time_device = math.ceil(time_device)
        pay = time_device * 150
        await callback.message.edit_text(f'К оплате {pay} за подключение одного устройства', reply_markup = end_date_device_pay(pay))
        await state.set_state(SumMoney.end_date_device_state)
    else:
        await callback.message.answer('Для подключения дополнительного устройства вам нужно оформить подписку это вы можете сделать в личном кабинете нажав на кнопку "Продлить подписку"')
    
@router.callback_query(F.data and SumMoney.end_date_device_state)
async def additional_seats_pay(callback: CallbackQuery, state: FSMContext):
    pay = callback.data

    username = callback.from_user.username
    user_id = callback.from_user.id


    if await database.status_limit_ip_end_date(username, 1, int(pay)):
        user_data = await database.get_user_full_info(user_id)

        await panel.extend_client_limit_ip(user_data['username'], user_data['limit_ip'], 1)
        await callback.message.answer(f'✅ Оплата прошла успешно, теперь вам доступно {user_data['limit_ip']} одновременных подключений')

    elif await database.status_limit_ip_end_date(username, 1, int(pay)) == False:
        await callback.message.answer(f'❌ На вашем счету недостаточно средств, вернитесь в личный кабинет для пополнения балланса')

    await state.clear()

#Получение конфига
@router.callback_query(F.data == 'key')
async def key(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Ваш запрос обрабатывается')

    telegram_id = callback.from_user.id

    async with database.get_connection() as conn:
        config_bd = await conn.fetchval("""SELECT vpn_config FROM users
                                     WHERE user_id = $1
                                     """, telegram_id)
        if callback.from_user.username == None:
            await callback.message.answer("Для того что бы наш сервис мог создать ваш конфиг у вас должен быть username(имя которое всегда начинается с @)")
        elif config_bd:
            await callback.message.answer('Скопируйте конфиг и найдите в програме функцию "Вставить из буфера обмена"')
            await callback.message.answer(f"{config_bd}")
        else:
            await panel.find_or_create_client(callback.from_user.username, 1)
            config = await panel.config(callback.from_user.username)
            await conn.execute("""UPDATE users
                               SET vpn_config = $1
                               WHERE user_id = $2
                               """, config, telegram_id)
            await callback.message.answer('Скопируйте конфиг и найдите в програме функцию "Вставить из буфера обмена"')
            await bot.send_message(chat_id=callback.from_user.id, text=f"{config}")
    await callback.answer()

#Инструкция настройки
@router.callback_query(F.data == 'info')
async def user_key(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer('Скопируйте конфиг который вам выдаст бот, после нажатия кнопки "Получить ключ"')
    await callback.message.answer_photo(photo=FSInputFile(f"./img/1.jpg"), caption="1) После того как вы скопируете ключ вам нужно будет зайти в приложение и нажать на плюсик")
    await callback.message.answer_photo(photo=FSInputFile(f"./img/2.jpg"), caption='2) В появившемся меню выберете пункт "Импорт из буфера обмена"')
    await callback.message.answer_photo(photo=FSInputFile(f"./img/3.jpg"), caption='3) После выполнение пунктов 1 и 2 у вас появится ваш конфиг')
    await callback.message.answer_photo(photo=FSInputFile(f"./img/4.jpg"), caption='4) Вам останется только выбрать ваш конфиг, и нажать на кнопку включения она будет синего цвета')
    await callback.message.answer_photo(photo=FSInputFile(f"./img/5.jpg"), caption='5) После нажатия кнопка должна будет сменить цвет с синего на зеленый')

#Настройка для белых списков
@router.callback_query(F.data == 'info_setings')
async def info_setings (callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f'{text_setings()}', reply_markup = back_menu())

#Поддержка
@router.callback_query(F.data == 'support')
async def support_message(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await state.set_state(User_States.f_support)
    await callback.message.answer(f"{support_text()}")

@router.message(User_States.f_support)
async def support_sending(message: Message, state: FSMContext):
    await bot.send_message(chat_id=ADMIN_ID, text=f"Пользователь: {message.from_user.full_name}\nID: {message.from_user.id}\n{message.text}")
    await message.answer("✅Ваш запрос был отправлен, мы постараемся в скором времени решить вашу проблему")
    await state.clear()

#Добавить функцию которая будет проверять бд и удалять время подписки если она истекла