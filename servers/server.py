import uuid
import pytz
import time
import asyncio
from config import *
from py3xui import AsyncApi, Client
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

class XUIAPIManager:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.api: Optional[AsyncApi] = None
        self._is_logged_in = False
    async def connect(self):
        if not self._is_logged_in:  
            self.api = AsyncApi(self.base_url, self.username, self.password)
            await self.api.login()
            self._is_logged_in = True

    async def find_or_create_client(self, email: str, inbound_id: int) -> Tuple[bool, Client, str]:

        await self.connect() #Здесь мы обращаемся к функции данного класса для того что бы обеспечить соединение
        try:
            await self.api.client.get_by_email(email)
            return True
        except Exception as e:
            await self.create_user(email, inbound_id)
            return False

    async def create_user(self, name: str, inbound_id: int):
        await self.connect()

        await self.api.inbound.get_by_id(inbound_id)
        expiry_time = int((datetime.now() + timedelta(days=7)).timestamp() * 1000)
        new_client = Client(
                id=str(uuid.uuid4()),  # Генерируем уникальный UUID
                email=name,  # Используем переданное имя как email
                enable=True,
                flow="xtls-rprx-vision",  # Flow для VLESS
                total_gb=0,  # 0 = безлимитный трафик
                expiry_time=1,  # 0 = бессрочный доступ
            )
        
        await self.api.client.add(inbound_id, [new_client])

    async def config(self, mail: str) -> str:

        client = await self.api.client.get_by_email(mail)
        inbound = None
        inbounds = await self.api.inbound.get_list()

        for ib in inbounds:
            for cl in ib.settings.clients:
                if cl.email == mail:
                    inbound = ib
                    break
            if inbound:
                break

        flow = None

        for ib in inbound.settings.clients:
            if ib.email == mail:
                flow = ib.flow
                break
        if inbound and inbound.protocol == "vless":
            public_key = inbound.stream_settings.reality_settings['settings']['publicKey']
            fingerprint = inbound.stream_settings.reality_settings['settings']['fingerprint']
            
            server_name = inbound.stream_settings.reality_settings.get("serverNames", [""])[0]
            short_id = inbound.stream_settings.reality_settings.get("shortIds", [""])[0]
            port = inbound.port

        connection_string = (
            f"vless://{client.uuid}@{server_ip}:{port}?"
            f"security={inbound.stream_settings.security}&"  # параметр security идет первым
            f"encryption=none&"   # добавлен encryption
            f"pbk={public_key}&"
            f"headerType=none&"   # добавлен headerType
            f"fp={fingerprint}&"
            f"spx=%2F&"           # spx в другом месте
            f"type=tcp&"
            f"flow={flow}&"  # добавлен flow
            f"sni={server_name}&"
            f"sid={short_id}"
            f"#{inbound.remark.replace(' ', '%20')}-{mail}"  # кодирование пробелов
        )
        
        
        return  connection_string
    
    async def extend_client(self, email: str, days: int, limit_ip: int, inbound_id: int = None):
        #ОНО РАБОТАЕТ перепроверь потом только на то что бы оно правильно начисляло время
        await self.connect()
        user_email = email
        inbound = await self.api.inbound.get_by_id(inbound_id)

        print(f"Inbound has {len(inbound.settings.clients)} clients")

        client = None
        for c in inbound.settings.clients:
            if c.email == user_email:
                client = c
                break
        
        if client:
            print(f"Found client with ID: {client.id}")  # ⬅️ The actual Client UUID.
        else:
            raise ValueError(f"Client with email {user_email} not found")
        
        cliend_uuid = client.id
        client_by_email = await self.api.client.get_by_email(user_email)
        print(f"Client by email has ID: {client_by_email.id}")

        current_expiry = client_by_email.expiry_time
        now_ms = int(datetime.now(pytz.utc).timestamp() * 1000)

        if current_expiry and current_expiry > now_ms:
            # Если подписка активна - добавляем дни к текущему сроку
            new_expiry = current_expiry + (days * 24 * 60 * 60 * 1000)
            print(f"Подписка активна, продлеваем с {datetime.fromtimestamp(current_expiry/1000)}")
        else:
            # Если подписка истекла или не установлена - начинаем с текущего момента
            new_expiry = now_ms + (days * 24 * 60 * 60 * 1000)
            print(f"Подписка истекла, начинаем с текущего момента")
        
        client_by_email.expiry_time = new_expiry
        client_by_email.limit_ip = limit_ip

        if not client_by_email.flow or client_by_email.flow != "xtls-rprx-vision":
            client_by_email.flow = "xtls-rprx-vision"
            print("Установлен flow: xtls-rprx-vision")

        client_by_email.id = cliend_uuid

        await self.api.client.update(client_by_email.id, client_by_email)

    async def off_user_comand(self, email, inbound_id):
        await self.connect()
        inbound = await self.api.inbound.get_by_id(inbound_id)

        client = None
        for c in inbound.settings.clients:
            if c.email == email:
                client = c
                break
        
        if not client:
            return f"❌ Клиент {email} не найден"

        client_uuid = client.id
        client_by_email = await self.api.client.get_by_email(email)

        if not client_by_email.flow or client_by_email.flow != "xtls-rprx-vision":
            client_by_email.flow = "xtls-rprx-vision"

        client_by_email.enable = False
        client_by_email.id = client_uuid

        await self.api.client.update(client_by_email.id, client_by_email)

        return f"✅ Клиент {email} отключен"
    
    async def delite_user(self, email: str, inbound_id):
        await self.connect()
        try:
            # Способ 1: через client.delete
            inbound = await self.api.inbound.get_by_id(inbound_id)
            inbound.settings.clients = [c for c in inbound.settings.clients if c.email != email]
            await self.api.inbound.update(inbound_id, inbound)
            
        
        except Exception as e:
            return f"❌ Ошибка при удалении: {e}"
    
    async def sync_all_users_expiry(self):
        """Синхронизировать даты окончания подписки для всех пользователей"""
        await self.connect()
        
        # Получаем всех пользователей из БД с активной подпиской
        async with database.get_connection() as conn:
            users = await conn.fetch("""
                SELECT username, config_end_date 
                FROM users 
                WHERE username IS NOT NULL 
                AND config_end_date IS NOT NULL
                AND config_end_date > CURRENT_TIMESTAMP
            """)
        
        if not users:
            print("Нет пользователей с активной подпиской")
            return
        
        success_count = 0
        error_count = 0
        
        for user in users:
            username = user['username']
            end_date = user['config_end_date']
            
            try:
                # Проверяем, существует ли клиент в панели
                try:
                    client = await self.api.client.get_by_email(username)
                except:
                    # Если клиента нет, создаем
                    await self.create_user(username, 1)
                    client = await self.api.client.get_by_email(username)
                
                # Конвертируем дату в timestamp (в миллисекундах)
                moscow_tz = pytz.timezone('Etc/GMT-3')
                now = datetime.now(moscow_tz)
                expiry_timestamp = (end_date - now).days
                await self.extend_client(username, expiry_timestamp, 1)

                user_data = await database.get_user_full_info(username)
                await self.extend_client_limit_ip(user_data['username'], user_data['limit_ip'], 1)
                
                print(f"✅ {username}: дата окончания установлена на {end_date}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {username}: ошибка - {e}")
                error_count += 1
        
        print(f"Синхронизация завершена. Успешно: {success_count}, Ошибок: {error_count}")

    async def extend_client_limit_ip(self, email: str, limit_ip: int, inbound_id: int = None):#Здесь изменяетя лимит ip
        await self.connect()
        user_email = email
        inbound = await self.api.inbound.get_by_id(inbound_id)
        client = None
        for c in inbound.settings.clients:
            if c.email == user_email:
                client = c
                break
            
        if client:
            print(f"Found client with ID: {client.id}")  # ⬅️ The actual Client UUID.
        else:
            raise ValueError(f"Client with email {user_email} not found")
        
        cliend_uuid = client.id
        client_by_email = await self.api.client.get_by_email(user_email)
        client_by_email.limit_ip = limit_ip

        if not client_by_email.flow or client_by_email.flow != "xtls-rprx-vision":
            client_by_email.flow = "xtls-rprx-vision"
            print("Установлен flow: xtls-rprx-vision")

        client_by_email.id = cliend_uuid
        await self.api.client.update(client_by_email.id, client_by_email)