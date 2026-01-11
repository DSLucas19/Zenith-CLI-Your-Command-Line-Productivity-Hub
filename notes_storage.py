import json
import os
from datetime import datetime
from typing import List, Optional

NOTES_FILE = "notes.json"

class Note:
    def __init__(self, content: str, id: int = 0, created_at: Optional[datetime] = None):
        self.id = id
        self.content = content
        self.created_at = created_at if created_at else datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"])
        )

def load_notes() -> List[Note]:
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r") as f:
            data = json.load(f)
            return [Note.from_dict(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []

def save_notes(notes: List[Note]):
    # Re-index ids to ensure consistency
    for i, note in enumerate(notes, 1):
        note.id = i
        
    try:
        with open(NOTES_FILE, "w") as f:
            json.dump([n.to_dict() for n in notes], f, indent=4)
    except IOError:
        pass
