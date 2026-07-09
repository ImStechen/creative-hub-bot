from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import is_super_admin

def get_main_menu_keyboard(is_admin: bool, raffle_count: int) -> InlineKeyboardMarkup:
    """
    Генерирует главное меню с Inline-кнопками согласно доке.
    """
    buttons = [
        [InlineKeyboardButton(text="Подробнее о мероприятиях", callback_data="btn_events_info")],
        [InlineKeyboardButton(text="Настроить предпочтения", callback_data="btn_preferences")],
        [InlineKeyboardButton(text="Архив пост-материалов", callback_data="btn_archive")]
    ]
    
    # Кнопка обратной связи показывается только рядовым пользователям и без эмодзи
    if not is_admin:
        buttons.append([InlineKeyboardButton(text="Обратная связь", callback_data="btn_feedback")])
    
    if raffle_count > 0:
        buttons.append([InlineKeyboardButton(text=f"Розыгрыш ({raffle_count})", callback_data="btn_raffle")])
        
    if is_admin:
        buttons.append([InlineKeyboardButton(text="Администрирование", callback_data="btn_admin")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_feedback_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-кнопку отмены обратной связи.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel_feedback")]]
    )


def get_events_list_keyboard(events: list, partners_count: int = 0) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-кнопки для списка доступных мероприятий.
    """
    buttons = []
    for event in events:
        buttons.append([InlineKeyboardButton(text=event.title, callback_data=f"show_event_{event.id}")])
    
    buttons.append([InlineKeyboardButton(text=f"Мероприятия партнеров ({partners_count})", callback_data="btn_partners_events")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_detail_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует кнопки статусов участия для конкретного мероприятия.
    """
    buttons = [
        [
            InlineKeyboardButton(text="Буду очно", callback_data=f"reg_status_{event_id}_очно"),
            InlineKeyboardButton(text="Буду удаленно", callback_data=f"reg_status_{event_id}_удаленно")
        ],
        [
            InlineKeyboardButton(text="Пока думаю", callback_data=f"reg_status_{event_id}_думаю"),
            InlineKeyboardButton(text="Точно не пойду", callback_data=f"reg_status_{event_id}_не пойду")
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_events_info"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_registration_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует кнопки перехода после выбора статуса участия.
    """
    buttons = [
        [InlineKeyboardButton(text="К другим мероприятиям", callback_data="btn_events_info")],
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_to_main_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует одну кнопку 'На главную'.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")]
    ])


def get_preferences_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует меню выбора типа настроек.
    """
    buttons = [
        [InlineKeyboardButton(text="Предпочтения по темам мероприятий", callback_data="pref_tags")],
        [InlineKeyboardButton(text="Предпочтения по уведомлениям", callback_data="pref_notifications")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


SHORT_NOTIFICATION_LABELS = {
    "Появилось мероприятие по избранной теме": "Новое мероприятие по моей теме",
    "За день до мероприятия, на которое я иду очно": "За день до события (очно)",
    "За два часа до мероприятия, на которое я иду очно": "За 2 часа до события (очно)",
    "За день до мероприятия, на котором я буду удалённо": "За день до события (удалённо)",
    "За два часа до мероприятия, на котором я буду удалённо": "За 2 часа до события (удалённо)",
    "За день до мероприятия, насчет которого я сомневаюсь": "За день до события (думаю)",
    "За два часа до мероприятия, насчет которого я сомневаюсь": "За 2 часа до события (думаю)",
    "После мероприятия, когда появятся пост-материалы": "Когда появятся пост-материалы"
}

def get_checkbox_keyboard(items: dict, pref_type: str) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с чекбоксами (теги или уведомления).
    """
    buttons = []
    
    # Для уведомлений кнопки широкие, выводим по одной в строку
    is_notifs = (pref_type == "notifs")
    
    current_row = []
    for idx, (name, value) in enumerate(items.items()):
        status_emoji = "✅" if value else "❌"
        cb_data = f"cb_{pref_type}_{idx}"
        
        display_name = SHORT_NOTIFICATION_LABELS.get(name, name) if is_notifs else name
        
        button = InlineKeyboardButton(
            text=f"{status_emoji} {display_name}",
            callback_data=cb_data
        )
        if is_notifs:
            buttons.append([button])
        else:
            current_row.append(button)
            if len(current_row) == 2:
                buttons.append(current_row)
                current_row = []
                
    if current_row and not is_notifs:
        buttons.append(current_row)
        
    buttons.append([InlineKeyboardButton(text="Сохранить", callback_data=f"save_{pref_type}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="btn_preferences")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_save_tags_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после сохранения настроек тегов.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")]
    ])


def get_to_main_back_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой '← На главную'.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← На главную", callback_data="back_to_main")]
    ])


def get_partners_events_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для списка партнерских мероприятий:
    [Назад] | [← К списку]
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_events_info"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ])


def get_archive_tags_keyboard(tags: list, unread_tags: set = None) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру со списком тегов для архива пост-материалов.
    """
    if unread_tags is None:
        unread_tags = set()
    buttons = []
    current_row = []
    for idx, tag in enumerate(tags):
        display_name = f"🔥 {tag}" if tag in unread_tags else tag
        current_row.append(InlineKeyboardButton(text=display_name, callback_data=f"arch_tag_{idx}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
        
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_archive_events_keyboard(events: list, unread_event_ids: set = None) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру списка мероприятий в архиве для конкретного тега.
    """
    if unread_event_ids is None:
        unread_event_ids = set()
    buttons = []
    for event in events:
        display_title = f"🔥 {event.title}" if event.id in unread_event_ids else event.title
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"arch_event_{event.id}")])
        
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="btn_archive")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_archive_detail_keyboard(tag_idx: int) -> InlineKeyboardMarkup:
    """
    Генерирует кнопки навигации из карточки пост-материалов мероприятия.
    """
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data=f"arch_tag_{tag_idx}"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_detail_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для окна розыгрыша.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])


def get_registration_keyboard(step: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру для шагов авторизации.
    """
    buttons = []
    if step == 3:
        buttons.append([InlineKeyboardButton(text="Пропустить этот пункт", callback_data="reg_skip_phone")])
    buttons.append([InlineKeyboardButton(text="Пропустить регистрацию", callback_data="reg_skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_notification_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура уведомления о новом мероприятии.
    """
    buttons = [
        [InlineKeyboardButton(text="Подробнее", callback_data=f"show_event_{event_id}")],
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_reminder_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура напоминания о предстоящем мероприятии.
    """
    buttons = [
        [InlineKeyboardButton(text="Подробнее о мероприятии", callback_data=f"show_event_{event_id}")],
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_agreement_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для принятия Положения о персональных данных.
    """
    buttons = [
        [InlineKeyboardButton(text="✅ Принять Положение и продолжить", callback_data="reg_accept")],
        [InlineKeyboardButton(text="Пропустить регистрацию", callback_data="reg_skip")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



