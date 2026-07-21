# Глобальные настройки и константы
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8732094097:AAESo74ULzp-s8O0oRbSXhKvPUOKGS3eaqg")

# Никнейм суперадминистратора
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "ASaavedraA")

# Список доступных тегов по умолчанию в системе
DEFAULT_TAGS = [
    "Наука",
    "Digital_Дизайн",
    "ЛюксПерсоны",
    "КреативныйБизнес",
    "Архитектура",
    "Саунд_Дизайн",
    "ЭкранныеИскусства",
    "ИскусственныйИнтеллект",
    "Брендинг_Дизайн",
    "Фотография",
    "Ивент_и_Театр",
    "Мода_Одежда",
    "Пром_Дизайн",
    "Медиа_дизайн",
    "Иллюстрация",
    "Среда_Интерьер",
    "СовременноеИскусство",
    "ГеймДизайн",
    "Анимация_CGI"
]

# Точные формулировки 8 триггеров уведомлений из UserFlow.docx
DEFAULT_NOTIFICATION_TRIGGERS = [
    "Появилось мероприятие по избранной теме",
    "За день до мероприятия, на которое я иду очно",
    "За два часа до мероприятия, на которое я иду очно",
    "За день до мероприятия, на котором я буду удалённо",
    "За два часа до мероприятия, на котором я буду удалённо",
    "За день до мероприятия, насчет которого я сомневаюсь",
    "За два часа до мероприятия, насчет которого я сомневаюсь",
    "После мероприятия, когда появятся пост-материалы"
]

# Строка подключения к базе данных SQLite (асинхронная)
DATA_DIR = os.getenv('DATA_DIR', '.')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'creative_hub.db')}"


def is_super_admin(username: str | None) -> bool:
    """
    Глобальная проверка, является ли пользователь суперадминистратором.
    """
    if not username:
        return False
    # Убираем '@', если он есть в начале никнейма
    clean_username = username.lstrip('@')
    return clean_username.lower() == SUPER_ADMIN_USERNAME.lower()


def format_display_date(date_str: str | None) -> str:
    """
    Форматирует дату из формата ДД.ММ.ГГГГ в ДД месяц ГГГГ (например, 12 июня 2026).
    Поддерживает диапазоны дат ДД.ММ.ГГГГ-ДД.ММ.ГГГГ.
    Если формат неверный, возвращает исходную строку.
    """
    if not date_str:
        return ""
        
    if "-" in date_str:
        parts = date_str.split("-")
        if len(parts) == 2:
            start_fmt = format_display_date(parts[0].strip())
            end_fmt = format_display_date(parts[1].strip())
            if start_fmt != parts[0].strip() and end_fmt != parts[1].strip():
                return f"{start_fmt} — {end_fmt}"
        return date_str
        
    parts = date_str.split('.')
    if len(parts) != 3:
        return date_str
    
    months = {
        "01": "января", "1": "января",
        "02": "февраля", "2": "февраля",
        "03": "марта", "3": "марта",
        "04": "апреля", "4": "апреля",
        "05": "мая", "5": "мая",
        "06": "июня", "6": "июня",
        "07": "июля", "7": "июля",
        "08": "августа", "8": "августа",
        "09": "сентября", "9": "сентября",
        "10": "октября",
        "11": "ноября",
        "12": "декабря"
    }
    
    day, month, year = parts
    try:
        day_num = str(int(day))
    except ValueError:
        day_num = day
        
    month_name = months.get(month)
    if not month_name:
        return date_str
        
    return f"{day_num} {month_name} {year}"


def format_series_date(date_str: str | None) -> str:
    """
    Форматирует дату серии мероприятий из формата ДД.ММ.ГГГГ в ДД месяц (например, 17 сентября).
    """
    if not date_str:
        return ""
    full_fmt = format_display_date(date_str)
    import re
    return re.sub(r'\s+\d{4}', '', full_fmt)


def format_partner_date(date_str: str) -> str:
    """
    Форматирует дату для партнерских мероприятий:
    - Двойную дату пишет через - и без пробелов.
    - Если год начала и окончания совпадают, пишем только год конца ивента.
    - Пример: 6 июля-17 июля 2026
    """
    if not date_str:
        return ""
        
    date_str = date_str.strip()
    if "-" in date_str:
        parts = date_str.split("-")
        if len(parts) == 2:
            d1_parts = parts[0].strip().split('.')
            d2_parts = parts[1].strip().split('.')
            if len(d1_parts) == 3 and len(d2_parts) == 3:
                day1, month1_num, year1 = d1_parts
                day2, month2_num, year2 = d2_parts
                
                months = {
                    "01": "января", "02": "февраля", "03": "марта", "04": "апреля",
                    "05": "мая", "06": "июня", "07": "июля", "08": "августа",
                    "09": "сентября", "10": "октября", "11": "ноября", "12": "декабря"
                }
                
                m1 = months.get(month1_num, month1_num)
                m2 = months.get(month2_num, month2_num)
                
                try:
                    d1_clean = str(int(day1))
                except ValueError:
                    d1_clean = day1
                try:
                    d2_clean = str(int(day2))
                except ValueError:
                    d2_clean = day2
                
                if year1 == year2:
                    return f"{d1_clean} {m1}-{d2_clean} {m2} {year2}"
                else:
                    return f"{d1_clean} {m1} {year1}-{d2_clean} {m2} {year2}"
                    
    # Если не диапазон или не удалось распарсить
    return format_display_date(date_str)

