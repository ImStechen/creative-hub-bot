from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

import config
from database.db import async_session
from database.models import User, Event, Raffle, Registration, Admin, get_default_tags, get_default_notifications
from keyboards import (
    get_main_menu_keyboard,
    get_events_list_keyboard,
    get_event_detail_keyboard,
    get_after_registration_keyboard,
    get_preferences_menu_keyboard,
    get_checkbox_keyboard,
    get_after_save_tags_keyboard,
    get_archive_tags_keyboard,
    get_archive_events_keyboard,
    get_archive_detail_keyboard,
    get_raffle_detail_keyboard,
    get_registration_keyboard,
    get_agreement_keyboard
)

router = Router()

class RegistrationStates(StatesGroup):
    accept_agreement = State()
    full_name = State()
    email = State()
    phone = State()

class PreferencesStates(StatesGroup):
    editing_tags = State()
    editing_notifications = State()


def is_event_hidden(event: Event) -> bool:
    if not event.hide_date:
        return False
    time_str = event.hide_time or "00:00"
    try:
        hide_datetime = datetime.strptime(f"{event.hide_date} {time_str}", "%d.%m.%Y %H:%M")
        return datetime.now() > hide_datetime
    except ValueError:
        return False


async def get_active_raffles_count(session: AsyncSession, user_tags: dict) -> int:
    """
    Возвращает количество активных розыгрышей, подходящих для конкретного пользователя.
    """
    # Сначала проверяем, не скрыт ли розыгрыш по дате/времени
    query = select(Raffle).where(Raffle.is_active == 1)
    result = await session.execute(query)
    active_raffles = result.scalars().all()
    
    if not active_raffles:
        return 0
        
    now = datetime.now()
    valid_raffles = []
    
    for r in active_raffles:
        if r.hide_date:
            time_str = r.hide_time or "00:00"
            try:
                hide_datetime = datetime.strptime(f"{r.hide_date} {time_str}", "%d.%m.%Y %H:%M")
                if now > hide_datetime:
                    continue
            except ValueError:
                pass
        valid_raffles.append(r)
        
    if not valid_raffles:
        return 0
        
    active_user_tags = {tag for tag, val in user_tags.items() if val}
    
    count = 0
    for raffle in valid_raffles:
        if raffle.event_id is None:
            count += 1
            continue
            
        event = await session.get(Event, raffle.event_id)
        if not event:
            continue
            
        event_tags = event.tags or []
        if any(tag in active_user_tags for tag in event_tags):
            count += 1
            
    return count


async def show_main_page(message: Message, telegram_id: int, username: str | None, session: AsyncSession):
    db_user = await session.get(User, telegram_id)
    if not db_user:
        db_user = User(telegram_id=telegram_id, username=username)
        session.add(db_user)
        await session.commit()

    user_tags = dict(db_user.tags_preferences or {})
    updated = False
    for tag in config.DEFAULT_TAGS:
        if tag not in user_tags:
            user_tags[tag] = True
            updated = True
    if updated:
        db_user.tags_preferences = user_tags
        session.add(db_user)
        await session.commit()

    active_user_tags = {tag for tag, val in user_tags.items() if val}

    events_query = select(Event)
    events_result = await session.execute(events_query)
    all_events = events_result.scalars().all()

    recommended_events = []
    for event in all_events:
        if is_event_hidden(event):
            continue
        event_tags = event.tags or []
        if any(tag in active_user_tags for tag in event_tags):
            recommended_events.append(event)

    text_lines = ["Мероприятия по вашим предпочтениям:\n"]
    if not recommended_events:
        text_lines.append("<i>Пока нет подходящих мероприятий по вашим тегам. Вы можете изменить их в настройках предпочтений.</i>")
    else:
        for event in recommended_events:
            title_html = f"<b>{event.title}</b>"
            if event.title_url:
                title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'
            tags_str = " ".join([f"#{tag}" for tag in event.tags])
            text_lines.append(f"<b>{config.format_display_date(event.date)}</b> {title_html}\n{tags_str}\n")

    text = "\n".join(text_lines)
    raffle_count = await get_active_raffles_count(session, user_tags)
    
    # Проверка прав администратора
    is_admin = False
    if username:
        if config.is_super_admin(username):
            is_admin = True
        else:
            clean_username = username.lstrip('@').lower()
            admin_query = select(Admin).where(func.lower(Admin.username) == clean_username)
            admin_result = await session.execute(admin_query)
            if admin_result.scalar_one_or_none() is not None:
                is_admin = True

    kb = get_main_menu_keyboard(is_admin, raffle_count)
    
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


