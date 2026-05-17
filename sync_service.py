import asyncio
import pytz
from handler.handler import panel
from datetime import datetime, timedelta
from config import database
from aiogram import Bot
from config import BOT_TOKEN, ADMIN_ID

bot = Bot(token=BOT_TOKEN)

class SyncService:

    def __init__(self):
        self.is_running = False
    
    async def check_and_clean_devices(self):
        print('Запуск проверки лимитов устройств')

        try:

            async with database.get_connection() as conn:
                users = await conn.fetch("""
                    SELECT user_id, username, limit_ip, limit_ip_end_date, config_end_date
                    FROM users 
                    WHERE username IS NOT NULL
                    AND limit_ip_end_date IS NOT NULL
                """)

                now = datetime.now(pytz.timezone('Europe/Moscow'))
                print(now)
                cleaned_count = 0
                errors = []

                for user in users:
                    username = user['username']
                    user_id = user['user_id']
                    limit_ip = user['limit_ip'] or 1
                    limit_ip_end_date = user['limit_ip_end_date']
                    config_end_date = user['config_end_date']

                    limit_ip_end_date = limit_ip_end_date + timedelta(hours=3)
                    config_end_date = config_end_date + timedelta(hours=3)
                    if limit_ip_end_date and limit_ip_end_date <= now:

                        try:
                            await conn.execute("""
                            UPDATE users 
                            SET limit_ip = 1,
                                limit_ip_end_date = NULL
                                WHERE user_id = $1
                                """, user_id)
                            
                            await panel.extend_client_limit_ip(username, 1, 1)
                            print(f"✅ {username}: лимит сброшен до 1 устройства")

                            try:
                                await bot.send_message(
                                    chat_id=user_id,
                                    text= f"⚠️ <b>Внимание!</b>\n\n"
                                         f"Истек срок действия дополнительных устройств.\n"
                                         f"Теперь у вас активено только 1 устройство.\n\n"
                                         f"Чтобы снова добавить устройства, приобретите дополнительный лимит в личном кабинете.",
                                        parse_mode="HTML")
                                
                            except:
                                pass

                            cleaned_count += 1
                        except Exception as e:
                            errors.append(f"{username}: {e}")
                            await bot.send_message(chat_id = ADMIN_ID, text = f"❌ Ошибка при сбросе лимита {username}: {e}")
                            print(f"❌ Ошибка при сбросе лимита {username}: {e}")

                    elif config_end_date and config_end_date <= now:

                        if limit_ip != 1:
                            print(f"⚠️ У {username} истекла подписка, сбрасываю лимит")
                            try:
                                await conn.execute("""
                                    UPDATE users 
                                    SET limit_ip = 1,
                                        limit_ip_end_date = NULL
                                    WHERE user_id = $1
                                """, user_id)
                                cleaned_count += 1
                            except Exception as e:
                                errors.append(f"{username}: {e}")
                                await bot.send_message(chat_id = ADMIN_ID, text = f"❌ Ошибка при сбросе лимита {username}: {e}")
                            
                print(f"📊 Проверка завершена. Сброшено лимитов: {cleaned_count}")
                await bot.send_message(chat_id = ADMIN_ID, text = f"📊 Проверка завершена. Сброшено лимитов: {cleaned_count}")

                if errors:
                    print(f"❌ Ошибок: {len(errors)}")
                    await bot.send_message(chat_id = ADMIN_ID, text = f"❌ Ошибок: {len(errors)}")

        except Exception as e:
            print(f"❌ Критическая ошибка в check_and_clean_devices: {e}")
            await bot.send_message(chat_id = ADMIN_ID, text = f"❌ Критическая ошибка в check_and_clean_devices: {e}")

    async def run_forever(self):

        self.is_running = True
        print("🟢 Сервис синхронизации запущен")

        while self.is_running:
            try:
                await self.check_and_clean_devices()

                print(f"⏰ Следующая проверка через 30 минут ({datetime.now().strftime('%H:%M:%S')})")

                await asyncio.sleep(30 * 60)
            
            except Exception as e:
                print(f"❌ Ошибка в цикле синхронизации: {e}")
                await bot.send_message(chat_id = ADMIN_ID, text = f"❌ Ошибка в цикле синхронизации: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """
        Остановка сервиса
        """
        self.is_running = False
        print("🔴 Сервис синхронизации остановлен")


sync_service = SyncService()
        
