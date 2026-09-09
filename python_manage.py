import os
from process_control import kill_other_bot_processes, start_bot_detached

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
            start_bot_detached()
            print("Бот запущен в новом окне!")
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "2":
            print("\nОстановка процесса бота (только main.py)...")
            killed = kill_other_bot_processes(exclude_pid=os.getpid())
            print(f"Остановлено процессов: {killed}")
            input("\nНажмите Enter для возврата в меню...")
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
