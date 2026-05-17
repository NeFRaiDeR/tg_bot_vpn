import os
import asyncio
from handler.handler import *
from aiogram import Dispatcher
from handler.handler import router
from admin.admin import admin
from sync_service import sync_service


async def main():
    await database.connect()

    
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin)

    print('✅ Бот запущен')
    try:
        await dp.start_polling(bot)
    finally:
        await database.disconnect()


if __name__ == '__main__':
    asyncio.run(main())