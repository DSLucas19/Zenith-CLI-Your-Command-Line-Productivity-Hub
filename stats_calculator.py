"""
Statistics Calculator for TDL
Calculates task completion statistics from history data
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from models import Task


def calculate_daily_time(history: List[Task], days: int = 30) -> Dict[str, int]:
    """
    Calculate total time spent per day for the last N days.
    
    Args:
        history: List of completed tasks
        days: Number of days to analyze (default 30)
    
    Returns:
        Dict mapping date string (YYYY-MM-DD) to total seconds
    """
    daily_time = defaultdict(int)
    today = datetime.now().date()
    
    for task in history:
        if not task.completed or not task.completed_at:
            continue
        
        task_date = task.completed_at.date()
        
        # Only include tasks from last N days
        days_ago = (today - task_date).days
        if 0 <= days_ago < days:
            date_str = task_date.isoformat()
            # Use time_duration as proxy for time spent
            if task.time_duration:
                daily_time[date_str] += task.time_duration
    
    return dict(daily_time)


def calculate_daily_task_count(history: List[Task], days: int = 30) -> Dict[str, int]:
    """
    Calculate number of tasks completed per day for the last N days.
    
    Args:
        history: List of completed tasks
        days: Number of days to analyze (default 30)
    
    Returns:
        Dict mapping date string (YYYY-MM-DD) to task count
    """
    daily_count = defaultdict(int)
    today = datetime.now().date()
    
    for task in history:
        if not task.completed or not task.completed_at:
            continue
        
        task_date = task.completed_at.date()
        
        # Only include tasks from last N days
        days_ago = (today - task_date).days
        if 0 <= days_ago < days:
            date_str = task_date.isoformat()
            daily_count[date_str] += 1
    
    return dict(daily_count)


def find_longest_day(daily_time: Dict[str, int]) -> Optional[Tuple[str, int]]:
    """
    Find the day with the most time spent on tasks.
    
    Args:
        daily_time: Dict from calculate_daily_time()
    
    Returns:
        Tuple of (date_string, total_seconds) or None if no data
    """
    if not daily_time:
        return None
    
    max_date = max(daily_time.items(), key=lambda x: x[1])
    return max_date


def find_most_productive_day(daily_count: Dict[str, int]) -> Optional[Tuple[str, int]]:
    """
    Find the day with the most tasks completed.
    
    Args:
        daily_count: Dict from calculate_daily_task_count()
    
    Returns:
        Tuple of (date_string, task_count) or None if no data
    """
    if not daily_count:
        return None
    
    max_date = max(daily_count.items(), key=lambda x: x[1])
    return max_date


def find_longest_task(history: List[Task]) -> Optional[Tuple[Task, int]]:
    """
    Find the task that took the longest time to complete.
    
    Args:
        history: List of completed tasks
    
    Returns:
        Tuple of (task, duration_seconds) or None if no tasks with duration
    """
    tasks_with_duration = [
        (task, task.time_duration)
        for task in history
        if task.completed and task.time_duration and task.time_duration > 0
    ]
    
    if not tasks_with_duration:
        return None
    
    longest = max(tasks_with_duration, key=lambda x: x[1])
    return longest


def format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration (e.g., '2h 30m')."""
    if seconds < 60:
        return f"{seconds}s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "0m"


def get_date_range(days: int = 30) -> List[str]:
    """
    Get list of date strings for the last N days.
    
    Args:
        days: Number of days (default 30)
    
    Returns:
        List of date strings in YYYY-MM-DD format, oldest to newest
    """
    today = datetime.now().date()
    date_range = []
    
    for i in range(days - 1, -1, -1):  # Count backwards
        date = today - timedelta(days=i)
        date_range.append(date.isoformat())
    
    return date_range
