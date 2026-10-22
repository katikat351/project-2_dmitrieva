"""Константы проекта."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
PROMPT = ">>>Введите команду: "
DATA_COMMANDS = ("insert", "select", "update", "delete", "info")
VALID_TYPES = ("int", "str", "bool")
TYPE_MAP = {"int": int, "str": str, "bool": bool}
QUOTES = ('"', "'")