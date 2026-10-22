import shlex

from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
    validate_clause,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import (
    parse_delete,
    parse_info,
    parse_insert,
    parse_select,
    parse_update,
)
from primitive_db.utils import (
    create_cacher,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

META_FILE = "db_meta.json"
PROMPT = ">>>Введите команду: "
DATA_COMMANDS = ("insert", "select", "update", "delete", "info")

select_cache = create_cacher()


def print_help():
    """Выводит справку по командам."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where "
        "<столбец> = <значение> - прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where "
        "<столбец> = <значение> - удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def print_rows(metadata, table_name, rows):
    """Выводит записи таблицы в виде красивой таблицы."""
    if not rows:
        print("Записей не найдено.")
        return

    columns = list(metadata[table_name]["columns"])
    table = PrettyTable(columns)
    for row in rows:
        table.add_row([row[column] for column in columns])
    print(table)


@handle_db_errors
def handle_data_command(command, user_input, metadata):
    """Выполняет команды insert / select / update / delete / info."""
    match command:
        case "insert":
            table_name, values = parse_insert(user_input)
            data = load_table_data(table_name)
            result = insert(metadata, table_name, values, data)
            if result is None:
                return
            new_data, new_id = result
            save_table_data(table_name, new_data)
            select_cache.clear()
            print(
                f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".'
            )

        case "select":
            table_name, where_clause = parse_select(user_input)
            validate_clause(metadata, table_name, where_clause or {})
            key = (table_name, tuple(sorted((where_clause or {}).items())))
            rows = select_cache(
                key,
                lambda: select(load_table_data(table_name), where_clause),
            )
            print_rows(metadata, table_name, rows)

        case "update":
            table_name, set_clause, where_clause = parse_update(user_input)
            validate_clause(metadata, table_name, set_clause)
            validate_clause(metadata, table_name, where_clause)
            if "ID" in set_clause:
                raise ValueError("Менять ID нельзя.")
            data = load_table_data(table_name)
            result = update(data, set_clause, where_clause)
            if result is None:
                return
            new_data, ids = result
            if not ids:
                print("Записей не найдено.")
                return
            save_table_data(table_name, new_data)
            select_cache.clear()
            for record_id in ids:
                print(
                    f'Запись с ID={record_id} в таблице "{table_name}" '
                    "успешно обновлена."
                )

        case "delete":
            table_name, where_clause = parse_delete(user_input)
            validate_clause(metadata, table_name, where_clause)
            data = load_table_data(table_name)
            result = delete(data, where_clause)
            if result is None:
                return
            new_data, ids = result
            if not ids:
                print("Записей не найдено.")
                return
            save_table_data(table_name, new_data)
            select_cache.clear()
            for record_id in ids:
                print(
                    f"Запись с ID={record_id} успешно удалена "
                    f'из таблицы "{table_name}".'
                )

        case "info":
            table_name = parse_info(user_input)
            if table_name not in metadata:
                raise ValueError(f'Таблица "{table_name}" не существует.')
            columns = metadata[table_name]["columns"]
            columns_str = ", ".join(f"{n}:{t}" for n, t in columns.items())
            print(f"Таблица: {table_name}")
            print(f"Столбцы: {columns_str}")
            print(f"Количество записей: {len(load_table_data(table_name))}")


def run():
    """Главный цикл программы."""
    print("\n***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)

        try:
            user_input = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not user_input:
            continue

        command = user_input.split()[0]

        if command in DATA_COMMANDS:
            handle_data_command(command, user_input, metadata)
            continue

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

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
                if new_metadata is None:
                    continue
                if new_metadata != metadata:
                    save_metadata(META_FILE, new_metadata)
                    select_cache.clear()

            case "list_tables":
                list_tables(metadata)

            case "help":
                print_help()

            case "exit":
                break

            case _:
                print(f"Функции {command} нет. Попробуйте снова.")