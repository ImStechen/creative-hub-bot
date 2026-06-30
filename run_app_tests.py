import asyncio
import os
import sys
import json
import traceback
from datetime import datetime, timedelta
import config

# Use test database
config.DATABASE_URL = "sqlite+aiosqlite:///test_creative_hub.db"

# Reconfigure stdout to print utf-8
sys.stdout.reconfigure(encoding='utf-8')

from database.db import init_db, async_session
from database.models import User, Event, Registration, Raffle, Admin, SystemTag

# --- Mock Classes for Aiogram ---
class DummyUser:
    def __init__(self, id, username):
        self.id = id
        self.username = username

class DummyMessage:
    def __init__(self, from_user_id, from_username, text=""):
        self.from_user = DummyUser(from_user_id, from_username)
        self.text = text
        self.sent_messages = []
        self.deleted = False
        self.document = None

    async def answer(self, text, reply_markup=None, parse_mode=None, disable_web_page_preview=False):
        self.sent_messages.append((text, reply_markup))
        return self

    async def answer_photo(self, photo, caption, reply_markup=None, parse_mode=None):
        self.sent_messages.append((caption, reply_markup))
        return self

    async def delete(self):
        self.deleted = True

    async def edit_text(self, text, reply_markup=None):
        self.sent_messages.append((text, reply_markup))
        return self

    async def edit_reply_markup(self, reply_markup=None):
        self.sent_messages.append(("", reply_markup))

    async def answer_document(self, document, caption=None, reply_markup=None, parse_mode=None):
        self.sent_messages.append((caption or "", document, reply_markup))
        return self

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

class DummyBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=False, reply_markup=None):
        self.sent_messages.append((chat_id, text, reply_markup))
        return None

    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode=None):
        self.sent_messages.append((chat_id, caption, reply_markup))
        return None

# --- Import Bot Modules ---
import handlers
import admin_handlers
import scheduler
from keyboards import (
    get_main_menu_keyboard, get_events_list_keyboard, get_event_detail_keyboard,
    get_after_registration_keyboard, get_preferences_menu_keyboard, get_checkbox_keyboard,
    get_after_save_tags_keyboard, get_archive_tags_keyboard, get_archive_events_keyboard,
    get_archive_detail_keyboard, get_raffle_detail_keyboard
)
from admin_keyboards import (
    get_admin_main_keyboard, get_admin_tags_keyboard,
    get_admin_rights_keyboard, get_admin_raffles_keyboard, get_raffle_sections_keyboard,
    get_admin_events_keyboard, get_admin_delete_select_keyboard, get_post_mats_tags_keyboard
)

