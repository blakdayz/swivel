import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.ble_dto import Device

DATABASE_URL = "sqlite+aiosqlite:///bluetooth_devices.db"
async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)
