import json
import os
from typing import List

CATEGORIES_FILE = "categories.json"

def load_categories() -> List[str]:
    if not os.path.exists(CATEGORIES_FILE):
        return []
    try:
        with open(CATEGORIES_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []

def save_categories(categories: List[str]):
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(categories, f, indent=4)
