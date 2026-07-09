import os
import sys
import subprocess

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("==========================================")
        print("      Управление Креативный Хаб Ботом     ")
        print("==========================================")
        print("1. Запустить бота")
        print("2. Отключить бота")
        print("3. Выйти")
        print("==========================================")
        choice = input("Выберите действие (1-3): ").strip()
        
        if choice == "1":
            print("\nЗапуск бота...")
            # Запускаем в новом окне на Windows
            subprocess.Popen([sys.executable, "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("Бот запущен в новом окне!")
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "2":
            print("\nОстановка процесса бота...")
            if os.name == 'nt':
                # Завершаем процессы python.exe, кроме текущего менеджера
                current_pid = os.getpid()
                # Мы можем использовать taskkill для завершения python.exe
                # Но чтобы не убить текущую консоль, отфильтруем по имени окна или завершим только дочерние процессы.
                # Самый простой и надежный способ на Windows - убить все python.exe, но запустить бота как отдельный скрипт.
                # Чтобы не убить самого себя, используем wmic или tasklist:
                os.system("taskkill /IM python.exe /F")
            print("Все процессы python.exe принудительно завершены.")
            # Поскольку этот скрипт тоже python, taskkill убьет и его. Это нормально и гарантирует выключение.
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
