import json
from pathlib import Path


def load_metadata(filepath):
    """Загружает метаданные из JSON-файла. Если файла нет — возвращает {}."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


DATA_DIR = Path("data")


def load_table_data(table_name):
    """Загружает записи таблицы из data/<table_name>.json."""
    filepath = DATA_DIR / f"{table_name}.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в data/<table_name>.json."""
    DATA_DIR.mkdir(exist_ok=True)
    filepath = DATA_DIR / f"{table_name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_cacher():
    """Возвращает функцию cache_result(key, value_func) с кэшем в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    def clear():
        cache.clear()

    cache_result.clear = clear
    return cache_result