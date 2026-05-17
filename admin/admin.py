import asyncio
from config import *
from aiogram.types import *
from keyboards.admin_keyboard import *
from aiogram import Router, F, types, Bot
from servers.server import *
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token=BOT_TOKEN)
admin = Router()

panel = XUIAPIManager(panel_url, panel_login, panel_password)
storage = MemoryStorage()

class Off_User_Panel(StatesGroup):
    off_user_state = State()

class Subscription_Date(StatesGroup):
    subscription_date_state = State()

class Delit_User(StatesGroup):
    delit_user_state = State()

class Admin_BD(StatesGroup):
    info_user_bd_state = State()
    admin_delit_user_state = State()
    admin_delit_config_state = State()
    admin_user_money_up_state = State()
    spam_text_state = State()
    limit_ip_date_state = State()

@admin.message(Command('admin'))
async def admin_start_message(message: Message, state: FSMContext):
    if message.from_user.id == int(ADMIN_ID):
        await state.clear()
        await message.answer('С чем будем взаимодействовать?', reply_markup = start_keyboard_admin())

@admin.callback_query(F.data == 'panel_admin')
async def panel_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id == int(ADMIN_ID):
        await state.clear()
        await callback.message.edit_text('Выберете действие в панели', reply_markup = panel_work_admin())

#Отключения пользователя
@admin.callback_query(F.data == 'off_user')
async def off_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id == int(ADMIN_ID):
        await state.clear()
        await callback.message.answer('Введите user_name пользователя для отключения') #Добавить кнопку возвращения в главное меню
        await state.set_state(Off_User_Panel.off_user_state)

@admin.message(Off_User_Panel.off_user_state)
async def off_panel_user(message: Message, state: FSMContext):
    user = message.text
    panel_user = await panel.off_user_comand(user, 1)
    await message.answer(f'{panel_user}')
    await state.clear()

