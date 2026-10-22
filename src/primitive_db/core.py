from primitive_db.decorators import confirm_action, handle_db_errors, log_time

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


@handle_db_errors
@confirm_action("удаление таблицы")
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


TYPE_MAP = {"int": int, "str": str, "bool": bool}


def _check_type(value, type_name):
    """Проверяет, что значение подходит под тип столбца."""
    if type_name == "int":
        # bool в Python это подкласс int, поэтому исключаем его отдельно
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, TYPE_MAP[type_name])


def _get_schema(metadata, table_name):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    return metadata[table_name]["columns"]


def validate_clause(metadata, table_name, clause):
    """Проверяет, что в условии есть такие столбцы и типы значений верные."""
    schema = _get_schema(metadata, table_name)
    for column, value in clause.items():
        if column not in schema:
            raise ValueError(f'Столбца "{column}" нет в таблице "{table_name}".')
        if not _check_type(value, schema[column]):
            raise ValueError(
                f'Неверный тип значения для "{column}": '
                f"ожидается {schema[column]}."
            )


@handle_db_errors
@log_time
def insert(metadata, table_name, values, table_data):
    """Добавляет запись. Возвращает (новые данные таблицы, новый ID)."""
    schema = _get_schema(metadata, table_name)
    columns = [name for name in schema if name != "ID"]

    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается значений: {len(columns)}, передано: {len(values)}."
        )

    record = {}
    for column, value in zip(columns, values):
        if not _check_type(value, schema[column]):
            raise ValueError(
                f'Неверный тип значения для "{column}": '
                f"ожидается {schema[column]}."
            )
        record[column] = value

    new_id = max((row["ID"] for row in table_data), default=0) + 1
    new_record = {"ID": new_id, **record}
    return table_data + [new_record], new_id


def _matches(record, where_clause):
    return all(record.get(key) == value for key, value in where_clause.items())


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает все записи или только подходящие под условие."""
    if not where_clause:
        return table_data
    return [row for row in table_data if _matches(row, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет подходящие записи. Возвращает (данные, список обновлённых ID)."""
    updated_ids = []
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
            updated_ids.append(row["ID"])
    return table_data, updated_ids


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет подходящие записи. Возвращает (данные, список удалённых ID)."""
    deleted_ids = [row["ID"] for row in table_data if _matches(row, where_clause)]
    remaining = [row for row in table_data if not _matches(row, where_clause)]
    return remaining, deleted_ids