async def test_suite():
    print("Initializing test database...")
    await init_db()

    async with async_session() as session:
        # Clear tables
        await session.execute(User.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(Registration.__table__.delete())
        await session.execute(Raffle.__table__.delete())
        await session.execute(Admin.__table__.delete())
        await session.execute(SystemTag.__table__.delete())
        await session.commit()

        # Seed System Tags
        for tag in config.DEFAULT_TAGS:
            session.add(SystemTag(name=tag))
        await session.commit()

        # ----------------------------------------------------
        # 1. Test Keyboards
        # ----------------------------------------------------
        print("Testing keyboard generation functions...")
        k1 = get_main_menu_keyboard(is_admin=True, raffle_count=5)
        k2 = get_checkbox_keyboard({"Digital_Дизайн": True}, "tags")
        k3 = get_admin_main_keyboard()
        k4 = get_post_mats_tags_keyboard(config.DEFAULT_TAGS, is_delete=False)
        assert len(k1.inline_keyboard) > 0
        assert len(k2.inline_keyboard) > 0
        assert len(k3.inline_keyboard) > 0
        assert len(k4.inline_keyboard) > 0

        # ----------------------------------------------------
        # 2. Command /start and User Onboarding & FSM Registration
        # ----------------------------------------------------
        print("Testing /start handler and user onboarding...")
        msg = DummyMessage(from_user_id=123, from_username="john_doe")
        state = DummyState()
        await handlers.cmd_start(msg, state)
        
        # Verify user created in DB
        user = await session.get(User, 123)
        assert user is not None
        assert user.username == "john_doe"
        assert user.tags_preferences["Digital_Дизайн"] is True
        assert user.is_registered is False

        # Run FSM registration flow
        assert state.state == handlers.RegistrationStates.accept_agreement
        cb_accept = DummyCallbackQuery("reg_accept", 123, "john_doe", msg)
        await handlers.process_reg_accept(cb_accept, state)
        
        assert state.state == handlers.RegistrationStates.full_name
        await handlers.process_reg_full_name(DummyMessage(123, "john_doe", "Кузнецов Пётр"), state)
        assert state.state == handlers.RegistrationStates.email

        # Email validation failure
        await handlers.process_reg_email(DummyMessage(123, "john_doe", "invalid-email"), state)
        assert state.state == handlers.RegistrationStates.email

        # Valid email
        await handlers.process_reg_email(DummyMessage(123, "john_doe", "ivanov@example.com"), state)
        assert state.state == handlers.RegistrationStates.phone

        # Skip phone step to complete registration
        cb_skip_phone = DummyCallbackQuery("reg_skip_phone", 123, "john_doe", msg)
        await handlers.process_reg_skip_phone(cb_skip_phone, state)

        # Verify registration values
        await session.refresh(user)
        assert user.is_registered is True
        assert user.full_name == "Кузнецов Пётр"
        assert user.email == "ivanov@example.com"
        assert user.phone == "-"


        # ----------------------------------------------------
        # 3. Preference Toggling and Saving
        # ----------------------------------------------------
        print("Testing preference checkbox toggling...")
        cb_pref = DummyCallbackQuery("pref_tags", 123, "john_doe", msg)
        await handlers.process_pref_tags(cb_pref, state)

        # Toggle Digital_Дизайн (index 1)
        cb_toggle = DummyCallbackQuery("cb_tags_1", 123, "john_doe", msg)
        await handlers.process_checkbox_toggle(cb_toggle, state)

        # Toggle another tag to test multiple interactions
        cb_toggle2 = DummyCallbackQuery("cb_tags_3", 123, "john_doe", msg)
        await handlers.process_checkbox_toggle(cb_toggle2, state)

        # Save preferences
        cb_save = DummyCallbackQuery("save_tags", 123, "john_doe", msg)
        await handlers.process_save_preferences(cb_save, state)

        # Reload and check
        await session.refresh(user)
        assert user.tags_preferences["Digital_Дизайн"] is False
        assert user.tags_preferences["КреативныйБизнес"] is False

        # ----------------------------------------------------
        # 4. Events Lifecycle & Preferences Filtering
        # ----------------------------------------------------
        print("Testing events details & preferences filtering...")
        # Create an event matching user's disabled tag
        event_dis = Event(
            id=1,
            title="Digital design stuff",
            date="10.06.2026",
            time="12:00",
            address="HSE",
            tags=["Digital_Дизайн"]
        )
        # Create an event matching user's active tag
        event_act = Event(
            id=2,
            title="Science talk",
            date="11.06.2026",
            time="14:00",
            address="HSE Science Hall",
            tags=["Наука"]
        )
        session.add_all([event_dis, event_act])
        await session.commit()

        # Query events list
        cb_events = DummyCallbackQuery("btn_events_info", 123, "john_doe", msg)
        await handlers.process_events_info(cb_events, state)
        
        # Check that only event 2 is shown
        kb = msg.sent_messages[-1][1]
        btn_texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "Science talk" in btn_texts
        assert "Digital design stuff" not in btn_texts

        # ----------------------------------------------------
        # 5. Registrations (Очно / Удаленно / ... ) & Interception
        # ----------------------------------------------------
        print("Testing event registration status handling...")
        cb_reg = DummyCallbackQuery("reg_status_2_очно", 123, "john_doe", msg)
        await handlers.process_registration_status(cb_reg, state)

        reg = await session.get(Registration, (123, 2))
        assert reg is not None
        assert reg.status == "очно"
        assert reg.registration_date is not None

        # Test registration interception for unregistered user
        unreg_user = User(telegram_id=456, username="unreg_test")
        session.add(unreg_user)
        await session.commit()

        state2 = DummyState()
        cb_reg_unreg = DummyCallbackQuery("reg_status_2_удаленно", 456, "unreg_test", msg)
        await handlers.process_registration_status(cb_reg_unreg, state2)

        # Registration should be intercepted and FSM started
        assert state2.state == handlers.RegistrationStates.accept_agreement
        cb_accept2 = DummyCallbackQuery("reg_accept", 456, "unreg_test", msg)
        await handlers.process_reg_accept(cb_accept2, state2)

        assert state2.state == handlers.RegistrationStates.full_name
        reg_unreg_check = await session.get(Registration, (456, 2))
        assert reg_unreg_check is None

        # Complete registration for this user
        await handlers.process_reg_full_name(DummyMessage(456, "unreg_test", "Тестов Тест"), state2)
        await handlers.process_reg_email(DummyMessage(456, "unreg_test", "test@example.com"), state2)
        await handlers.process_reg_phone(DummyMessage(456, "unreg_test", "+79997777777"), state2)

        # Now registration should be automatically created after FSM finishes
        reg_unreg_check2 = await session.get(Registration, (456, 2))
        assert reg_unreg_check2 is not None
        assert reg_unreg_check2.status == "удаленно"
        assert reg_unreg_check2.registration_date is not None


        # Test change of status to "думаю" updates the registration status to "думаю" (remains in DB)
        cb_change_thinking = DummyCallbackQuery("reg_status_2_думаю", 456, "unreg_test", msg)
        await handlers.process_registration_status(cb_change_thinking, state2)
        session.expire_all()
        reg_unreg_thinking = await session.get(Registration, (456, 2))
        assert reg_unreg_thinking is not None
        assert reg_unreg_thinking.status == "думаю"

        # Test change of status to "не пойду" deletes the registration
        cb_change_nopgo = DummyCallbackQuery("reg_status_2_не пойду", 456, "unreg_test", msg)
        await handlers.process_registration_status(cb_change_nopgo, state2)
        session.expire_all()
        reg_unreg_deleted = await session.get(Registration, (456, 2))
        assert reg_unreg_deleted is None


        # ----------------------------------------------------
        # 6. Admin Authentication & Controls
        # ----------------------------------------------------
        print("Testing admin access controls...")
        normal_cb = DummyCallbackQuery("btn_admin", 123, "john_doe", msg)
        await admin_handlers.process_admin_menu(normal_cb, state)
        # Verify access denied alert was triggered
        assert normal_cb.answered is True
        assert "нет прав доступа" in normal_cb.answer_text.lower()

        # Admin user authentication (super admin configured in config)
        admin_cb = DummyCallbackQuery("btn_admin", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_menu(admin_cb, state)
        # Verify keyboard returned in admin_cb.message.sent_messages
        assert len(msg.sent_messages[-1][0]) > 0

        # ----------------------------------------------------
        # 7. Admin Tags CRUD
        # ----------------------------------------------------
        print("Testing admin tags CRUD...")
        # Create tag
        await admin_handlers.process_save_tag(DummyMessage(999, "ASaavedraA", "НовыйТестТаг"), state)
        # Confirm del tag with cascade validation
        del_cb = DummyCallbackQuery("admin_confirm_del_tag_НовыйТестТаг", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_confirm_del_tag(del_cb)

        # ----------------------------------------------------
        # 8. Admin Post-Materials CRUD
        # ----------------------------------------------------
        print("Testing admin post-materials addition/deletion...")
        # Simulate admin post-material state flow
        state_pm = DummyState()
        await state_pm.update_data(event_id=2)
        
        # Save photo url
        pm_msg = DummyMessage(999, "ASaavedraA", "https://photos.url/123")
        await state_pm.set_state(admin_handlers.PostMatsForm.photos_url)
        await admin_handlers.process_add_pm_photos(pm_msg, state_pm)

        # Skip stream record
        skip_cb = DummyCallbackQuery("skip_pm_stream", 999, "ASaavedraA", msg)
        await admin_handlers.process_skip_pm_stream(skip_cb, state_pm)

        # ----------------------------------------------------
        # 9. Scheduler Reminders
        # ----------------------------------------------------
        print("Testing scheduler reminders check...")
        mock_bot = DummyBot()
        
        # Calculate exactly 24 hours from now
        target_dt = datetime.now() + timedelta(hours=24)
        event_act.date = target_dt.strftime("%d.%m.%Y")
        event_act.time = target_dt.strftime("%H:%M")
        session.add(event_act)
        await session.commit()

        # Run scheduler tick
        await scheduler.check_and_send_reminders(mock_bot)
        assert len(mock_bot.sent_messages) > 0
        chat_id, text, kb = mock_bot.sent_messages[0]
        assert chat_id == 123
        assert "напоминание о мероприятии" in text.lower()
        assert kb is not None
        button_texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "Подробнее о мероприятии" in button_texts


        # ----------------------------------------------------
        # 10. Admin Archived Event Edit Flow
        # ----------------------------------------------------
        print("Testing admin archived event edit flow...")
        # Mark event_dis (Digital design stuff) as hidden by changing its date to past
        past_dt = datetime.now() - timedelta(days=5)
        event_dis.hide_date = past_dt.strftime("%d.%m.%Y")
        event_dis.hide_time = "12:00"
        session.add(event_dis)
        await session.commit()

        # Trigger "admin_edit_archive_tags"
        cb_archtags = DummyCallbackQuery("admin_edit_archive_tags", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_edit_archive_tags(cb_archtags)
        # Verify message popped up with options
        assert "Выберите тему" in msg.sent_messages[-1][0]

        # Trigger tag select (index 1 is Digital_Дизайн)
        cb_archtag_sel = DummyCallbackQuery("admin_archtag_1", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_archtag_select(cb_archtag_sel)
        # Verify event 1 is listed
        arch_kb = msg.sent_messages[-1][1]
        arch_btn_texts = [btn.text for row in arch_kb.inline_keyboard for btn in row]
        assert "Digital design stuff" in arch_btn_texts
        print("Admin archived event edit flow test PASSED!")

        # Delete test user 456 to prevent notification test interference
        u456 = await session.get(User, 456)
        if u456:
            await session.delete(u456)
            await session.commit()

        # ----------------------------------------------------
        # 11. Event and Raffle Creation Notifications
        # ----------------------------------------------------
        print("Testing event and raffle creation notifications...")
        mock_bot_creation = DummyBot()
        
        # Test Event Notification
        # user 123 has "Наука" enabled, should receive event_act notification
        await admin_handlers.send_event_creation_notifications(mock_bot_creation, event_act)
        assert len(mock_bot_creation.sent_messages) > 0
        assert mock_bot_creation.sent_messages[0][0] == 123
        assert "появилось мероприятие" in mock_bot_creation.sent_messages[0][1].lower()

        # Test Raffle Notification
        mock_bot_creation2 = DummyBot()
        # raffle is linked to event 100 which has tag "Digital_Дизайн"
        # user 123 has "Digital_Дизайн" disabled, should not receive it
        raffle_test = Raffle(
            id=300,
            title="Test Raffle Notification",
            description="Awesome description",
            is_active=1,
            event_id=1
        )
        await admin_handlers.send_raffle_creation_notifications(mock_bot_creation2, raffle_test)
        assert len(mock_bot_creation2.sent_messages) == 0

        # Change user 123 preferences to enable "Digital_Дизайн"
        user.tags_preferences = {k: True for k in config.DEFAULT_TAGS}
        session.add(user)
        await session.commit()

        await admin_handlers.send_raffle_creation_notifications(mock_bot_creation2, raffle_test)
        assert len(mock_bot_creation2.sent_messages) > 0
        assert "появился розыгрыш" in mock_bot_creation2.sent_messages[0][1].lower()
        print("Event and raffle creation notifications test PASSED!")

        # ----------------------------------------------------
        # 12. Admin Registrations Excel Export
        # ----------------------------------------------------
        print("Testing admin registrations Excel export...")
        # Trigger export select category
        cb_export = DummyCallbackQuery("admin_export_registrations", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_export_registrations(cb_export)
        assert "Выберите категорию" in msg.sent_messages[-1][0]

        # Trigger active events selection
        cb_export_act = DummyCallbackQuery("admin_export_select_active", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_export_select_active(cb_export_act)
        assert "Выберите активное мероприятие" in msg.sent_messages[-1][0]

        # Seed registrations with "думаю" and "очно" statuses to test sorting
        async with async_session() as test_session:
            # Let's clean up existing registrations for event 2
            await test_session.execute(Registration.__table__.delete().where(Registration.event_id == 2))
            
            # Add user 456
            u456 = await test_session.get(User, 456)
            if not u456:
                u456 = User(telegram_id=456, username="dummy456", full_name="Алексеев Алексей", is_registered=True, notification_preferences={}, tags_preferences={})
                test_session.add(u456)
            
            # Add "думаю" registration (first, so naturally it would be first without sorting)
            r_think = Registration(user_id=123, event_id=2, status="думаю", registration_date="25.06.2026")
            test_session.add(r_think)
            
            # Add "очно" registration (second)
            r_active = Registration(user_id=456, event_id=2, status="очно", registration_date="25.06.2026")
            test_session.add(r_active)
            await test_session.commit()

        # Trigger actual Excel file generation for event 2
        cb_export_ev = DummyCallbackQuery("admin_export_event_2", 999, "ASaavedraA", msg)
        await admin_handlers.process_admin_export_event(cb_export_ev)
        
        # Verify the file was generated and sent
        sent_doc_msg = msg.sent_messages[-1]
        assert "Список регистраций" in sent_doc_msg[0]
        # The document is a BufferedInputFile
        from aiogram.types import BufferedInputFile
        assert isinstance(sent_doc_msg[1], BufferedInputFile)
        assert sent_doc_msg[1].filename.startswith("registrations_2_")
        assert sent_doc_msg[2] is not None  # reply_markup check
        
        # Let's inspect the excel data bytes to make sure they are a valid workbook
        import io
        import openpyxl
        file_bytes = sent_doc_msg[1].data
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active
        assert ws.title == "Регистрации"
        row1 = [cell.value for cell in ws[1]]
        assert row1 == ["ФИО", "Электронная почта", "Телефон", "Откуда вы узнали о событии?", "Вы планируете быть очно или удалённо?", "Дата", "TG ник"]
        
        # Row 2 should be the active one ("очно") because "думаю" is sorted to the end
        row2 = [cell.value for cell in ws[2]]
        assert row2[0] == "Алексеев Алексей"
        assert row2[4] == "очно"
        assert row2[6] == "@dummy456"

        # Row 3 should be the thinking one ("думаю")
        row3 = [cell.value for cell in ws[3]]
        assert row3[0] == "Кузнецов Пётр"
        assert row3[4] == "думаю"
        assert row3[6] == "@john_doe"

        print("Admin registrations Excel export test PASSED!")


        # ----------------------------------------------------
        # 13. User Data Deletion (/delete Command)
        # ----------------------------------------------------
        print("Testing user registration deletion via /delete...")
        # Verify user 123 is registered beforehand
        u123 = await session.get(User, 123)
        assert u123.is_registered is True
        assert u123.full_name == "Кузнецов Пётр"

        # Check registrations exist for user 123
        reg123 = await session.get(Registration, (123, 2))
        assert reg123 is not None

        # Execute /delete
        delete_state = DummyState()
        await handlers.cmd_delete(DummyMessage(123, "john_doe"), delete_state)

        # Clear identity map cache so we fetch fresh state from DB
        session.expire_all()

        # Refresh database session and verify user fields are reset
        await session.refresh(u123)
        assert u123.is_registered is False
        assert u123.full_name is None
        assert u123.email is None
        assert u123.phone == "-"
        # Also ensure FSM registration flow is restarted for the user
        assert delete_state.state == handlers.RegistrationStates.accept_agreement

        # Ensure registrations are deleted
        reg123_check = await session.get(Registration, (123, 2))
        assert reg123_check is None

        print("User data deletion via /delete test PASSED!")

        # ----------------------------------------------------
        # 14. Admin Default Event Address Button
        # ----------------------------------------------------
        print("Testing admin default event address option...")
        address_state = DummyState()
        await address_state.set_state(admin_handlers.EventForm.address)
        
        from admin_keyboards import get_address_keyboard
        kb = get_address_keyboard(show_back=True, back_callback="back_address")
        button_texts = [btn.text for row in kb.inline_keyboard for btn in row]
        assert "Вставить адрес Хаба" in button_texts
        
        msg_address = DummyMessage(999, "ASaavedraA")
        cb_address = DummyCallbackQuery("admin_event_default_address", 999, "ASaavedraA", msg_address)
        await admin_handlers.process_add_event_default_address(cb_address, address_state)
        
        data = await address_state.get_data()
        assert data.get("address") == "Москва, Пантелеевская 53"
        assert address_state.state == admin_handlers.EventForm.description
        assert "Вопрос 6: Основной текст" in msg_address.sent_messages[-1][0]
        print("Admin default event address option test PASSED!")

        # ----------------------------------------------------
        # 15. Admin Post-Materials Deletion Flow
        # ----------------------------------------------------
        print("Testing admin post-materials deletion flow...")
        # Populate event 2 with a photo url to test deletion
        async with async_session() as test_session:
            ev2 = await test_session.get(Event, 2)
            ev2.photos_url = "https://photos.url/123"
            test_session.add(ev2)
            await test_session.commit()

        # Verify event 2 has photos_url first
        async with async_session() as test_session:
            ev2 = await test_session.get(Event, 2)
            assert ev2.photos_url == "https://photos.url/123"

        msg_pm_del = DummyMessage(999, "ASaavedraA")
        # Trigger confirm step (admin_pm_del_2)
        cb_pm_del_start = DummyCallbackQuery("admin_pm_del_2", 999, "ASaavedraA", msg_pm_del)
        await admin_handlers.process_admin_pm_del_confirm_start(cb_pm_del_start)
        assert "Вы уверены? Это действие нельзя отменить!" in msg_pm_del.sent_messages[-1][0]
        
        # Trigger final deletion step (admin_pm_del_confirm_2)
        cb_pm_del_final = DummyCallbackQuery("admin_pm_del_confirm_2", 999, "ASaavedraA", msg_pm_del)
        await admin_handlers.process_admin_pm_del_final(cb_pm_del_final)
        assert "Пост-материалы удалены!" in msg_pm_del.sent_messages[-1][0]
        
        # Verify database fields are updated to None
        async with async_session() as test_session:
            ev2_updated = await test_session.get(Event, 2)
            assert ev2_updated.photos_url is None
        print("Admin post-materials deletion flow test PASSED!")

        # ----------------------------------------------------
        # 16. Stream URL Notifications for Remote Participants
        # ----------------------------------------------------
        print("Testing stream URL update notifications...")
        
        async with async_session() as test_session:
            existing_reg = await test_session.get(Registration, (123, 2))
            if existing_reg:
                await test_session.delete(existing_reg)
                await test_session.commit()
                
            remote_reg = Registration(
                user_id=123,
                event_id=2,
                status="удаленно",
                registration_date="25.06.2026"
            )
            test_session.add(remote_reg)
            
            ev2 = await test_session.get(Event, 2)
            ev2.stream_url = None
            ev2.images = ["AgACAgIAAxkBAAIB"]
            test_session.add(ev2)
            await test_session.commit()
            
        edit_state = DummyState()
        await edit_state.set_state(admin_handlers.EditEventForm.value)
        await edit_state.update_data(event_id=2, section="streamurl")
        
        mock_bot_stream = DummyBot()
        edit_msg = DummyMessage(999, "ASaavedraA", "https://youtube.com/live_stream")
        edit_msg.bot = mock_bot_stream
        
        await admin_handlers.process_edit_event_value(edit_msg, edit_state)
        
        await asyncio.sleep(0.1)
        
        async with async_session() as test_session:
            ev2_updated = await test_session.get(Event, 2)
            assert ev2_updated.stream_url == "https://youtube.com/live_stream"
            
        assert len(mock_bot_stream.sent_messages) > 0
        
        broadcast_msg = None
        for chat_id, content, kb in mock_bot_stream.sent_messages:
            if chat_id == 123:
                broadcast_msg = content
                break
                
        assert broadcast_msg is not None
        assert "Ссылка на трансляцию мероприятия уже доступна!" in broadcast_msg
        assert "Вы зарегистрировались на трансляцию мероприятия" in broadcast_msg
        assert "Трансляция" in broadcast_msg
        assert "youtube.com/live_stream" in broadcast_msg
        print("Stream URL update notifications test PASSED!")








def main():
    print("Starting comprehensive Bot Test Suite...")
    try:
        asyncio.run(test_suite())
        print("\nALL BOT HANDLERS & LOGIC TESTED SUCCESSFULLY WITH ZERO ERRORS!")
        # If success, clear test_errors.log if it exists
        if os.path.exists("test_errors.log"):
            os.remove("test_errors.log")
    except Exception as e:
        error_msg = f"TEST SUITE FAILED WITH EXCEPTION:\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        with open("test_errors.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
