from primitive_db.constants import (
    DELETE_USAGE,
    INFO_USAGE,
    INSERT_USAGE,
    QUOTES,
    SELECT_USAGE,
    UPDATE_USAGE,
)


def parse_value(raw):
    """Превращает строку из команды в значение: "abc", 28 или true."""
    raw = raw.strip()

    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        raise ValueError(
            f"Некорректное значение: {raw}. Строки должны быть в кавычках."
        )


def split_values(text):
    """Делит строку по запятым, не трогая запятые внутри кавычек."""
    parts, current, quote = [], "", None
    for ch in text:
        if quote:
            current += ch
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            current += ch
        elif ch == ",":
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())
    return parts


def parse_condition(text):
    """'age = 28' -> {'age': 28}. Для set можно несколько через запятую."""
    result = {}
    for part in split_values(text):
        if "=" not in part:
            raise ValueError(f"Некорректное условие: {part}")
        column, value = part.split("=", 1)
        result[column.strip()] = parse_value(value)
    return result


def _starts_with(parts, *words):
    """Проверяет, что первые слова команды совпадают с ожидаемыми."""
    if len(parts) < len(words):
        return False
    return all(part.lower() == word for part, word in zip(parts, words))


def _parse_where(text, usage):
    """Разбирает строку 'where <условие>' и возвращает словарь условия."""
    parts = text.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "where":
        raise ValueError(usage)
    return parse_condition(parts[1])


def _split_on_keyword(text, keyword):
    """Делит строку по слову-ключу вне кавычек. Возвращает пару или None."""
    marker = f" {keyword} "
    quote = None
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = None
        elif char in QUOTES:
            quote = char
        elif text[index:index + len(marker)].lower() == marker:
            return text[:index], text[index + len(marker):]
    return None


def parse_insert(line):
    """Разбирает 'insert into <таблица> values (...)'."""
    parts = line.strip().split(None, 3)
    if len(parts) != 4 or not _starts_with(parts, "insert", "into"):
        raise ValueError(INSERT_USAGE)

    rest = parts[3].strip()
    if not rest.lower().startswith("values"):
        raise ValueError(INSERT_USAGE)
    rest = rest[len("values"):].strip()
    if not (rest.startswith("(") and rest.endswith(")")):
        raise ValueError(INSERT_USAGE)

    values = [parse_value(value) for value in split_values(rest[1:-1])]
    return parts[2], values


def parse_select(line):
    """Разбирает 'select from <таблица> [where ...]'."""
    parts = line.strip().split(None, 3)
    if len(parts) < 3 or not _starts_with(parts, "select", "from"):
        raise ValueError(SELECT_USAGE)
    if len(parts) == 3:
        return parts[2], None
    return parts[2], _parse_where(parts[3], SELECT_USAGE)


def parse_update(line):
    """Разбирает 'update <таблица> set ... where ...'."""
    parts = line.strip().split(None, 2)
    if len(parts) != 3 or not _starts_with(parts, "update"):
        raise ValueError(UPDATE_USAGE)

    set_parts = parts[2].split(None, 1)
    if len(set_parts) != 2 or set_parts[0].lower() != "set":
        raise ValueError(UPDATE_USAGE)

    halves = _split_on_keyword(set_parts[1], "where")
    if halves is None:
        raise ValueError(UPDATE_USAGE)
    set_text, where_text = halves
    return parts[1], parse_condition(set_text), parse_condition(where_text)


def parse_delete(line):
    """Разбирает 'delete from <таблица> where ...'."""
    parts = line.strip().split(None, 3)
    if len(parts) != 4 or not _starts_with(parts, "delete", "from"):
        raise ValueError(DELETE_USAGE)
    return parts[2], _parse_where(parts[3], DELETE_USAGE)


def parse_info(line):
    """Разбирает 'info <таблица>' и возвращает имя таблицы."""
    parts = line.split()
    if len(parts) != 2 or not _starts_with(parts, "info"):
        raise ValueError(INFO_USAGE)
    return parts[1]