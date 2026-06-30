import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

import config
from database.db import init_db
import handlers
import admin_handlers
from scheduler import run_reminders_scheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)


async def main():
    # Инициализация базы данных
    await init_db()
    
    # Синхронизация и загрузка тегов из БД
    from database.db import async_session
    from database.models import SystemTag
    from sqlalchemy import select
    
    async with async_session() as session:
        result = await session.execute(select(SystemTag))
        db_tags = result.scalars().all()
        if not db_tags:
            print("База данных тегов пуста. Заполняем дефолтными тегами...")
            for tag_name in config.DEFAULT_TAGS:
                session.add(SystemTag(name=tag_name))
            await session.commit()
            result = await session.execute(select(SystemTag))
            db_tags = result.scalars().all()
        config.DEFAULT_TAGS = [t.name for t in db_tags]
        print(f"Загружено тегов из БД: {len(config.DEFAULT_TAGS)}")
    
    # Создание бота с использованием DefaultBotProperties для настройки parse_mode
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация роутеров
    dp.include_router(admin_handlers.router)
    dp.include_router(handlers.router)
    
    print("Бот запускается...")
    
    # Запускаем фоновые задачи (напоминания)
    asyncio.create_task(run_reminders_scheduler(bot))
    
    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
