import json
import os
from typing import List
from models import Task

DATA_FILE = "tasks.json"

def load_tasks() -> List[Task]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return [Task.from_dict(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []

def save_tasks(tasks: List[Task]):
    with open(DATA_FILE, "w") as f:
        json.dump([t.to_dict() for t in tasks], f, indent=4)
