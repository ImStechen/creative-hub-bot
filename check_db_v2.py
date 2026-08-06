import asyncio
from database.db import init_db, async_session
from database.models import User, Event, Registration, Raffle
from config import is_super_admin
from keyboards import get_main_menu_keyboard

class DummyMessage:
    def __init__(self, from_user_id, from_username):
        self.from_user = DummyUser(from_user_id, from_username)
        self.sent_messages = []

    async def answer(self, text, reply_markup=None, disable_web_page_preview=False):
        self.sent_messages.append((text, reply_markup))
        # Избегаем UnicodeEncodeError на Windows-консоли при выводе эмодзи
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ОТПРАВЛЕНО СООБЩЕНИЕ]:\n{safe_text}")
        if reply_markup:
            print("Клавиатура:")
            for row in reply_markup.inline_keyboard:
                row_str = " | ".join([btn.text.encode('ascii', errors='replace').decode('ascii') for btn in row])
                print(f"  [{row_str}]")

class DummyUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username

async def test():
    print("Инициализация базы данных...")
    await init_db()
    
    async with async_session() as session:
        # Очистим таблицы от прошлых тестов
        await session.execute(User.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(Raffle.__table__.delete())
        await session.commit()

        # Создадим несколько мероприятий
        event1 = Event(
            title="Лекция по искусству",
            title_url="https://art-lecture.ru",
            date="15.06.2026",
            time="19:00",
            address="Покровка",
            tags=["Искусство", "Лекции"],
            hide_date="16.06.2026",
            hide_time="00:00"
        )
        event2 = Event(
            title="Кинопоказ",
            title_url="https://cinema.ru",
            date="16.06.2026",
            time="20:00",
            address="Покровка",
            tags=["Кино"],
            hide_date="17.06.2026",
            hide_time="00:00"
        )
        event_hidden = Event(
            title="Прошедшее событие",
            title_url=None,
            date="01.06.2026",
            time="12:00",
            address="Покровка",
            tags=["Медиа"],
            hide_date="02.06.2026",
            hide_time="00:00"
        )
        session.add_all([event1, event2, event_hidden])
        await session.commit()

        # 1. Симулируем /start для обычного пользователя
        print("\n=== ТЕСТ 1: Обычный пользователь запускает бота ===")
        msg1 = DummyMessage(from_user_id=55555, from_username="regular_user")
        
        # Симулируем handlers.cmd_start
        db_user = await session.get(User, msg1.from_user.id)
        if not db_user:
            db_user = User(telegram_id=msg1.from_user.id, username=msg1.from_user.username)
            session.add(db_user)
            await session.commit()
            print(f"Пользователь создан с тегами: {db_user.tags_preferences}")
        
        from handlers import show_main_page
        await show_main_page(msg1, msg1.from_user.id, msg1.from_user.username, session)

        # 2. Симулируем /start для суперадминистратора и при наличии активного розыгрыша
        print("\n=== ТЕСТ 2: Суперадмин запускает бота при активном розыгрыше ===")
        raffle = Raffle(title="Розыгрыш мерча", is_active=1)
        session.add(raffle)
        await session.commit()

        msg_admin = DummyMessage(from_user_id=11111, from_username="ASaavedraA")
        db_admin = await session.get(User, msg_admin.from_user.id)
        if not db_admin:
            db_admin = User(telegram_id=msg_admin.from_user.id, username=msg_admin.from_user.username)
            session.add(db_admin)
            await session.commit()
            
        await show_main_page(msg_admin, msg_admin.from_user.id, msg_admin.from_user.username, session)

        # 3. Изменим предпочтения пользователя, отключив тег "Искусство" и "Лекции"
        print("\n=== ТЕСТ 3: Изменение предпочтений пользователя (отключили 'Искусство' и 'Лекции') ===")
        db_user = await session.get(User, 55555)
        prefs = dict(db_user.tags_preferences)
        prefs["Искусство"] = False
        prefs["Лекции"] = False
        db_user.tags_preferences = prefs
        session.add(db_user)
        await session.commit()

        msg3 = DummyMessage(from_user_id=55555, from_username="regular_user")
        await show_main_page(msg3, msg3.from_user.id, msg3.from_user.username, session)

if __name__ == "__main__":
    asyncio.run(test())