@router.message(F.text == "/restart")
async def cmd_restart(message: Message, state: FSMContext):
    import os
    import subprocess
    current_pid = os.getpid()
    try:
        # WMIC command to list python command lines
        output = subprocess.check_output(
            'wmic process where "name=\'python.exe\'" get commandline,processid',
            shell=True
        ).decode('utf-8', errors='ignore')
        
        for line in output.splitlines():
            line = line.strip()
            if not line or "ProcessId" in line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    pid = int(parts[-1])
                    cmdline = " ".join(parts[:-1]).lower()
                    # Kill other duplicate instances of main.py or main test runs
                    if pid != current_pid and ("main.py" in cmdline or "asyncio.run(main.main())" in cmdline):
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                except Exception:
                    pass
    except Exception:
        pass

    # Redirect user to start flow
    await cmd_start(message, state)


@router.message(Command("delete"))
async def cmd_delete(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            user.full_name = None
            user.email = None
            user.phone = "-"
            user.is_registered = False
            user.tags_preferences = get_default_tags()
            user.notification_preferences = get_default_notifications()
            
            # Delete registrations
            await session.execute(delete(Registration).where(Registration.user_id == telegram_id))
            session.add(user)
            await session.commit()
            
        await message.answer("Ваша регистрационная информация и предпочтения успешно удалены.")
        # Start onboarding from scratch
        await cmd_start(message, state)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with async_session() as session:
        db_user = await session.get(User, telegram_id)
        if not db_user:
            db_user = User(telegram_id=telegram_id, username=username)
            session.add(db_user)
            await session.commit()

        # Точный приветственный текст с вшитой ссылкой hse.ru/hub согласно доке
        welcome_text = (
            "Привет!\n"
            'Я бот <a href="https://creative.hse.ru/hub">Креативного хаба НИУ ВШЭ</a>.\n\n'
            "Моя работа — рассказывать вам о мероприятиях в Хабе и хранить ценные материалы по итогам событий. "
            "Но я не спам-бот: здесь вы сами решаете, какие уведомления получать и за какими тематиками мероприятий следить.\n\n"
            "Рекомендую сразу зайти в раздел «Настроить предпочтения» и отрегулировать систему под себя, чтобы я не беспокоил вас без повода.\n\n"
            "Увидимся по адресу: <b>Пантелеевская, 53</b>"
        )
        await message.answer(welcome_text, disable_web_page_preview=True)

        if not db_user.is_registered:
            await state.set_state(RegistrationStates.accept_agreement)
            reg_text = (
                "<b>Но сперва познакомимся!</b>\n\n"
                "Чтобы попасть на наши мероприятия (очно и удалённо), нужно зарегистрироваться. "
                "Можно каждый раз заполнять анкету на сайте Вышки, а можно — один раз авторизоваться в боте.\n\n"
                "Авторизация откроет доступ к более тонкой настройке уведомлений и позволит записываться на события одной кнопкой.\n\n"
                "Продолжая авторизацию, вы принимаете <a href=\"https://www.hse.ru/data_protection_regulation\">Положение об обработке персональных данных НИУ ВШЭ</a>."
            )
            await message.answer(reg_text, reply_markup=get_agreement_keyboard(), parse_mode="HTML")
        else:
            await show_main_page(message, telegram_id, username, session)


@router.callback_query(F.data == "reg_accept", RegistrationStates.accept_agreement)
async def process_reg_accept(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationStates.full_name)
    reg_text = (
        "<b>Вопрос 1.</b> Как вас зовут? Напишите сперва фамилию, затем имя, например:\n"
        "<blockquote>Кузнецов Пётр</blockquote>"
    )
    await callback.message.answer(reg_text, reply_markup=get_registration_keyboard(1), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "reg_skip")
async def process_reg_skip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    telegram_id = callback.from_user.id
    username = callback.from_user.username
    async with async_session() as session:
        await show_main_page(callback.message, telegram_id, username, session)
    await callback.answer("Регистрация пропущена")


@router.callback_query(F.data == "reg_skip_phone", RegistrationStates.phone)
async def process_reg_skip_phone(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    email = data.get("email")
    phone = "-"
    
    telegram_id = callback.from_user.id
    username = callback.from_user.username
    
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            user.full_name = full_name
            user.email = email
            user.phone = phone
            user.is_registered = True
            session.add(user)
            await session.commit()
            
        await callback.message.answer("Регистрация успешно завершена!")
        
        pending_event_id = data.get("pending_event_id")
        pending_status = data.get("pending_status")
        
        if pending_event_id and pending_status:
            await state.clear()
            await finalize_pending_registration(callback.message, telegram_id, pending_event_id, pending_status, session)
        else:
            await state.clear()
            await show_main_page(callback.message, telegram_id, username, session)
            
    await callback.answer()


@router.message(RegistrationStates.full_name)
async def process_reg_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if not full_name:
        await message.answer("Имя и фамилия не могут быть пустыми. Пожалуйста, напишите сперва фамилию, затем имя:")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationStates.email)
    await message.answer(
        "<b>Вопрос 2.</b> Укажите контактную почту\n<blockquote>Пример: ivanov@example.com</blockquote>",
        reply_markup=get_registration_keyboard(2),
        parse_mode="HTML"
    )


import re
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@router.message(RegistrationStates.email)
async def process_reg_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if not EMAIL_REGEX.match(email):
        await message.answer(
            "Неверный формат e-mail. Пожалуйста, укажите корректную контактную почту:\n"
            "<blockquote>Пример: ivanov@example.com</blockquote>",
            reply_markup=get_registration_keyboard(2),
            parse_mode="HTML"
        )
        return
    await state.update_data(email=email)
    await state.set_state(RegistrationStates.phone)
    await message.answer(
        "<b>Вопрос 3.</b> Укажите номер телефона\n<blockquote>Пример: +79991234567</blockquote>",
        reply_markup=get_registration_keyboard(3),
        parse_mode="HTML"
    )


@router.message(RegistrationStates.phone)
async def process_reg_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone:
        await message.answer("Номер телефона не может быть пустым. Пожалуйста, укажите номер телефона:")
        return
    
    data = await state.get_data()
    full_name = data.get("full_name")
    email = data.get("email")
    telegram_id = message.from_user.id
    username = message.from_user.username
    
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            user.full_name = full_name
            user.email = email
            user.phone = phone
            user.is_registered = True
            session.add(user)
            await session.commit()
            
        await message.answer("Регистрация успешно завершена!")
        
        pending_event_id = data.get("pending_event_id")
        pending_status = data.get("pending_status")
        
        if pending_event_id and pending_status:
            await state.clear()
            await finalize_pending_registration(message, telegram_id, pending_event_id, pending_status, session)
        else:
            await state.clear()
            await show_main_page(message, telegram_id, username, session)


async def finalize_pending_registration(message: Message, telegram_id: int, event_id: int, status: str, session: AsyncSession):
    user = await session.get(User, telegram_id)
    event = await session.get(Event, event_id)
    if not event:
        await message.answer("Мероприятие не найдено.")
        return
        
    reg_query = select(Registration).where(
        Registration.user_id == telegram_id,
        Registration.event_id == event_id
    )
    reg_result = await session.execute(reg_query)
    reg = reg_result.scalar_one_or_none()
    
    current_date_str = datetime.now().strftime("%d.%m.%Y")
    
    if reg:
        reg.status = status
        reg.registration_date = current_date_str
        reg.reminded_24h = False
        reg.reminded_2h = False
    else:
        reg = Registration(
            user_id=telegram_id, 
            event_id=event_id, 
            status=status, 
            registration_date=current_date_str,
            reminded_24h=False,
            reminded_2h=False
        )
        session.add(reg)
        
    await session.commit()
    
    user_prefs = user.notification_preferences or {}
    reminders = []
    
    if status == "очно":
        if user_prefs.get("За день до мероприятия, на которое я иду очно", False):
            reminders.append("За день до мероприятия")
        if user_prefs.get("За два часа до мероприятия, на которое я иду очно", False):
            reminders.append("За два часа до мероприятия")
    elif status == "удаленно":
        if user_prefs.get("За день до мероприятия, на котором я буду удалённо", False):
            reminders.append("За день до мероприятия")
        if user_prefs.get("За два часа до мероприятия, на котором я буду удалённо", False):
            reminders.append("За два часа до мероприятия")
            
    reminders_text = "\n".join([f"✅ {r}" for r in reminders]) if reminders else "Уведомления отключены"
    
    title_html = f"<b>{event.title}</b>"
    if event.title_url:
        title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'
        
    if status == "очно":
        confirmation_text = (
            f"Успешная регистрация!\n"
            f"Вы пойдете очно на мероприятие {title_html}\n\n"
            f"<b>Дата:</b> {config.format_display_date(event.date)}\n"
            f"<b>Время:</b> {event.time}\n"
            f"<b>Место:</b> {event.address}\n\n"
            f"Согласно вашим предпочтениям, вы получите напоминание:\n{reminders_text}"
        )
    elif status == "удаленно":
        confirmation_text = (
            f"Успешная регистрация!\n"
            f"Вы будете удалённо на мероприятии {title_html}\n\n"
            f"<b>Дата:</b> {config.format_display_date(event.date)}\n"
            f"<b>Время:</b> {event.time}\n\n"
            f"Согласно вашим предпочтениям, вы получите напоминание:\n{reminders_text}"
        )
        
    await message.answer(
        confirmation_text,
        reply_markup=get_after_registration_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        await show_main_page(callback.message, callback.from_user.id, callback.from_user.username, session)
    await callback.answer()


# ==========================================
# 1. ПРОСМОТР МЕРОПРИЯТИЙ
# ==========================================

@router.callback_query(F.data == "btn_events_info")
async def process_events_info(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        user_tags = dict(user.tags_preferences or {})
        active_user_tags = {tag for tag, val in user_tags.items() if val}
        
        events_query = select(Event)
        events_result = await session.execute(events_query)
        all_events = events_result.scalars().all()
        
        active_events = []
        for e in all_events:
            if is_event_hidden(e):
                continue
            event_tags = e.tags or []
            if any(tag in active_user_tags for tag in event_tags):
                active_events.append(e)
        
        if not active_events:
            await callback.message.answer(
                "На данный момент нет запланированных мероприятий по вашим интересам.",
                reply_markup=get_events_list_keyboard([])
            )
        else:
            await callback.message.answer(
                "Выберите интересующее мероприятие.",
                reply_markup=get_events_list_keyboard(active_events)
            )
    await callback.answer()


@router.callback_query(F.data.startswith("show_event_"))
async def process_show_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            await callback.answer("Мероприятие не найдено.")
            return

        title_html = f"<b>{event.title}</b>"
        if event.title_url:
            title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'
            
        tags_str = " ".join([f"#{tag}" for tag in event.tags])
        desc = event.description or ""
        
        links_list = []
        if event.reg_url:
            links_list.append(f'→ <a href="{event.reg_url}">Регистрация на сайте</a>')
        if event.stream_url:
            links_list.append(f'→ <a href="{event.stream_url}">Трансляция</a>')
        links_str = "\n\n" + "\n".join(links_list) if links_list else ""
        
        text = (
            f"{title_html}\n\n"
            f"{desc}\n\n"
            f"📆 <b>Дата:</b> {config.format_display_date(event.date)}\n"
            f"⏳ <b>Время:</b> {event.time}\n"
            f"📍 <b>Место:</b> {event.address}"
            f"{links_str}\n\n"
            f"{tags_str}"
        )
        
        kb = get_event_detail_keyboard(event.id)
        
        if event.images and len(event.images) > 0:
            await callback.message.answer_photo(
                photo=event.images[0],
                caption=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                text,
                reply_markup=kb,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    await callback.answer()


@router.callback_query(F.data.startswith("reg_status_"))
async def process_registration_status(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    event_id = int(parts[2])
    status = parts[3]
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await session.get(User, telegram_id)
        
        # Intercept event booking for non-registered users (only if status is "очно" or "удаленно")
        if (not user or not user.is_registered) and status in ["очно", "удаленно"]:
            await state.update_data(pending_event_id=event_id, pending_status=status)
            await state.set_state(RegistrationStates.accept_agreement)
            reg_text = (
                "<b>Но сперва познакомимся!</b>\n\n"
                "Чтобы попасть на наши мероприятия (очно и удалённо), нужно зарегистрироваться. "
                "Можно каждый раз заполнять анкету на сайте Вышки, а можно — один раз авторизоваться в боте.\n\n"
                "Авторизация откроет доступ к более тонкой настройке уведомлений и позволит записываться на события одной кнопкой.\n\n"
                "Продолжая авторизацию, вы принимаете <a href=\"https://www.hse.ru/data_protection_regulation\">Положение об обработке персональных данных НИУ ВШЭ</a>."
            )
            await callback.message.answer(reg_text, reply_markup=get_agreement_keyboard(), parse_mode="HTML")
            await callback.answer()
            return

        event = await session.get(Event, event_id)
        if not event:
            await callback.answer("Мероприятие не найдено.")
            return

        reg_query = select(Registration).where(
            Registration.user_id == telegram_id,
            Registration.event_id == event_id
        )
        reg_result = await session.execute(reg_query)
        reg = reg_result.scalar_one_or_none()

        current_date_str = datetime.now().strftime("%d.%m.%Y")

        if status == "не пойду":
            if reg:
                await session.delete(reg)
                await session.commit()
        else:
            if reg:
                reg.status = status
                reg.registration_date = current_date_str
                reg.reminded_24h = False
                reg.reminded_2h = False
            else:
                reg = Registration(
                    user_id=telegram_id, 
                    event_id=event_id, 
                    status=status, 
                    registration_date=current_date_str,
                    reminded_24h=False,
                    reminded_2h=False
                )
                session.add(reg)
            await session.commit()
        
        # Получаем выбранные типы напоминаний пользователя
        user_prefs = user.notification_preferences or {}
        reminders = []
        
        # Перечисляем подходящие уведомления пользователя
        if status == "очно":
            if user_prefs.get("За день до мероприятия, на которое я иду очно", False):
                reminders.append("За день до мероприятия")
            if user_prefs.get("За два часа до мероприятия, на которое я иду очно", False):
                reminders.append("За два часа до мероприятия")
        elif status == "удаленно":
            if user_prefs.get("За день до мероприятия, на котором я буду удалённо", False):
                reminders.append("За день до мероприятия")
            if user_prefs.get("За два часа до мероприятия, на котором я буду удалённо", False):
                reminders.append("За два часа до мероприятия")
        elif status == "думаю":
            if user_prefs.get("За день до мероприятия, насчет которого я сомневаюсь", False):
                reminders.append("За день до мероприятия")
            if user_prefs.get("За два часа до мероприятия, насчет которого я сомневаюсь", False):
                reminders.append("За два часа до мероприятия")

        reminders_text = "\n".join([f"✅ {r}" for r in reminders]) if reminders else "Уведомления отключены"

        title_html = f"<b>{event.title}</b>"
        if event.title_url:
            title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'

        if status == "очно":
            confirmation_text = (
                f"Успешная регистрация!\n"
                f"Вы пойдете очно на мероприятие {title_html}\n\n"
                f"<b>Дата:</b> {config.format_display_date(event.date)}\n"
                f"<b>Время:</b> {event.time}\n"
                f"<b>Место:</b> {event.address}\n\n"
                f"Согласно вашим предпочтениям, вы получите напоминание:\n{reminders_text}"
            )
        elif status == "удаленно":
            confirmation_text = (
                f"Успешная регистрация!\n"
                f"Вы будете удалённо на мероприятии {title_html}\n\n"
                f"<b>Дата:</b> {config.format_display_date(event.date)}\n"
                f"<b>Время:</b> {event.time}\n\n"
                f"Согласно вашим предпочтениям, вы получите напоминание:\n{reminders_text}"
            )
        elif status == "думаю":
            confirmation_text = (
                f"Понял, вы пока не уверены, сможете ли быть на мероприятии {title_html}.\n\n"
                f"Согласно вашим предпочтениям, вы получите напоминание:\n{reminders_text}"
            )
        else: # не пойду
            confirmation_text = (
                f"Понял, вы не пойдете на мероприятие {title_html}.\n"
                "Если оно не соответствует вашим предпочтениям, вы всегда можете изменить их в настройках."
            )

        await callback.message.answer(
            confirmation_text,
            reply_markup=get_after_registration_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
            
    await callback.answer()


# ==========================================
# 2. НАСТРОЙКИ ПРЕДПОЧТЕНИЙ
# ==========================================

@router.callback_query(F.data == "btn_preferences")
async def process_preferences_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Что вы хотите настроить?",
        reply_markup=get_preferences_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "pref_tags")
async def process_pref_tags(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        tags_data = dict(user.tags_preferences or {})
        
        updated = False
        for tag in config.DEFAULT_TAGS:
            if tag not in tags_data:
                tags_data[tag] = True
                updated = True
                
        if updated:
            user.tags_preferences = tags_data
            session.add(user)
            await session.commit()
            
        await state.set_state(PreferencesStates.editing_tags)
        await state.update_data(temp_preferences=tags_data)
        
        await callback.message.answer(
            "Выберите любимые темы мероприятий, о которых хотите получать уведомления:",
            reply_markup=get_checkbox_keyboard(tags_data, "tags")
        )
    await callback.answer()


@router.callback_query(F.data == "pref_notifications")
async def process_pref_notifications(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        notifs_data = dict(user.notification_preferences or {})
        
        await state.set_state(PreferencesStates.editing_notifications)
        await state.update_data(temp_preferences=notifs_data)
        
        await callback.message.answer(
            "Выберите, в каких случаях получать уведомления:",
            reply_markup=get_checkbox_keyboard(notifs_data, "notifs")
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cb_"))
async def process_checkbox_toggle(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    pref_type = parts[1]
    key_name = "_".join(parts[2:])

    state_data = await state.get_data()
    temp_prefs = state_data.get("temp_preferences", {})

    try:
        idx = int(key_name)
        keys = list(temp_prefs.keys())
        if idx < len(keys):
            real_key = keys[idx]
            temp_prefs[real_key] = not temp_prefs[real_key]
            await state.update_data(temp_preferences=temp_prefs)
            await callback.message.edit_reply_markup(
                reply_markup=get_checkbox_keyboard(temp_prefs, pref_type)
            )
    except ValueError:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("save_"))
async def process_save_preferences(callback: CallbackQuery, state: FSMContext):
    pref_type = callback.data.split("_")[1]
    state_data = await state.get_data()
    temp_prefs = state_data.get("temp_preferences", {})
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            if pref_type == "tags":
                user.tags_preferences = temp_prefs
                session.add(user)
                await session.commit()
                
                # Выводим сохраненные теги
                active_tags = [t for t, val in temp_prefs.items() if val]
                tags_list_str = "\n".join([f"✅ {tag}" for tag in active_tags])
                if not tags_list_str:
                    tags_list_str = "Вы не выбрали ни одной темы"
                    
                await callback.message.answer(
                    f"Принято! Теперь я буду уведомлять вас о мероприятиях следующих тематик:\n\n{tags_list_str}",
                    reply_markup=get_after_save_tags_keyboard()
                )
            else:
                user.notification_preferences = temp_prefs
                session.add(user)
                await session.commit()
                
                await callback.message.answer(
                    "Принято! Теперь я буду уведомлять вас в указанных случаях.",
                    reply_markup=get_after_save_tags_keyboard()
                )

    await callback.answer("Сохранено!")
    await state.clear()


# ==========================================
# 3. АРХИВ ПОСТ-МАТЕРИАЛОВ
# ==========================================

@router.callback_query(F.data == "btn_archive")
async def process_archive_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Здесь хранятся статьи, фотографии, презентации спикеров и записи трансляций всех мероприятий Креативного хаба.\n\n"
        "Выберите интересующую тематику мероприятия, чтобы начать поиск.",
        reply_markup=get_archive_tags_keyboard(config.DEFAULT_TAGS)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("arch_tag_"))
async def process_archive_tag_selection(callback: CallbackQuery):
    idx_str = callback.data.split("_")[2]
    try:
        idx = int(idx_str)
        tag = config.DEFAULT_TAGS[idx]
    except (ValueError, IndexError):
        tag = idx_str
    
    async with async_session() as session:
        query = select(Event)
        result = await session.execute(query)
        events = result.scalars().all()
        
        archived_events = []
        for e in events:
            if tag in (e.tags or []):
                if any([e.photos_url, e.stream_record_url, e.article_url, e.presentations_url, e.other_materials_url]):
                    archived_events.append(e)
                    
        if not archived_events:
            await callback.message.answer(
                f"По теме #{tag} пока нет прошедших мероприятий с материалами.",
                reply_markup=get_archive_events_keyboard([], idx)
            )
        else:
            await callback.message.answer(
                "Вот список всех мероприятий по этой теме. Выберите нужное.",
                reply_markup=get_archive_events_keyboard(archived_events, idx)
            )
    await callback.answer()


@router.callback_query(F.data.startswith("arch_event_"))
async def process_archive_event_detail(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            await callback.answer("Мероприятие не найдено.")
            return
            
        title_html = f"<b>{event.title}</b>"
        if event.title_url:
            title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'
            
        tags_str = " ".join([f"#{t}" for t in event.tags])
        
        links = []
        if event.photos_url:
            links.append(f'Фотографии: <a href="{event.photos_url}">открыть</a>')
        if event.article_url:
            links.append(f'Статья-конспект: <a href="{event.article_url}">открыть</a>')
        if event.presentations_url:
            links.append(f'Презентации спикеров: <a href="{event.presentations_url}">открыть</a>')
        if event.stream_record_url:
            links.append(f'Запись трансляции: <a href="{event.stream_record_url}">открыть</a>')
        if event.other_materials_url:
            links.append(f'Другие материалы: <a href="{event.other_materials_url}">открыть</a>')
            
        materials_text = "\n".join(links) if links else "Материалы отсутствуют."
        
        text = (
            f"{title_html}\n\n"
            f"📆 <b>Дата:</b> {config.format_display_date(event.date)}\n"
            f"⏳ <b>Время:</b> {event.time}\n"
            f"📍 <b>Место:</b> {event.address}\n\n"
            f"{materials_text}\n\n"
            f"{tags_str}"
        )
        
        back_tag_idx = 0
        if event.tags:
            first_tag = event.tags[0]
            if first_tag in config.DEFAULT_TAGS:
                back_tag_idx = config.DEFAULT_TAGS.index(first_tag)
        
        await callback.message.answer(
            text,
            reply_markup=get_archive_detail_keyboard(back_tag_idx),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    await callback.answer()


# ==========================================
# 4. РОЗЫГРЫШ
# ==========================================

@router.callback_query(F.data == "btn_raffle")
async def process_raffle_info(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        user_tags = dict(user.tags_preferences or {})
        active_user_tags = {tag for tag, val in user_tags.items() if val}
        
        query = select(Raffle).where(Raffle.is_active == 1)
        result = await session.execute(query)
        active_raffles = result.scalars().all()
        
        now = datetime.now()
        valid_raffles = []
        
        for r in active_raffles:
            if r.hide_date:
                time_str = r.hide_time or "00:00"
                try:
                    hide_datetime = datetime.strptime(f"{r.hide_date} {time_str}", "%d.%m.%Y %H:%M")
                    if now > hide_datetime:
                        continue
                except ValueError:
                    pass
            valid_raffles.append(r)
            
        suitable_raffle = None
        for raffle in valid_raffles:
            if raffle.event_id is None:
                suitable_raffle = raffle
                break
                
            event = await session.get(Event, raffle.event_id)
            if not event:
                continue
                
            event_tags = event.tags or []
            if any(tag in active_user_tags for tag in event_tags):
                suitable_raffle = raffle
                break
                
        if not suitable_raffle:
            await callback.message.answer(
                "В данный момент нет активных розыгрышей по вашим интересам.",
                reply_markup=get_raffle_detail_keyboard()
            )
        else:
            title_html = suitable_raffle.title
            if suitable_raffle.url:
                title_html = f'<a href="{suitable_raffle.url}">{suitable_raffle.title}</a>'
                
            desc = suitable_raffle.description or "Подробности розыгрыша отсутствуют."
            text = f"<b>{title_html}</b>\n\n{desc}"
            
            await callback.message.answer(
                text,
                reply_markup=get_raffle_detail_keyboard(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
    await callback.answer()
