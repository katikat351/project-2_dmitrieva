VALID_TYPES = ("int", "str", "bool")


def _parse_columns(columns):
    """Разбирает ['name:str', ...] в список пар (имя, тип).

    Возвращает None, если найдено некорректное значение (оно уже выведено).
    """
    parsed = []
    names = set()

    for column in columns:
        name, sep, col_type = column.partition(":")
        if not sep or not name or col_type not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return None
        if name in names:
            print(f'Ошибка: Столбец "{name}" указан дважды.')
            return None
        names.add(name)
        parsed.append((name, col_type))

    return parsed


def create_table(metadata, table_name, columns):
    """Создаёт таблицу, автоматически добавляя столбец ID:int первым."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed = _parse_columns(columns)
    if parsed is None:
        return metadata

    if not parsed:
        print("Ошибка: Укажите хотя бы один столбец.")
        return metadata

    # Если пользователь сам задал ID — он должен быть int, ставим его первым.
    user_ids = [item for item in parsed if item[0] == "ID"]
    if user_ids:
        if user_ids[0][1] != "int":
            print(f"Некорректное значение: ID:{user_ids[0][1]}. Попробуйте снова.")
            return metadata
        parsed = user_ids + [item for item in parsed if item[0] != "ID"]
    else:
        parsed = [("ID", "int")] + parsed

    table_columns = dict(parsed)
    columns_str = ", ".join(f"{name}:{col_type}" for name, col_type in parsed)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}')

    return {**metadata, table_name: {"columns": table_columns}}


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    print(f'Таблица "{table_name}" успешно удалена.')
    return {name: info for name, info in metadata.items() if name != table_name}


def list_tables(metadata):
    """Выводит список таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")
