import re


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


# Разбор целых команд регулярками
INSERT_RE = re.compile(
    r"^insert\s+into\s+(\w+)\s+values\s*\((.*)\)\s*$", re.IGNORECASE
)
SELECT_RE = re.compile(
    r"^select\s+from\s+(\w+)(?:\s+where\s+(.+))?\s*$", re.IGNORECASE
)
UPDATE_RE = re.compile(
    r"^update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)$", re.IGNORECASE
)
DELETE_RE = re.compile(
    r"^delete\s+from\s+(\w+)\s+where\s+(.+)$", re.IGNORECASE
)
INFO_RE = re.compile(r"^info\s+(\w+)\s*$", re.IGNORECASE)


def parse_insert(line):
    m = INSERT_RE.match(line.strip())
    if not m:
        raise ValueError("Формат: insert into <таблица> values (<значения>)")
    table, values_text = m.groups()
    return table, [parse_value(v) for v in split_values(values_text)]


def parse_select(line):
    m = SELECT_RE.match(line.strip())
    if not m:
        raise ValueError("Формат: select from <таблица> [where <столбец> = <значение>]")
    table, where = m.groups()
    return table, parse_condition(where) if where else None


def parse_update(line):
    m = UPDATE_RE.match(line.strip())
    if not m:
        raise ValueError(
            "Формат: update <таблица> set <столбец> = <значение> "
            "where <столбец> = <значение>"
        )
    table, set_text, where_text = m.groups()
    return table, parse_condition(set_text), parse_condition(where_text)


def parse_delete(line):
    m = DELETE_RE.match(line.strip())
    if not m:
        raise ValueError("Формат: delete from <таблица> where <столбец> = <значение>")
    table, where_text = m.groups()
    return table, parse_condition(where_text)


def parse_info(line):
    m = INFO_RE.match(line.strip())
    if not m:
        raise ValueError("Формат: info <таблица>")
    return m.group(1)