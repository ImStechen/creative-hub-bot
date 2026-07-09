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
import os
import shutil
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)


def make_db_backup():
    data_dir = os.getenv('DATA_DIR', '.')
    db_path = os.path.join(data_dir, 'creative_hub.db')
    
    if os.path.exists(db_path):
        backup_dir = os.path.join(data_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(backup_dir, f"creative_hub_{date_str}.db")
        
        try:
            shutil.copy2(db_path, backup_path)
            logging.info(f"Резервная копия базы данных успешно создана: {backup_path}")
        except Exception as e:
            logging.error(f"Ошибка при создании бэкапа базы данных: {e}")


async def main():
    # Создание резервной копии базы данных перед запуском
    make_db_backup()
    
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
