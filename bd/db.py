import os
import asyncio
import pytz
import asyncpg
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from pathlib import Path

#ЗАПУСКАТЬ ЭТОТ ФАИЛ ТОЛЬКО ДЛЯ СОЗДАНИЯ БД


class DB:
    def __init__(self, user, password, host, port, database, min_size, max_size):
        self.dsn = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn = self.dsn,
            min_size = self.min_size,
            max_size = self.max_size,
            command_timeout = 60
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            raise RuntimeError("Pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            await connection.execute("SET TIME ZONE 'Europe/Moscow';")
            tz = await connection.fetchval("SHOW TIMEZONE")
            print(f"🕐 Timezone для соединения: {tz}")
            yield connection

    async def add_user(self, user_id: int, username: str = None):
        #Создание пользователя
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                                INSERT INTO users (user_id, username)
                                VALUES ($1, $2)
                                ON CONFLICT (user_id) DO NOTHING
                                   """, user_id, username)
                
                print(f"✅ Пользователь {user_id} добавлен в БД")
                return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении пользователя: {e}")
            return False
        
    async def date_status(self, user_id: int, days: int, price: int):
        #Это продление подписки со списанием средств
        #применять для кнопок в которых указанно кол-во дней и цена, указывать пользователя сколько дней нужна подписка и стоимость подписки
        async with self.get_connection() as conn:
            balance = await conn.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)

            if balance < price:
                return False
            else:
                # Списываем деньги
                await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", price, user_id)

            # Продлеваем подписку
            end_date = await conn.fetchval(
            "SELECT config_end_date FROM users WHERE user_id = $1",
            user_id
            )

            now = datetime.now(pytz.timezone('Europe/Moscow'))

            if end_date and end_date > now:
                # Если подписка активна - добавляем дни к текущему сроку
                new_end_date = end_date + timedelta(days=days)
                print(f"Подписка активна, продлеваем с {end_date.strftime('%d.%m.%Y %H:%M')}")
            else:
                # Если подписка истекла или не установлена - начинаем с текущего момента
                new_end_date = now + timedelta(days=days)
                print(f"Подписка истекла, начинаем с текущего момента {now.strftime('%d.%m.%Y %H:%M')}")
                
            await conn.execute("""
            UPDATE users 
            SET config_end_date = $1,
                config_start_date = CASE 
                    WHEN config_start_date IS NULL THEN CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Moscow'
                    ELSE config_start_date 
                END
            WHERE user_id = $2
        """, new_end_date, user_id)
            
            return True
    
    async def get_user_full_info(self, user_id: int):
        #Вся инфформация пользователя
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                                        SELECT
                                            user_id,
                                            username,
                                            balance,
                                            config_start_date,
                                            config_end_date,
                                            vpn_config,
                                            created_at,
                                            has_free_trial,
                                            limit_ip,
                                            limit_ip_end_date
                                        FROM users
                                        WHERE user_id = $1
                                        """, user_id)
    
            if row:
                return dict(row)
            return None
    
    async def get_username_full_info(self, user_name: str):
        #Вся инфформация пользователя
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                                        SELECT
                                            user_id,
                                            username,
                                            balance,
                                            config_start_date,
                                            config_end_date,
                                            vpn_config,
                                            created_at,
                                            has_free_trial,
                                            limit_ip,
                                            limit_ip_end_date
                                        FROM users
                                        WHERE username = $1
                                        """, user_name)
    
            if row:
                return dict(row)
            return None
        
    async def delite_user(self, username: str) -> bool:
        try:
            async with self.get_connection() as conn:
               result = await conn.execute("""
                   DELETE FROM users 
                   WHERE username = $1
               """, username)
        except Exception as e:
            print(f'Ошибка при удалении: {e}')

    async def delete_user_config(self, username: int) -> bool:
        async with self.get_connection() as conn:
            result = await conn.execute("""
                UPDATE users 
                SET vpn_config = NULL
                WHERE username = $1
            """, username)
    
    async def set_free_trial_true(self, user_id: int) -> bool:
        """Установить has_free_trial в True"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    UPDATE users 
                    SET has_free_trial = FALSE
                    WHERE user_id = $1
                """, user_id)
                return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
    
    async def check_free_trial(self, user_id: int) -> bool:
        """Проверить значение has_free_trial"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("""
                    SELECT has_free_trial FROM users WHERE user_id = $1
                """, user_id)
                return result  # Вернет True или False
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
    
    async def get_all_usernames(self) -> list:
        """Получить все username из БД"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT username FROM users WHERE username IS NOT NULL
                """)
                return [row['username'] for row in rows]
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
        
    async def status_limit_ip_end_date(self, username: int, ip: int, price: int):
        async with self.get_connection() as conn:
            # Получаем пользователя по username
            user = await conn.fetchrow("""
            SELECT user_id, balance, limit_ip, limit_ip_end_date, config_end_date 
            FROM users WHERE username = $1
        """, username)

            if user['balance'] < price:
                return False
            
            await conn.execute("""
            UPDATE users 
            SET balance = balance - $1 
            WHERE username = $2
            """, price, username)

            new_limit_ip = (user['limit_ip'] or 1) + ip
            limit_ip_end_date = user['limit_ip_end_date']
            now = datetime.now(pytz.timezone('Europe/Moscow'))

            if limit_ip_end_date and limit_ip_end_date > now:
                new_limit_ip_end_date = limit_ip_end_date
            else:
                # Устанавливаем дату окончания подписки
                new_limit_ip_end_date = user['config_end_date']

            await conn.execute("""
            UPDATE users 
            SET limit_ip = $1,
                limit_ip_end_date = $2
            WHERE username = $3
        """, new_limit_ip, new_limit_ip_end_date, username)

            return True

    async def limit_ip_date_admin(self, username: str, days: int):
        async with self.get_connection() as conn:
            # Получаем пользователя
            user = await conn.fetchrow("""
                SELECT user_id, limit_ip_end_date, config_end_date 
                FROM users 
                WHERE username = $1
            """, username)

            if not user:
                return False, f"❌ Пользователь {username} не найден"
            
            now = datetime.now(pytz.timezone('Europe/Moscow'))
            limit_ip_end_date = user['limit_ip_end_date']
            config_end_date = user['config_end_date']

            if limit_ip_end_date and limit_ip_end_date > now:
                new_limit_date = limit_ip_end_date + timedelta(days=days)

            else:
                new_limit_date = now + timedelta(days=days)

            await conn.execute("""
                UPDATE users 
                SET limit_ip_end_date = $1
                WHERE username = $2
                """, new_limit_date, username)