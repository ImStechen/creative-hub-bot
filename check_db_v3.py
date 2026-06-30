import asyncio
from database.db import init_db, async_session
from database.models import User, Event, Registration, Raffle
from handlers import show_main_page
from keyboards import get_checkbox_keyboard

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

    async def answer_photo(self, photo, caption, reply_markup=None, parse_mode=None):
        self.sent_messages.append((caption, reply_markup))
        safe_caption = caption.encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ОТПРАВЛЕНО ФОТО С ОПИСАНИЕМ]:\n{safe_caption}")
        if reply_markup:
            print("Клавиатура:")
            for row in reply_markup.inline_keyboard:
                row_str = " | ".join([btn.text.encode('ascii', errors='replace').decode('ascii') for btn in row])
                print(f"  [{row_str}]")

    async def delete(self):
        self.deleted = True
        print("[СООБЩЕНИЕ УДАЛЕНО]")

    async def edit_text(self, text, reply_markup=None):
        self.sent_messages.append((text, reply_markup))
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(f"\n[ОБНОВЛЕН ТЕКСТ СООБЩЕНИЯ]:\n{safe_text}")
        if reply_markup:
            print("Клавиатура:")
            for row in reply_markup.inline_keyboard:
                row_str = " | ".join([btn.text.encode('ascii', errors='replace').decode('ascii') for btn in row])
                print(f"  [{row_str}]")

    async def edit_reply_markup(self, reply_markup=None):
        self.sent_messages.append(("", reply_markup))
        print("\n[ОБНОВЛЕНА КЛАВИАТУРА]")
        if reply_markup:
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
        await session.commit()

        # Создадим пользователя
        user = User(telegram_id=999, username="user_path_test")
        session.add(user)
        
        # Создадим мероприятие
        event = Event(
            id=10,
            title="Дизайн-хакатон",
            title_url="https://design.ru",
            date="20.06.2026",
            time="10:00",
            address="Покровский бульвар",
            tags=["Дизайн"],
            images=["img_id_999"]
        )
        session.add(event)
        await session.commit()

        # Импортируем хэндлеры
        from handlers import (
            process_events_info,
            process_show_event,
            process_registration_status,
            process_pref_tags,
            process_checkbox_toggle,
            process_save_preferences
        )

        print("\n=== ТЕСТ 1: Переход в меню 'Подробнее о мероприятиях' ===")
        msg = DummyMessage(from_user_id=999, from_username="user_path_test")
        cb = DummyCallbackQuery("btn_events_info", 999, "user_path_test", msg)
        state = DummyState()
        await process_events_info(cb, state)

        print("\n=== ТЕСТ 2: Открытие конкретного мероприятия ===")
        msg2 = DummyMessage(from_user_id=999, from_username="user_path_test")
        cb2 = DummyCallbackQuery("show_event_10", 999, "user_path_test", msg2)
        await process_show_event(cb2)

        print("\n=== ТЕСТ 3: Выбор статуса присутствия ('очно') ===")
        msg3 = DummyMessage(from_user_id=999, from_username="user_path_test")
        cb3 = DummyCallbackQuery("reg_status_10_очно", 999, "user_path_test", msg3)
        await process_registration_status(cb3)

        # Проверяем запись в БД
        reg_check = await session.get(Registration, (999, 10))
        print(f"Статус записи в БД: {reg_check.status if reg_check else 'ОТСУТСТВУЕТ'}")

        print("\n=== ТЕСТ 4: Переход в настройки тегов ===")
        msg4 = DummyMessage(from_user_id=999, from_username="user_path_test")
        cb4 = DummyCallbackQuery("pref_tags", 999, "user_path_test", msg4)
        await process_pref_tags(cb4, state)

        print("\n=== ТЕСТ 5: Изменение чекбокса ('Дизайн') ===")
        # Симулируем клик по тегу Дизайн
        cb5 = DummyCallbackQuery("cb_tags_Дизайн", 999, "user_path_test", msg4)
        await process_checkbox_toggle(cb5, state)
        
        print("\n=== ТЕСТ 6: Сохранение настроек ===")
        cb6 = DummyCallbackQuery("save_tags", 999, "user_path_test", msg4)
        await process_save_preferences(cb6, state)
        
        # Проверяем в БД
        db_user = await session.get(User, 999)
        print(f"Обновленные теги пользователя в БД: {db_user.tags_preferences}")

if __name__ == "__main__":
    asyncio.run(test())