#Продление подписки
@admin.callback_query(F.data == 'subscription_date')
async def subscription_date_user(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id == int(ADMIN_ID):
        await state.clear()
        await callback.message.answer('Введите username пользователя, id пользователя, и кол-во дней для увелечения через пробел, и в правильном порядке')
        await state.set_state(Subscription_Date.subscription_date_state)

@admin.message(Subscription_Date.subscription_date_state)
async def subscription_date_panel_and_bd(message: Message, state: FSMContext):
    try:
        user_date = message.text
        text_admin = [x.strip() for x in user_date.split(' ') if x.strip()]
        user_id = text_admin[1]
        user_name = text_admin[0]
        date_time = text_admin[2]
        limit_ip = await database.get_username_full_info(user_name)#Проверка на кол-во устройств
        await panel.extend_client(user_name, int(date_time), limit_ip['limit_ip'], 1)
        await database.date_status(int(user_id), int(date_time), 0)
        await message.answer(f'Пользователю {text_admin[0]}, продлили подписку на {text_admin[2]}')
        await state.clear()
    except Exception as e:
        await message.answer('Упс что-то пошло не так')
        await message.answer(f'Ошибка: {e}')
        await message.answer(text_admin)
        await state.clear()

@admin.callback_query(F.data == 'delit_user_panel')
async def delit_user_1(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id == int(ADMIN_ID):
        await state.clear()
        await callback.message.answer('Введите ник того кого хотите удалить')
        await state.set_state(Delit_User.delit_user_state)
    else:
        print("Все же что-то не так")

@admin.message(Delit_User.delit_user_state)
async def delit_user_state_admin(message: Message, state: FSMContext):
    email = message.text
    await panel.delite_user(email, 1)
    await message.answer(f'Клиент {email} был удален из панели') #Дописать удаления пользователя из бд и из панели
    await state.clear()

#Взаимодействие с базой данных
@admin.callback_query(F.data == 'bd_admin')
async def admin_bd(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.edit_text('Выберете действие в БД', reply_markup = bd_admin())

@admin.callback_query(F.data == 'info_user_admin')
async def admin_user_full_info(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите usernme пользователя для предоставления информации')
        await state.set_state(Admin_BD.info_user_bd_state)

@admin.message(Admin_BD.info_user_bd_state)
async def full_info_user_bd(message: Message, state: FSMContext):
    username = message.text
    info_user = await database.get_username_full_info(username)
    if info_user:
        if info_user['config_start_date']:
            start_date = info_user['config_start_date']
            start_date = start_date + timedelta(hours=3)
        else:
            start_date = None

        start_date_str = start_date.strftime('%d.%m.%Y %H:%M') if start_date else "Не указана"

        if info_user['config_end_date']:
            end_date = info_user['config_end_date']
            end_date = end_date + timedelta(hours=3)
        else:
            end_date = None

        end_date_str = end_date.strftime('%d.%m.%Y %H:%M') if start_date else "Не указана"

        if info_user['vpn_config']:
            vpn_config = info_user['vpn_config']
        else:
            vpn_config = None

        vpn_config_str = vpn_config if vpn_config else "Не получал"

        await message.answer(f"""Информация пользователя {username} 

ID: {info_user['user_id']}
UserName: {info_user['username']}

Начала действия: {start_date_str}
Конец действия: {end_date_str}

Конфиг: {vpn_config_str}

limit_ip: {info_user['limit_ip']}
Дата окончания действия limit_ip: {info_user['limit_ip_end_date']}

Баланс: {info_user['balance']}
Беплатная подписка: {info_user['has_free_trial']}""")
    else:
        await message.answer('Данного пользователя нет в базе данных')
    
    await state.clear()

@admin.callback_query(F.data == 'limit_ip_date')
async def limit_ip_date_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите username пользователя и кол-во дней для изменения даты limit_ip')
        await state.set_state(Admin_BD.limit_ip_date_state)

@admin.message(Admin_BD.limit_ip_date_state)
async def limit_ip_date_admin_state(message: Message, state: FSMContext):
    user_date = message.text
    text_admin = [x.strip() for x in user_date.split(' ') if x.strip()]
    await database.limit_ip_date_admin(text_admin[0], int(text_admin[1]))
    await message.answer(f'Пользователю {text_admin[0]}, прибавили {text_admin[1]} для доп. устройств')
    await state.clear()


@admin.callback_query(F.data == 'delite_user_admin')
async def admin_bd_delit_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите username пользователя для удаления его из бд')
        await state.set_state(Admin_BD.admin_delit_user_state)

@admin.message(Admin_BD.admin_delit_user_state)
async def admin_bd_user_delit(message: Message, state: FSMContext):
    username = message.text
    if await database.delite_user(username):
        await message.answer(f'Пользователь {username} был успешно удален')
    else:
        await message.answer(f'Пользователь {username}, не найден')
    await state.clear()

@admin.callback_query(F.data == 'delit_config_user_admin')
async def admin_delit_config_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите username пользователя для удаления')
        await state.set_state(Admin_BD.admin_delit_config_state)

@admin.message(Admin_BD.admin_delit_config_state)
async def admin_delit_config_user_state(message: Message, state:FSMContext):
    username = message.text
    if await database.delete_user_config(username):
        await message.answer(f'Пользователю {username}, конфиг удален')
    else:
        await message.answer(f'У Пользователя {username}, кониг не найден')
    await state.clear()

@admin.callback_query(F.data == 'money_up')
async def admin_money_up_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите username и сумму пополнения пользователя')
        await state.set_state(Admin_BD.admin_user_money_up_state)

@admin.message(Admin_BD.admin_user_money_up_state)
async def admin_money_up_state(message: Message, state: FSMContext):
    user_date = message.text
    text_admin = [x.strip() for x in user_date.split(' ') if x.strip()]
    async with database.get_connection() as conn:
        await conn.execute("""
                            UPDATE users
                            SET balance = balance + $1
                            WHERE username = $2
                            """, int(text_admin[1]), str(text_admin[0]))
    await message.answer(f'Счет успешно пополнен на {text_admin[1]} руб пользователю {text_admin[0]}')
    await state.clear()

@admin.callback_query(F.data == 'spam_new_key')
async def spam_new_key(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    if callback.from_user.id == int(ADMIN_ID):
        usernames = await database.get_all_usernames()

        for conf in usernames:
            if await database.delete_user_config(conf):
                await callback.message.answer(f'Пользователю {conf}, конфиг удален')
            else:
                await callback.message.answer(f'У Пользователя {conf}, кониг не найден')

            await panel.find_or_create_client(conf, 1)
        await panel.sync_all_users_expiry() #Здесь зашит сразу инбаунд 1
        
        for conf in usernames:
            config_spam = await panel.config(conf)
            get_user_id = await database.get_username_full_info(conf)
            await bot.send_message(chat_id = get_user_id['user_id'], text = config_spam)

@admin.callback_query(F.data == 'spam_admin')
async def spam_text(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.answer('Введите текст для рассылки')
        await state.set_state(Admin_BD.spam_text_state)

@admin.message(Admin_BD.spam_text_state)
async def admin_spam_text(message: Message, state: FSMContext):
    spam_message = message.text
    async with database.get_connection() as conn:
        telegram_id = await conn.fetch("""SELECT user_id FROM users
                                       ORDER BY user_id""")
        telegram_ids = [row['user_id'] for row in telegram_id]

        sent = 0
        failed = 0
        for i in telegram_ids:
            try:
                await bot.send_message(chat_id = i, text = f'{spam_message}')
                sent += 1
            except Exception as e:
                failed += 1
                await bot.send_message(chat_id=ADMIN_ID, text=f'Ошибка отправки для {i}: {e}')

            await asyncio.sleep(0.2)
        await message.answer(f"✅ Рассылка завершена\n"
                             f"📨 Отправлено: {sent}\n"
                             f"❌ Ошибок: {failed}")
    await state.clear()

@admin.callback_query(F.data == 'menu_admin')
async def panel_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id == int(ADMIN_ID):
        await callback.message.edit_text('С чем будем взаимодействовать?', reply_markup=start_keyboard_admin())