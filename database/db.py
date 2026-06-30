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


async def init_db():
    """
    Инициализация базы данных: создание всех таблиц.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
