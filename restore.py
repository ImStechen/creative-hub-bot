import os
import sys
import sqlite3

# Данные для разового восстановления. НЕ коммитьте персональные данные.
# Скрипт читает список словарей с ключами: fio, email, phone, status, reg_date, tg_nick.
REGISTRATIONS_DATA = []

def main():
    if not REGISTRATIONS_DATA:
        print("REGISTRATIONS_DATA пуст. Не вставляйте персональные данные в git.")
        sys.exit(1)

    db_path = "creative_hub.db"
    
    if not os.path.exists(db_path):
        print(f"Ошибка: Файл базы данных не найден по пути {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Проверяем, существует ли мероприятие с ID 7 на сервере
    cursor.execute("SELECT id, title FROM events WHERE id = 7")
    event = cursor.fetchone()
    if not event:
        print("Мероприятия с ID 7 нет в базе. Создаем временную запись...")
        cursor.execute("""
            INSERT INTO events (id, title, date, time, address, tags, images)
            VALUES (7, 'Смысл Есть: как гастродипломатия формирует визуал', '06.07.2026', '19:00', 'Хаб', '[]', '[]')
        """)
        conn.commit()
    else:
        print(f"Найдено мероприятие 7: {event[1]}")
        
    fake_id_counter = -1000000000
    cursor.execute("SELECT MIN(telegram_id) FROM users")
    min_id = cursor.fetchone()[0]
    if min_id and min_id < fake_id_counter:
        fake_id_counter = min_id - 1
        
    restored_count = 0
    
    for row in REGISTRATIONS_DATA:
        fio = row["fio"]
        email = row["email"]
        phone = row["phone"]
        status = row["status"]
        reg_date = row["reg_date"]
        tg_nick = row["tg_nick"]
        
        username = None
        if tg_nick and tg_nick != "-":
            username = tg_nick.lstrip("@").strip()
            
        user_id = None
        
        if username:
            cursor.execute("SELECT telegram_id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            res = cursor.fetchone()
            if res:
                user_id = res[0]
                
        if not user_id and phone and phone != "-":
            cursor.execute("SELECT telegram_id FROM users WHERE phone = ?", (phone,))
            res = cursor.fetchone()
            if res:
                user_id = res[0]
                
        if not user_id and email and email != "-":
            cursor.execute("SELECT telegram_id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            res = cursor.fetchone()
            if res:
                user_id = res[0]
                
        if not user_id and fio and fio != "-":
            cursor.execute("SELECT telegram_id FROM users WHERE LOWER(full_name) = LOWER(?)", (fio,))
            res = cursor.fetchone()
            if res:
                user_id = res[0]
                
        if not user_id:
            user_id = fake_id_counter
            fake_id_counter -= 1
            cursor.execute("""
                INSERT INTO users (telegram_id, username, full_name, email, phone, is_registered, tags_preferences, notification_preferences)
                VALUES (?, ?, ?, ?, ?, 1, '{"Дизайн": true, "Медиа": true, "Культура": true, "Шоу-дизайн": true, "Искусство": true, "Архитектура": true}', '{"new_events": true, "event_reminders": true}')
            """, (user_id, username, fio, email, phone))
        else:
            cursor.execute("""
                UPDATE users 
                SET full_name = COALESCE(full_name, ?),
                    email = COALESCE(email, ?),
                    phone = COALESCE(phone, ?),
                    is_registered = 1
                WHERE telegram_id = ?
            """, (fio, email, phone, user_id))
            
        cursor.execute("SELECT 1 FROM registrations WHERE user_id = ? AND event_id = 7", (user_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO registrations (user_id, event_id, status, registration_date, reminded_24h, reminded_2h)
                VALUES (?, 7, ?, ?, 0, 0)
            """, (user_id, status, reg_date))
            restored_count += 1
            
    conn.commit()
    conn.close()
    
    print(f"Успешно восстановлено {restored_count} регистраций в базе данных на сервере.")

if __name__ == "__main__":
    main()
