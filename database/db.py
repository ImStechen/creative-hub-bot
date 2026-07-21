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

async def init_db():
    """
    Инициализация базы данных: создание всех таблиц.
    """
    async with engine.begin() as conn:
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
            
        # Миграция: Проверка наличия колонок фотографа в таблице events
        cursor_ev = await conn.execute(text("PRAGMA table_info(events)"))
        ev_columns = [row[1] for row in cursor_ev.fetchall()]
        if "photographer_name" not in ev_columns:
            await conn.execute(text("ALTER TABLE events ADD COLUMN photographer_name TEXT"))
        if "photographer_url" not in ev_columns:
            await conn.execute(text("ALTER TABLE events ADD COLUMN photographer_url TEXT"))

        # Миграция: Проверка наличия колонки tag в таблице series_events
        cursor_se = await conn.execute(text("PRAGMA table_info(series_events)"))
        se_columns = [row[1] for row in cursor_se.fetchall()]
        if se_columns and "tag" not in se_columns:
            await conn.execute(text("ALTER TABLE series_events ADD COLUMN tag TEXT"))
