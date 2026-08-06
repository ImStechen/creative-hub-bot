import asyncio
import logging
from datetime import datetime, timezone, timedelta
from aiogram import Bot
from sqlalchemy import select

import config
from database.db import async_session
from database.models import User, Event, Registration, SeriesEvent, SeriesEventRegistration, EventSeries
from keyboards import get_reminder_keyboard, get_to_main_keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reminders_scheduler")

async def check_and_send_reminders(bot: Bot):
    """
    Фоновая периодическая задача, проверяющая предстоящие мероприятия и рассылающая уведомления
    пользователям в соответствии с их предпочтениями (настройками уведомлений).
    """
    async with async_session() as session:
        # Извлекаем все мероприятия
        events_query = select(Event)
        events_result = await session.execute(events_query)
        events = events_result.scalars().all()
        
        # Получаем текущее время в Московском часовом поясе (UTC+3) для корректного сравнения с БД
        now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).replace(tzinfo=None)
        
        for event in events:
            # Парсим дату и время начала события
            try:
                time_str = event.time.strip()
                normalized_time = time_str.replace("—", "-").replace(" - ", "-").replace(" -", "-").replace("- ", "-")
                start_time_part = normalized_time.split("-")[0].strip()
                
                # Извлекаем первую дату если это диапазон (например, 16.07.2026-17.07.2026)
                event_date_str = event.date.split("-")[0].strip()
                event_datetime = datetime.strptime(f"{event_date_str} {start_time_part}", "%d.%m.%Y %H:%M")
            except Exception:
                continue
                
            time_diff = event_datetime - now
            time_diff_hours = time_diff.total_seconds() / 3600.0
            
            # Определяем, находимся ли мы в окне "за день" (23-25 часов) или "за 2 часа" (1.9-2.1 часа)
            is_one_day_window = 23.5 <= time_diff_hours <= 24.5
            is_two_hours_window = 1.8 <= time_diff_hours <= 2.2
            
            if not (is_one_day_window or is_two_hours_window):
                continue
                
            # Ищем все регистрации на это мероприятие
            regs_query = select(Registration).where(Registration.event_id == event.id)
            regs_result = await session.execute(regs_query)
            registrations = regs_result.scalars().all()
            
            for reg in registrations:
                user = await session.get(User, reg.user_id)
                if not user:
                    continue
                    
                user_prefs = user.notification_preferences or {}
                
                # Проверяем соответствие настроек уведомлений
                should_notify = False
                trigger_name = ""
                
                if reg.status == "очно":
                    if is_one_day_window and not reg.reminded_24h:
                        trigger_name = "За день до мероприятия, на которое я иду очно"
                    elif is_two_hours_window and not reg.reminded_2h:
                        trigger_name = "За два часа до мероприятия, на которое я иду очно"
                elif reg.status == "удаленно":
                    if is_one_day_window and not reg.reminded_24h:
                        trigger_name = "За день до мероприятия, на котором я буду удалённо"
                    elif is_two_hours_window and not reg.reminded_2h:
                        trigger_name = "За два часа до мероприятия, на котором я буду удалённо"
                elif reg.status == "думаю":
                    if is_one_day_window and not reg.reminded_24h:
                        trigger_name = "За день до мероприятия, насчет которого я сомневаюсь"
                    elif is_two_hours_window and not reg.reminded_2h:
                        trigger_name = "За два часа до мероприятия, насчет которого я сомневаюсь"
                
                if trigger_name and user_prefs.get(trigger_name, False):
                    should_notify = True
                    
                if should_notify:
                    # Отправляем напоминание
                    try:
                        title_html = f"<b>{event.title}</b>"
                        if event.title_url:
                            title_html = f'<b><a href="{event.title_url}">{event.title}</a></b>'
                            
                        timing_desc = "завтра" if is_one_day_window else "через 2 часа"
                        
                        stream_str = ""
                        if reg.status in ["удаленно", "думаю"] and event.stream_url:
                            stream_str = f"\n\n→ <a href=\"{event.stream_url}\">Трансляция</a>"
                            
                        notification_text = (
                            f"🔔 <b>Напоминание о мероприятии!</b>\n\n"
                            f"Мероприятие {title_html} начнется {timing_desc}!\n\n"
                            f"📆 <b>Дата:</b> {config.format_display_date(event.date)}\n"
                            f"⏳ <b>Время:</b> {event.time}\n"
                            f"📍 <b>Место:</b> {event.address}"
                            f"{stream_str}"
                        )
                        
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=notification_text,
                            reply_markup=get_reminder_keyboard(event.id),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                        logger.info(f"Reminded user {user.telegram_id} about event {event.id} ({trigger_name})")
                        
                        # Update database flags
                        if is_one_day_window:
                            reg.reminded_24h = True
                        elif is_two_hours_window:
                            reg.reminded_2h = True
                        session.add(reg)
                        await session.commit()
                        
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logger.error(f"Failed to remind user {user.telegram_id}: {e}")

        # Проверка напоминаний по событиям серий (SeriesEventRegistration)
        se_res = await session.execute(select(SeriesEvent).where(SeriesEvent.is_deleted == 0))
        series_events = se_res.scalars().all()

        for sevent in series_events:
            try:
                time_str = sevent.time.strip()
                normalized_time = time_str.replace("—", "-").replace(" - ", "-").replace(" -", "-").replace("- ", "-")
                start_time_part = normalized_time.split("-")[0].strip()
                sevent_datetime = datetime.strptime(f"{sevent.date.strip()} {start_time_part}", "%d.%m.%Y %H:%M")
            except Exception:
                continue

            time_diff = sevent_datetime - now
            time_diff_hours = time_diff.total_seconds() / 3600.0

            is_one_day_window = 23.5 <= time_diff_hours <= 24.5
            is_two_hours_window = 1.8 <= time_diff_hours <= 2.2

            if not (is_one_day_window or is_two_hours_window):
                continue

            sregs_res = await session.execute(
                select(SeriesEventRegistration).where(SeriesEventRegistration.series_event_id == sevent.id)
            )
            sregistrations = sregs_res.scalars().all()

            series = await session.get(EventSeries, sevent.series_id)
            series_title = series.title if series else "Серия"

            for sreg in sregistrations:
                user = await session.get(User, sreg.user_id)
                if not user:
                    continue

                user_prefs = user.notification_preferences or {}
                should_notify = False
                trigger_name = ""

                if sreg.status == "очно":
                    if is_one_day_window:
                        trigger_name = "За день до мероприятия, на которое я иду очно"
                    elif is_two_hours_window:
                        trigger_name = "За два часа до мероприятия, на которое я иду очно"
                elif sreg.status == "удаленно":
                    if is_one_day_window:
                        trigger_name = "За день до мероприятия, на котором я буду удалённо"
                    elif is_two_hours_window:
                        trigger_name = "За два часа до мероприятия, на котором я буду удалённо"
                elif sreg.status == "думаю":
                    if is_one_day_window:
                        trigger_name = "За день до мероприятия, насчет которого я сомневаюсь"
                    elif is_two_hours_window:
                        trigger_name = "За два часа до мероприятия, насчет которого я сомневаюсь"

                if trigger_name and user_prefs.get(trigger_name, False):
                    should_notify = True

                if should_notify:
                    try:
                        timing_desc = "завтра" if is_one_day_window else "через 2 часа"
                        notification_text = (
                            f"🔔 <b>Напоминание о событии серии!</b>\n\n"
                            f"Событие <b>{sevent.topic}</b> серии <b>{series_title}</b> начнется {timing_desc}!\n\n"
                            f"📆 <b>Дата:</b> {config.format_series_date(sevent.date)}\n"
                            f"⏳ <b>Время:</b> {sevent.time}\n"
                        )
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=notification_text,
                            reply_markup=get_to_main_keyboard(),
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                        logger.info(f"Reminded user {user.telegram_id} about series event {sevent.id}")
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        logger.error(f"Failed to remind user {user.telegram_id} for series event: {e}")


async def run_reminders_scheduler(bot: Bot):
    """
    Вечный цикл планировщика (запуск проверки каждые 5 минут)
    """
    logger.info("Scheduler task started.")
    while True:
        try:
            await check_and_send_reminders(bot)
        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {e}")
        await asyncio.sleep(300) # Проверяем каждые 5 минут
