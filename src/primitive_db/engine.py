import shlex

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

META_FILE = "db_meta.json"
PROMPT = ">>>Введите команду: "


def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """Главный цикл программы."""
    print("\n***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)

        try:
            user_input = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            continue

        command = args[0]

        match command:
            case "create_table":
                if len(args) < 3:
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                    continue
                new_metadata = create_table(metadata, args[1], args[2:])
                if new_metadata != metadata:
                    save_metadata(META_FILE, new_metadata)

            case "drop_table":
                if len(args) != 2:
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                    continue
                new_metadata = drop_table(metadata, args[1])
                if new_metadata != metadata:
                    save_metadata(META_FILE, new_metadata)

            case "list_tables":
                list_tables(metadata)

            case "help":
                print_help()

            case "exit":
                break

            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
