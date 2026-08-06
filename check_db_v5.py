import asyncio
import config
config.DATABASE_URL = "sqlite+aiosqlite:///test_creative_hub.db"

from database.db import init_db, async_session
from database.models import User, Event, Registration, Raffle, Admin
from check_db_v3 import DummyMessage, DummyState
from admin_handlers import is_user_admin

class DummyCallbackQuery:
    def __init__(self, data, from_user_id, from_username, message):
        self.data = data
        self.from_user = DummyUser(from_user_id, from_username)
        self.message = message
        self.answered = False
        self.answer_text = ""

    async def answer(self, text="", show_alert=False):
        self.answered = True
        self.answer_text = text
        print(f"[CALLBACK ANSWERED] (alert={show_alert}): {text}")

class DummyUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username

async def test():
    print("Инициализация базы данных...")
    await init_db()

    async with async_session() as session:
        # Очистим таблицы
        await session.execute(User.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(Registration.__table__.delete())
        await session.execute(Raffle.__table__.delete())
        await session.execute(Admin.__table__.delete())
        await session.commit()

        # Создадим суперадмина и обычного пользователя
        super_admin_username = "ASaavedraA"
        normal_username = "some_random_user"

        print("\n=== ТЕСТ 1: Проверка прав доступа ===")
        print(f"Имеет ли доступ суперадмин @{super_admin_username}? -> {await is_user_admin(super_admin_username, session)}")
        print(f"Имеет ли доступ обычный пользователь @{normal_username}? -> {await is_user_admin(normal_username, session)}")

        # Добавим дополнительного админа в БД
        new_admin = Admin(username="assistant_admin")
        session.add(new_admin)
        await session.commit()
        print(f"Имеет ли доступ добавленный админ @assistant_admin? -> {await is_user_admin('assistant_admin', session)}")

        # Импортируем админ-хэндлеры
        from admin_handlers import (
            process_admin_menu,
            process_save_tag,
            process_admin_confirm_del_tag,
            process_save_admin_rights,
            process_admin_del_rights
        )

        print("\n=== ТЕСТ 2: Заход в админ-панель ===")
        # От лица обычного пользователя
        msg_user = DummyMessage(from_user_id=111, from_username="regular_user")
        cb_user = DummyCallbackQuery("btn_admin", 111, "regular_user", msg_user)
        state = DummyState()
        await process_admin_menu(cb_user, state)
        # Должен быть отказ в доступе (answered=True с предупреждением)

        # От лица суперадмина
        msg_admin = DummyMessage(from_user_id=999, from_username="ASaavedraA")
        cb_admin = DummyCallbackQuery("btn_admin", 999, "ASaavedraA", msg_admin)
        await process_admin_menu(cb_admin, state)
        # Должна успешно отрисоваться клавиатура главного меню админки

        print("\n=== ТЕСТ 3: Каскадное удаление тега ===")
        # 1. Создаем пользователя с тегами
        user = User(telegram_id=777, username="test_tag_cascade")
        session.add(user)
        
        # 2. Создаем мероприятие с тегами
        import config
        config.DEFAULT_TAGS.append("УдаляемыйТег")
        event = Event(
            title="Событие под удаление тега",
            date="20.06.2026",
            time="12:00",
            address="Покровка",
            tags=["Дизайн", "УдаляемыйТег"],
            photos_url="http://url" # Чтобы числилось как архивное
        )
        session.add(event)
        await session.commit()
        
        # Обновим теги у пользователя, добавив "УдаляемыйТег": True
        db_user = await session.get(User, 777)
        prefs = dict(db_user.tags_preferences)
        prefs["УдаляемыйТег"] = True
        db_user.tags_preferences = prefs
        session.add(db_user)
        await session.commit()

        print(f"Теги пользователя перед удалением: {db_user.tags_preferences}")
        print(f"Теги мероприятия перед удалением: {event.tags}")

        # Симулируем удаление тега админом
        cb_del_tag = DummyCallbackQuery("admin_confirm_del_tag_УдаляемыйТег", 999, "ASaavedraA", msg_admin)
        await process_admin_confirm_del_tag(cb_del_tag)

        # Проверяем каскадное удаление тега
        await session.refresh(db_user)
        await session.refresh(event)
        print(f"Теги пользователя после удаления тега: {db_user.tags_preferences}")
        print(f"Теги мероприятия после удаления тега: {event.tags}")

        print("\n=== ТЕСТ 4: Права администратора (защита от удаления суперадмина) ===")
        # Добавим админа с никнеймом суперадмина в БД (в теории невозможно через интерфейс, проверим защиту кода)
        fake_super = Admin(username="ASaavedraA")
        session.add(fake_super)
        await session.commit()

        cb_del_admin = DummyCallbackQuery(f"admin_del_rights_{fake_super.id}", 999, "ASaavedraA", msg_admin)
        await process_admin_del_rights(cb_del_admin)
        # Должен сработать триггер защиты (callback answered с ошибкой)

        # Удаляем обычного ассистента
        cb_del_assistant = DummyCallbackQuery(f"admin_del_rights_{new_admin.id}", 999, "ASaavedraA", msg_admin)
        await process_admin_del_rights(cb_del_assistant)
        # Должно успешно удалиться

        # Очистим таблицы в конце теста, чтобы не засорять БД пользователя
        await session.execute(User.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(Registration.__table__.delete())
        await session.execute(Raffle.__table__.delete())
        await session.execute(Admin.__table__.delete())
        from database.models import SystemTag
        await session.execute(SystemTag.__table__.delete())
        await session.commit()
        print("База данных успешно очищена после выполнения тестов.")

if __name__ == "__main__":
    asyncio.run(test())
