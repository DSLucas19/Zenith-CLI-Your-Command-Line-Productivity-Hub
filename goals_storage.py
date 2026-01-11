import json
import os
from typing import List
from models import Goal

GOALS_FILE = "goals.json"

def load_goals() -> List[Goal]:
    if not os.path.exists(GOALS_FILE):
        return []
    
    try:
        with open(GOALS_FILE, 'r') as f:
            data = json.load(f)
            return [Goal.from_dict(item) for item in data]
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_goals(goals: List[Goal]):
    with open(GOALS_FILE, 'w') as f:
        json.dump([g.to_dict() for g in goals], f, indent=4)
