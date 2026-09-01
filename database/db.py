from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config import DATABASE_URL

# Создание асинхронного движка
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()


from sqlalchemy import text
from datetime import datetime

async def _add_column_if_missing(conn, table: str, column: str, ddl: str):
    cursor = await conn.execute(text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in cursor.fetchall()]
    if columns and column not in columns:
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


async def init_db():
    """
    Инициализация базы данных: создание всех таблиц.
    """
    async with engine.begin() as conn:
        # Включаем WAL-режим SQLite для защиты от блокировок при параллельных запросах
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(Base.metadata.create_all)
        
        # Миграция: Проверка наличия колонки created_at в таблице users
        cursor = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in cursor.fetchall()]
        if "created_at" not in columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN created_at TEXT"))
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await conn.execute(
                text("UPDATE users SET created_at = :now WHERE created_at IS NULL"),
                {"now": now_str}
            )
            
        await _add_column_if_missing(conn, "events", "photographer_name", "photographer_name TEXT")
        await _add_column_if_missing(conn, "events", "photographer_url", "photographer_url TEXT")
        await _add_column_if_missing(conn, "series_events", "tag", "tag TEXT")
        await _add_column_if_missing(conn, "admins", "telegram_id", "telegram_id INTEGER")
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_admins_telegram_id ON admins(telegram_id)"))
        await _add_column_if_missing(conn, "series_event_registrations", "reminded_24h", "reminded_24h INTEGER NOT NULL DEFAULT 0")
        await _add_column_if_missing(conn, "series_event_registrations", "reminded_2h", "reminded_2h INTEGER NOT NULL DEFAULT 0")
