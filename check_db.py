import asyncio
from database.db import init_db, async_session
from database.models import User, Event, Registration
from config import is_super_admin

async def test():
    print("Инициализация базы данных...")
    await init_db()
    print("База данных успешно инициализирована!")

    print("\nПроверка логики суперадмина:")
    admins_to_test = ["@ASaavedraA", "ASaavedraA", "@other_user", "other_user", None]
    for username in admins_to_test:
        print(f"Пользователь '{username}' суперадмин? -> {is_super_admin(username)}")

    async with async_session() as session:
        print("\nСоздание тестового пользователя...")
        new_user = User(telegram_id=123456789, username="test_user")
        session.add(new_user)
        await session.commit()
        print("Пользователь успешно создан!")

        # Извлекаем пользователя и проверяем значения по умолчанию
        db_user = await session.get(User, 123456789)
        print(f"Проверка default тегов: {db_user.tags_preferences}")
        print(f"Проверка default уведомлений: {db_user.notification_preferences}")

        print("\nСоздание тестового мероприятия...")
        new_event = Event(
            title="Выставка графического дизайна",
            date="10.06.2026",
            time="18:00",
            address="Покровский бульвар, 11",
            tags=["Дизайн", "Искусство"],
            images=["image_file_id_123"]
        )
        session.add(new_event)
        await session.commit()
        print(f"Мероприятие создано: {new_event}")

        print("\nСоздание тестовой регистрации...")
        new_reg = Registration(
            user_id=db_user.telegram_id,
            event_id=new_event.id,
            status="очно"
        )
        session.add(new_reg)
        await session.commit()
        print("Регистрация успешно создана!")

        # Очистка базы данных после теста
        await session.delete(new_reg)
        await session.delete(db_user)
        await session.delete(new_event)
        await session.commit()
        print("\nТестовые данные успешно очищены.")

if __name__ == "__main__":
    asyncio.run(test())
