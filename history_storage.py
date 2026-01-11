import json
import os
from typing import List
from models import Task

HISTORY_FILE = "history.json"

def load_history() -> List[Task]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return [Task.from_dict(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []

def save_history(tasks: List[Task]):
    with open(HISTORY_FILE, "w") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=4)

def add_to_history(tasks: List[Task]):
    """Append tasks to history."""
    history = load_history()
    history.extend(tasks)
    save_history(history)
