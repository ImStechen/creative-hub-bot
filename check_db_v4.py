import asyncio
from database.db import init_db, async_session
from database.models import User, Event, Registration, Raffle
from handlers import show_main_page

class DummyCallbackQuery:
    def __init__(self, data, from_user_id, from_username, message):
        self.data = data
        self.from_user = DummyUser(from_user_id, from_username)
        self.message = message
        self.answered = False
        self.answer_text = ""

    async def answer(self, text=""):
        self.answered = True
        self.answer_text = text
        print(f"[CALLBACK ANSWERED]: {text}")

class DummyMessage:
    def __init__(self, from_user_id, from_username, photo=None):
        self.from_user = DummyUser(from_user_id, from_username)
        self.photo = photo
        self.sent_messages = []
        self.deleted = False

    async def answer(self, text, reply_markup=None, parse_mode=None, disable_web_page_preview=False):
        self.sent_messages.append((text, reply_markup))
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ОТПРАВЛЕНО СООБЩЕНИЕ]:\n{safe_text}")
        if reply_markup:
            print("Клавиатура:")
            for row in reply_markup.inline_keyboard:
                row_str = " | ".join([btn.text.encode('ascii', errors='replace').decode('ascii') for btn in row])
                print(f"  [{row_str}]")

    async def delete(self):
        self.deleted = True
        print("[СООБЩЕНИЕ УДАЛЕНО]")

    async def edit_text(self, text, reply_markup=None, parse_mode=None, disable_web_page_preview=False):
        self.sent_messages.append((text, reply_markup))
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ОБНОВЛЕН ТЕКСТ СООБЩЕНИЯ]:\n{safe_text}")
        if reply_markup:
            print("Клавиатура:")
            for row in reply_markup.inline_keyboard:
                row_str = " | ".join([btn.text.encode('ascii', errors='replace').decode('ascii') for btn in row])
                print(f"  [{row_str}]")

class DummyUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username

class DummyState:
    def __init__(self):
        self.state = None
        self.data = {}

    async def set_state(self, state):
        self.state = state

    async def get_data(self):
        return self.data

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def clear(self):
        self.state = None
        self.data = {}

async def test():
    print("Инициализация базы данных...")
    await init_db()

    async with async_session() as session:
        # Очистим таблицы
        await session.execute(User.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(Registration.__table__.delete())
        await session.execute(Raffle.__table__.delete())
        await session.commit()

        # Создадим пользователя (все теги по умолчанию True)
        user = User(telegram_id=888, username="regular_user")
        session.add(user)
        
        # Создадим прошедшее мероприятие с материалами
        event = Event(
            id=101,
            title="Мастер-класс по Cinema 4D",
            date="20.05.2026",
            time="18:00",
            address="Покровка",
            tags=["Дизайн", "Кино"],
            photos_url="https://photos.com/c4d",
            stream_record_url="https://youtube.com/c4d_record",
            article_url="https://habr.com/c4d"
        )
        # Создадим мероприятие без материалов
        event_no_materials = Event(
            id=102,
            title="Лекция без материалов",
            date="21.05.2026",
            time="18:00",
            address="Покровка",
            tags=["Дизайн"]
        )
        session.add_all([event, event_no_materials])
        await session.commit()

        # Создадим розыгрыш, привязанный к событию 101 (мастер-класс по Cinema 4D, теги Дизайн, Кино)
        raffle = Raffle(
            title="Розыгрыш лицензий Cinema 4D",
            description="Разыгрываем 3 лицензии среди участников!",
            url="https://raffle.com/c4d",
            is_active=1,
            event_id=101
        )
        session.add(raffle)
        await session.commit()

        # Импортируем хэндлеры Блока 4
        from handlers import (
            process_archive_menu,
            process_archive_tag_selection,
            process_archive_event_detail,
            process_raffle_info
        )

        print("\n=== ТЕСТ 1: Переход в Архив пост-материалов ===")
        msg = DummyMessage(from_user_id=888, from_username="regular_user")
        cb = DummyCallbackQuery("btn_archive", 888, "regular_user", msg)
        state = DummyState()
        await process_archive_menu(cb, state)

        print("\n=== ТЕСТ 2: Выбор тега 'Дизайн' ===")
        cb2 = DummyCallbackQuery("arch_tag_Дизайн", 888, "regular_user", msg)
        await process_archive_tag_selection(cb2)
        # Должен отобразиться только "Мастер-класс по Cinema 4D" (id=101), так как у 102 нет пост-материалов

        print("\n=== ТЕСТ 3: Выбор конкретного архивного мероприятия ===")
        cb3 = DummyCallbackQuery("arch_event_101", 888, "regular_user", msg)
        await process_archive_event_detail(cb3)

        print("\n=== ТЕСТ 4: Переход на Главный экран для проверки видимости кнопки Розыгрыш ===")
        # У юзера включены все теги (включая Дизайн/Кино). Кнопка Розыгрыш должна отображаться.
        await show_main_page(msg, 888, "regular_user", session)

        print("\n=== ТЕСТ 5: Открытие Розыгрыша ===")
        cb_raffle = DummyCallbackQuery("btn_raffle", 888, "regular_user", msg)
        await process_raffle_info(cb_raffle)

        print("\n=== ТЕСТ 6: Смена тегов юзера и проверка скрытия кнопки Розыгрыш ===")
        # Отключаем теги Дизайн и Кино
        db_user = await session.get(User, 888)
        prefs = dict(db_user.tags_preferences)
        prefs["Дизайн"] = False
        prefs["Кино"] = False
        db_user.tags_preferences = prefs
        session.add(db_user)
        await session.commit()

        # Кнопка Розыгрыш теперь должна пропасть на Главной
        msg_hidden = DummyMessage(from_user_id=888, from_username="regular_user")
        await show_main_page(msg_hidden, 888, "regular_user", session)

if __name__ == "__main__":
    asyncio.run(test())
