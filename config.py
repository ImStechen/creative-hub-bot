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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///creative_hub.db")


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

