from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    category: Optional[List[str]] = None  # Now supports multiple categories
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None  # NEW: timestamp when task was completed
    priority: int = 0  # -1=unimportant, 0=normal, 1=important
    time_duration: Optional[int] = None  # Duration in seconds
    # Recurrence fields
    recurrent: bool = False
    recurrence_type: Optional[str] = None  # "daily", "weekdays", "weekly", "biweekly", "monthly", "custom"
    recurrence_days: Optional[List[int]] = None  # 0=Mon, 1=Tue, ..., 6=Sun (for custom days)
    recurrence_interval: int = 1  # Every N days/weeks/months

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "priority": self.priority,
            "time_duration": self.time_duration,
            "recurrent": self.recurrent,
            "recurrence_type": self.recurrence_type,
            "recurrence_days": self.recurrence_days,
            "recurrence_interval": self.recurrence_interval
        }

    @classmethod
    def from_dict(cls, data):
        # Handle migration from old 'important' field
        priority = data.get("priority", 0)
        if "important" in data and "priority" not in data:
            priority = 1 if data.get("important") else 0
        
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            category=data.get("category"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            completed=data.get("completed", False),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            priority=priority,
            time_duration=data.get("time_duration"),
            recurrent=data.get("recurrent", False),
            recurrence_type=data.get("recurrence_type"),
            recurrence_days=data.get("recurrence_days"),
            recurrence_interval=data.get("recurrence_interval", 1)
        )

    
    def get_duration_str(self) -> str:
        """Format duration as XXhXXmXXs"""
        if not self.time_duration:
            return ""
        
        hours = self.time_duration // 3600
        minutes = (self.time_duration % 3600) // 60
        seconds = self.time_duration % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0:
            parts.append(f"{seconds}s")
        
        return "".join(parts) if parts else "0s"

@dataclass
class Goal:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    completed: bool = False
    created_date: datetime = field(default_factory=datetime.now)
    completed_date: Optional[datetime] = None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_date": self.created_date.isoformat(),
            "completed_date": self.completed_date.isoformat() if self.completed_date else None
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            completed=data.get("completed", False),
            created_date=datetime.fromisoformat(data["created_date"]) if data.get("created_date") else datetime.now(),
            completed_date=datetime.fromisoformat(data["completed_date"]) if data.get("completed_date") else None
        )

@dataclass
class Template:
    """Template for quickly creating tasks with predefined properties."""
    alias: str  # The short name/alias for the template (e.g., "meeting", "workout")
    title: str = ""  # Default task title
    category: Optional[List[str]] = None  # Default categories
    due_date_offset: Optional[str] = None  # Relative due date like "today", "tomorrow", "+2d"
    time_duration: Optional[int] = None  # Duration in seconds
    priority: int = 0  # -1=unimportant, 0=normal, 1=important
    recurrent: bool = False
    recurrence_type: Optional[str] = None
    recurrence_days: Optional[List[int]] = None
    recurrence_interval: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self):
        return {
            "id": self.id,
            "alias": self.alias,
            "title": self.title,
            "category": self.category,
            "due_date_offset": self.due_date_offset,
            "time_duration": self.time_duration,
            "priority": self.priority,
            "recurrent": self.recurrent,
            "recurrence_type": self.recurrence_type,
            "recurrence_days": self.recurrence_days,
            "recurrence_interval": self.recurrence_interval
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            alias=data.get("alias"),
            title=data.get("title", ""),
            category=data.get("category"),
            due_date_offset=data.get("due_date_offset"),
            time_duration=data.get("time_duration"),
            priority=data.get("priority", 0),
            recurrent=data.get("recurrent", False),
            recurrence_type=data.get("recurrence_type"),
            recurrence_days=data.get("recurrence_days"),
            recurrence_interval=data.get("recurrence_interval", 1)
        )
