"""Константы проекта."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
PROMPT = ">>>Введите команду: "
DATA_COMMANDS = ("insert", "select", "update", "delete", "info")
VALID_TYPES = ("int", "str", "bool")
TYPE_MAP = {"int": int, "str": str, "bool": bool}
QUOTES = ('"', "'")
INSERT_USAGE = "Формат: insert into <таблица> values (<значения>)"
SELECT_USAGE = "Формат: select from <таблица> [where <столбец> = <значение>]"
UPDATE_USAGE = (
    "Формат: update <таблица> set <столбец> = <значение> "
    "where <столбец> = <значение>"
)
DELETE_USAGE = "Формат: delete from <таблица> where <столбец> = <значение>"
INFO_USAGE = "Формат: info <таблица>"