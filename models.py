from sqlalchemy import Column, String, BigInteger, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database.db import Base
import config

# Вспомогательные функции для дефолтных значений в БД
def get_default_tags():
    # По умолчанию пользователю проставляются все доступные теги со значением True
    return {tag: True for tag in config.DEFAULT_TAGS}

def get_default_notifications():
    # По умолчанию пользователю проставляются все типы уведомлений со значением True
    return {trigger: True for trigger in config.DEFAULT_NOTIFICATION_TRIGGERS}


class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String, nullable=True)
    
    # Регистрационная анкета
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True, default='-')
    is_registered = Column(Boolean, nullable=False, default=False)
    
    # JSON-хранилище для настроек тегов: {"Дизайн": true, "Медиа": true, ...}
    tags_preferences = Column(JSON, nullable=False, default=get_default_tags)
    
    # JSON-хранилище для уведомлений: {"new_events": true, "event_reminders": true, ...}
    notification_preferences = Column(JSON, nullable=False, default=get_default_notifications)

    # Отношение к регистрациям
    registrations = relationship("Registration", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User telegram_id={self.telegram_id} username={self.username}>"


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    title_url = Column(String, nullable=True) # Ссылка на мероприятие
    
    date = Column(String, nullable=False) # Формат ЧЧ.ММ.ГГГГ
    time = Column(String, nullable=False) # Формат ЧЧ:ММ
    address = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    reg_url = Column(String, nullable=True) # Ссылка на регистрацию
    stream_url = Column(String, nullable=True) # Ссылка на трансляцию
    
    # Список тегов мероприятия в формате JSON-массива строк, например: ["Дизайн", "Медиа"]
    tags = Column(JSON, nullable=False, default=list)
    
    # Список ссылок на изображения/File ID в Telegram: ["file_id_1", "file_id_2"]
    images = Column(JSON, nullable=False, default=list)
    
    hide_date = Column(String, nullable=True) # Дата скрытия мероприятия ЧЧ.ММ.ГГГГ
    hide_time = Column(String, nullable=True) # Время скрытия мероприятия ЧЧ:ММ

    # Ссылки на пост-материалы прошедшего мероприятия
    photos_url = Column(String, nullable=True)         # Ссылка на фото
    stream_record_url = Column(String, nullable=True)  # Ссылка на запись трансляции
    article_url = Column(String, nullable=True)        # Ссылка на конспект-статью
    presentations_url = Column(String, nullable=True)  # Ссылка на презентации
    other_materials_url = Column(String, nullable=True) # Ссылка на другие материалы

    # Отношение к регистрациям
    registrations = relationship("Registration", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event id={self.id} title={self.title} date={self.date} time={self.time}>"


class Registration(Base):
    __tablename__ = 'registrations'

    user_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete="CASCADE"), primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id', ondelete="CASCADE"), primary_key=True)
    
    # Статус участия: "очно", "удаленно", "думаю", "не пойду"
    status = Column(String, nullable=False, default="думаю")
    
    # Дата регистрации
    registration_date = Column(String, nullable=True)

    # Флаги напоминаний во избежание дублирования
    reminded_24h = Column(Boolean, nullable=False, default=False, server_default="0")
    reminded_2h = Column(Boolean, nullable=False, default=False, server_default="0")

    # Обратные связи
    user = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

    def __repr__(self):
        return f"<Registration user_id={self.user_id} event_id={self.event_id} status={self.status}>"


class Raffle(Base):
    __tablename__ = 'raffles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    is_active = Column(Integer, nullable=False, default=1) # 1 - активен, 0 - неактивен
    
    hide_date = Column(String, nullable=True) # Дата скрытия розыгрыша ЧЧ.ММ.ГГГГ
    hide_time = Column(String, nullable=True) # Время скрытия розыгрыша ЧЧ:ММ

    # Связь с конкретным мероприятием для таргетирования розыгрыша по тегам
    event_id = Column(Integer, ForeignKey('events.id', ondelete="SET NULL"), nullable=True)
    event = relationship("Event")

    def __repr__(self):
        return f"<Raffle id={self.id} title={self.title} is_active={self.is_active}>"


class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False) # Телеграм-никнейм без символа @

    def __repr__(self):
        return f"<Admin id={self.id} username={self.username}>"


class SystemTag(Base):
    __tablename__ = 'system_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<SystemTag id={self.id} name={self.name}>"


class FeedbackMessage(Base):
    __tablename__ = 'feedback_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(String, nullable=False) # Формат YYYY-MM-DD HH:MM:SS

    def __repr__(self):
        return f"<FeedbackMessage id={self.id} user_id={self.user_id} text={self.text[:20]}...>"



