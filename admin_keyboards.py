from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура главного меню админки.
    """
    buttons = [
        [InlineKeyboardButton(text="Выгрузить список регистраций", callback_data="admin_export_registrations")],
        [InlineKeyboardButton(text="Редактировать мероприятие", callback_data="admin_edit_events")],
        [InlineKeyboardButton(text="Редактировать серию мероприятий", callback_data="admin_edit_series")],
        [InlineKeyboardButton(text="Редактировать теги", callback_data="admin_edit_tags")],
        [InlineKeyboardButton(text="Редактировать пост-материалы", callback_data="admin_edit_post_mats")],
        [InlineKeyboardButton(text="Редактировать розыгрыш", callback_data="admin_edit_raffles")],
        [InlineKeyboardButton(text="Посмотреть обратную связь", callback_data="admin_view_feedback")],
        [InlineKeyboardButton(text="Права администратора", callback_data="admin_rights")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_feedback_navigation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн-кнопки перелистывания обратной связи по кругу с возможностью ответа.
    """
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="feedback_nav_prev"),
            InlineKeyboardButton(text="Дальше", callback_data="feedback_nav_next")
        ],
        [
            InlineKeyboardButton(text="Ответить", callback_data=f"admin_reply_feedback_{user_id}"),
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skip_keyboard(callback_data: str, show_back: bool = False, back_callback: str = "admin_cancel") -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Пропустить".
    """
    buttons = []
    row = [InlineKeyboardButton(text="Пропустить", callback_data=callback_data)]
    buttons.append(row)
    
    control_row = []
    if show_back:
        control_row.append(InlineKeyboardButton(text="Назад", callback_data=back_callback))
    control_row.append(InlineKeyboardButton(text="Отменить", callback_data="admin_cancel"))
    buttons.append(control_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard(show_back: bool = False, back_callback: str = "admin_cancel") -> InlineKeyboardMarkup:
    """
    Клавиатура отмены / возврата.
    """
    row = []
    if show_back:
        row.append(InlineKeyboardButton(text="Назад", callback_data=back_callback))
    row.append(InlineKeyboardButton(text="Отменить", callback_data="admin_cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def get_address_keyboard(show_back: bool = False, back_callback: str = "admin_cancel") -> InlineKeyboardMarkup:
    """
    Клавиатура для шага ввода адреса с кнопкой автозаполнения адреса Хаба.
    """
    buttons = [
        [InlineKeyboardButton(text="Вставить адрес Хаба", callback_data="admin_event_default_address")]
    ]
    row = []
    if show_back:
        row.append(InlineKeyboardButton(text="Назад", callback_data=back_callback))
    row.append(InlineKeyboardButton(text="Отменить", callback_data="admin_cancel"))
    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_events_keyboard() -> InlineKeyboardMarkup:
    """
    Меню управления мероприятиями.
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить новое мероприятие", callback_data="admin_add_event")],
        [InlineKeyboardButton(text="Редактировать существующее мероприятие", callback_data="admin_edit_event_list")],
        [InlineKeyboardButton(text="Редактировать архивное мероприятие", callback_data="admin_edit_archive_tags")],
        [InlineKeyboardButton(text="Удалить мероприятие", callback_data="admin_del_event_list")],
        [InlineKeyboardButton(text="Добавить партнерское мероприятие", callback_data="admin_add_partner_event")],
        [InlineKeyboardButton(text="Удалить партнерское мероприятие", callback_data="admin_del_partner_event_list")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_partner_events_keyboard(events: list) -> InlineKeyboardMarkup:
    """
    Список партнерских мероприятий для удаления.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_del_pevent_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_events"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_select_edit_keyboard(events: list) -> InlineKeyboardMarkup:
    """
    Список мероприятий для редактирования разделов.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_select_edit_event_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_events"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_sections_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Список разделов мероприятия для редактирования.
    """
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"edit_evsec_{event_id}_title")],
        [InlineKeyboardButton(text="Ссылка, вшиваемая в название", callback_data=f"edit_evsec_{event_id}_titleurl")],
        [InlineKeyboardButton(text="Отображаемая дата мероприятия", callback_data=f"edit_evsec_{event_id}_date")],
        [InlineKeyboardButton(text="Отображаемое время мероприятия", callback_data=f"edit_evsec_{event_id}_time")],
        [InlineKeyboardButton(text="Отображаемый адрес мероприятия", callback_data=f"edit_evsec_{event_id}_address")],
        [InlineKeyboardButton(text="Основной текст", callback_data=f"edit_evsec_{event_id}_desc")],
        [InlineKeyboardButton(text="Ссылка на регистрацию", callback_data=f"edit_evsec_{event_id}_regurl")],
        [InlineKeyboardButton(text="Ссылка на трансляцию", callback_data=f"edit_evsec_{event_id}_streamurl")],
        [InlineKeyboardButton(text="Выбор тегов", callback_data=f"edit_evsec_{event_id}_tags")],
        [InlineKeyboardButton(text="Добавление изображения", callback_data=f"edit_evsec_{event_id}_image")],
        [InlineKeyboardButton(text="Дата, когда мероприятие должно исчезнуть из видимости", callback_data=f"edit_evsec_{event_id}_hidedate")],
        [InlineKeyboardButton(text="Время, когда мероприятие должно исчезнуть из видимости", callback_data=f"edit_evsec_{event_id}_hidetime")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_edit_event_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_edit_event_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура после завершения редактирования.
    """
    buttons = [
        [InlineKeyboardButton(text="Отредактировать другой раздел", callback_data=f"admin_select_edit_event_{event_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_edit_event_list")],
        [InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_delete_keyboard(events: list) -> InlineKeyboardMarkup:
    """
    Список мероприятий для удаления.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_confirm_del_event_{e.id}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="admin_edit_events")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_delete_event_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Подтверждение удаления события.
    """
    buttons = [
        [InlineKeyboardButton(text="Удалить выбранное мероприятие", callback_data=f"admin_delete_event_final_{event_id}")],
        [InlineKeyboardButton(text="Отмена", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_deleted_event_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после удаления мероприятия.
    """
    buttons = [
        [
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_tags_keyboard() -> InlineKeyboardMarkup:
    """
    Меню управления тегами.
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить новый тег", callback_data="admin_add_tag")],
        [InlineKeyboardButton(text="Удалить тег", callback_data="admin_del_tag_list")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_tag_created_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после успешного создания тега.
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить еще тег", callback_data="admin_add_tag")],
        [
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tag_delete_keyboard(tags: list) -> InlineKeyboardMarkup:
    """
    Список тегов для удаления.
    """
    buttons = []
    for i, t in enumerate(tags):
        buttons.append([InlineKeyboardButton(text=t, callback_data=f"admin_confirm_del_tag_{i}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_tags"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_tag_deleted_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после удаления тега.
    """
    buttons = [
        [
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_raffles_keyboard() -> InlineKeyboardMarkup:
    """
    Меню управления розыгрышами.
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить новый розыгрыш", callback_data="admin_add_raffle")],
        [InlineKeyboardButton(text="Редактировать существующий розыгрыш", callback_data="admin_edit_raffle_list")],
        [InlineKeyboardButton(text="Удалить розыгрыш", callback_data="admin_del_raffle_list")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_select_edit_keyboard(raffles: list) -> InlineKeyboardMarkup:
    """
    Список розыгрышей для изменения полей.
    """
    buttons = []
    for r in raffles:
        buttons.append([InlineKeyboardButton(text=r.title, callback_data=f"admin_select_edit_raffle_{r.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_raffles"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_sections_keyboard(raffle_id: int) -> InlineKeyboardMarkup:
    """
    Список разделов розыгрыша для изменения.
    """
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"edit_rafsec_{raffle_id}_title")],
        [InlineKeyboardButton(text="Ссылка, вшиваемая в название", callback_data=f"edit_rafsec_{raffle_id}_url")],
        [InlineKeyboardButton(text="Основной текст", callback_data=f"edit_rafsec_{raffle_id}_desc")],
        [InlineKeyboardButton(text="Дата, когда розыгрыш должен исчезнуть из видимости", callback_data=f"edit_rafsec_{raffle_id}_hidedate")],
        [InlineKeyboardButton(text="Время, когда розыгрыш должен исчезнуть из видимости", callback_data=f"edit_rafsec_{raffle_id}_hidetime")],
        [InlineKeyboardButton(text="Привязка к мероприятию", callback_data=f"edit_rafsec_{raffle_id}_eventid")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_edit_raffle_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_edit_raffle_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после сохранения изменений розыгрыша.
    """
    buttons = [
        [InlineKeyboardButton(text="Отредактировать другой раздел", callback_data="admin_edit_raffle_list")],
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")],
        [InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_delete_keyboard(raffles: list) -> InlineKeyboardMarkup:
    """
    Список розыгрышей для удаления.
    """
    buttons = []
    for r in raffles:
        buttons.append([InlineKeyboardButton(text=r.title, callback_data=f"admin_confirm_del_raffle_{r.id}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="admin_edit_raffles")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_delete_raffle_keyboard(raffle_id: int) -> InlineKeyboardMarkup:
    """
    Подтверждение удаления розыгрыша.
    """
    buttons = [
        [InlineKeyboardButton(text="Удалить выбранный розыгрыш", callback_data=f"admin_delete_raffle_final_{raffle_id}")],
        [InlineKeyboardButton(text="Отмена", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_deleted_raffle_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после удаления розыгрыша.
    """
    buttons = [
        [InlineKeyboardButton(text="На главную", callback_data="back_to_main")],
        [InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_link_choice_keyboard() -> InlineKeyboardMarkup:
    """
    Вопрос привязки при создании розыгрыша.
    """
    buttons = [
        [InlineKeyboardButton(text="Выбрать мероприятие", callback_data="admin_raffle_link_select")],
        [InlineKeyboardButton(text="Не привязывать и завершить", callback_data="admin_raffle_link_none")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_link_event_keyboard(events: list) -> InlineKeyboardMarkup:
    """
    Выбор мероприятия для привязки.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_raffle_link_event_{e.id}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="admin_raffle_link_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_raffle_save_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки завершения добавления розыгрыша.
    """
    buttons = [
        [
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_rights_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура раздела "Права администратора".
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить админа", callback_data="admin_add_rights")],
        [InlineKeyboardButton(text="Удалить админа", callback_data="admin_del_rights_list")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_delete_select_keyboard(admins: list) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком админов для удаления.
    """
    buttons = []
    for a in admins:
        if a.username.lower() != "asaavedraa":
            buttons.append([InlineKeyboardButton(text=f"@{a.username}", callback_data=f"admin_del_rights_{a.id}")])
    buttons.append([InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_tags_selection_keyboard(tags: list, selected_tags: list, step_mode: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора тегов мероприятия с помощью чекбоксов (для формы создания).
    """
    buttons = []
    current_row = []
    for idx, t in enumerate(tags):
        emoji = "✅" if t in selected_tags else "❌"
        buttons.append([InlineKeyboardButton(text=f"{emoji} {t}", callback_data=f"admin_evtag_{idx}")])
        
    buttons.append([InlineKeyboardButton(text="Сохранить теги", callback_data="admin_evtag_confirm")])
    if step_mode:
        buttons.append([InlineKeyboardButton(text="Пропустить", callback_data="skip_tags")])
        buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_tags")])
    else:
        buttons.append([InlineKeyboardButton(text="Назад", callback_data="admin_cancel")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_image_add_keyboard(has_images: bool) -> InlineKeyboardMarkup:
    """
    Кнопки шага добавления изображений.
    """
    buttons = []
    if has_images:
        buttons.append([InlineKeyboardButton(text="Добавить еще изображение", callback_data="admin_image_add_more")])
        buttons.append([InlineKeyboardButton(text="Сохранить изображения", callback_data="admin_image_save")])
    else:
        buttons.append([InlineKeyboardButton(text="Пропустить", callback_data="skip_image")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_image")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_event_created_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после успешного добавления мероприятия.
    """
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_edit_events"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ],
        [InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_finish_event_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура на последнем шаге добавления мероприятия (время скрытия).
    """
    buttons = [
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_hide_time")],
        [InlineKeyboardButton(text="Назад", callback_data="back_hide_time")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def get_admin_post_mats_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура раздела "Редактировать пост-материалы".
    """
    buttons = [
        [InlineKeyboardButton(text="Добавить пост-материалы", callback_data="admin_add_post_mats")],
        [InlineKeyboardButton(text="Удалить пост-материалы", callback_data="admin_del_post_mats")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_post_mats_event_select_keyboard(events: list, is_delete: bool = False) -> InlineKeyboardMarkup:
    """
    Выбор мероприятия для добавления или удаления пост-материалов.
    """
    buttons = []
    prefix = "admin_pm_del_" if is_delete else "admin_pm_add_"
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"{prefix}{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_post_mats"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_post_mats_saved_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после сохранения пост-материалов.
    """
    buttons = [
        [
            InlineKeyboardButton(text="В Администрирование", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_del_post_mats_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """
    Подтверждение удаления пост-материалов.
    """
    buttons = [
        [InlineKeyboardButton(text="Да, удалить", callback_data=f"admin_pm_del_confirm_{event_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_edit_post_mats")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_post_mats_tags_keyboard(tags: list, is_delete: bool = False) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру со списком тегов для выбора мероприятия при добавлении/удалении пост-материалов.
    """
    buttons = []
    current_row = []
    prefix = "pm_tag_del_" if is_delete else "pm_tag_add_"
    for idx, tag in enumerate(tags):
        current_row.append(InlineKeyboardButton(text=tag, callback_data=f"{prefix}{idx}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
        
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_post_mats"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_raffle_edit_link_event_keyboard(events: list, raffle_id: int) -> InlineKeyboardMarkup:
    """
    Выбор мероприятия для привязки при редактировании розыгрыша.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_raf_edit_link_{raffle_id}_{e.id}")])
    buttons.append([InlineKeyboardButton(text="Не привязывать", callback_data=f"admin_raf_edit_link_{raffle_id}_none")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=f"admin_select_edit_raffle_{raffle_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_archive_tags_keyboard(tags: list) -> InlineKeyboardMarkup:
    """
    Список тегов для выбора архивного мероприятия для редактирования.
    """
    buttons = []
    current_row = []
    for idx, tag in enumerate(tags):
        current_row.append(InlineKeyboardButton(text=tag, callback_data=f"admin_archtag_{idx}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_events"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_archive_events_keyboard(events: list, tag_idx: int) -> InlineKeyboardMarkup:
    """
    Список архивных мероприятий по выбранному тегу для редактирования.
    """
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=e.title, callback_data=f"admin_select_edit_event_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_edit_archive_tags"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_export_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Активные мероприятия", callback_data="admin_export_select_active")],
        [InlineKeyboardButton(text="Архивные мероприятия", callback_data="admin_export_select_archive")],
        [
            InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_export_events_keyboard(events: list, reg_counts: dict = None) -> InlineKeyboardMarkup:
    if reg_counts is None:
        reg_counts = {}
    buttons = []
    for e in events:
        cnt = reg_counts.get(e.id, 0)
        display_title = f"({cnt}) {e.title}"
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"admin_export_event_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_export_registrations"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_export_archive_tags_keyboard(tags: list) -> InlineKeyboardMarkup:
    buttons = []
    current_row = []
    for idx, tag in enumerate(tags):
        current_row.append(InlineKeyboardButton(text=tag, callback_data=f"admin_exarchtag_{idx}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_export_registrations"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_export_archive_events_keyboard(events: list, tag_idx: int, reg_counts: dict = None) -> InlineKeyboardMarkup:
    if reg_counts is None:
        reg_counts = {}
    buttons = []
    for e in events:
        cnt = reg_counts.get(e.id, 0)
        display_title = f"({cnt}) {e.title}"
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"admin_export_event_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="admin_export_select_archive"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_export_back_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_export_registrations"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_series_list_keyboard(series_list: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in series_list:
        buttons.append([InlineKeyboardButton(text=s.title, callback_data=f"admin_select_series_{s.id}")])
    buttons.append([InlineKeyboardButton(text="Создать серию", callback_data="admin_create_series")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data="btn_admin"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_series_actions_keyboard(series_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Выгрузить список регистраций", callback_data=f"admin_series_export_{series_id}")],
        [InlineKeyboardButton(text="Добавить событие", callback_data=f"admin_series_add_event_{series_id}")],
        [InlineKeyboardButton(text="Удалить событие", callback_data=f"admin_series_del_event_list_{series_id}")],
        [InlineKeyboardButton(text="Редактировать текст-описание серии", callback_data=f"admin_series_edit_info_{series_id}")],
        [InlineKeyboardButton(text="Редактировать анкету регистрации", callback_data=f"admin_series_edit_form_{series_id}")],
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_edit_series"),
            InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_questionnaire_loop_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_q_back"),
            InlineKeyboardButton(text="Отмена", callback_data="admin_cancel"),
            InlineKeyboardButton(text="Завершить", callback_data="admin_q_finish")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_series_events_select_keyboard(events: list, prefix: str, series_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for e in events:
        buttons.append([InlineKeyboardButton(text=f"{e.date} | {e.topic}", callback_data=f"{prefix}_{e.id}")])
    buttons.append([
        InlineKeyboardButton(text="Назад", callback_data=f"admin_select_series_{series_id}"),
        InlineKeyboardButton(text="← К списку", callback_data="back_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)




