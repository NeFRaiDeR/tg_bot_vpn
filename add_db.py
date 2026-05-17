import asyncio
import os
from config import *
from bd.db import DB
from datetime import datetime



async def create_table():

    await database.connect()
    
    async with database.get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    config_start_date TIMESTAMP WITH TIME ZONE,
                    config_end_date TIMESTAMP WITH TIME ZONE,
                    vpn_config TEXT,
                    balance DECIMAL(10, 2) DEFAULT 0.00,
                    limit_ip INTEGER DEFAULT 1,
                    limit_ip_end_date TIMESTAMP WITH TIME ZONE,
                    has_free_trial BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Moscow'))
                               """)
    
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(create_table())