import json
import uuid
from datetime import datetime
from models import Task

tasks = [
    Task(
        id=str(uuid.uuid4()),
        title="Test Task 1",
        completed=True,
        completed_at=datetime(2026, 1, 7, 10, 0, 0),
        time_duration=1200 # 20 mins
    ),
    Task(
        id=str(uuid.uuid4()),
        title="Test Task 2",
        completed=True,
        completed_at=datetime(2026, 1, 8, 14, 0, 0),
        time_duration=600 # 10 mins
    ),
    Task(
        id=str(uuid.uuid4()),
        title="Test Task 3",
        completed=True,
        completed_at=datetime(2026, 1, 9, 16, 0, 0),
        time_duration=1800 # 30 mins
    )
]

with open("history.json", "w") as f:
    json.dump([t.to_dict() for t in tasks], f, indent=4, default=str)

print("Injected history.json")
