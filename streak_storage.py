
import json
import os
from datetime import datetime, timedelta

STREAK_FILE = "streak.json"

def load_streak():
    """Returns (current_streak: int, last_active_date: str)"""
    if not os.path.exists(STREAK_FILE):
        return 0, None
    try:
        with open(STREAK_FILE, "r") as f:
            data = json.load(f)
            return data.get("streak", 0), data.get("last_date")
    except Exception:
        return 0, None

def save_streak(streak, date_str):
    with open(STREAK_FILE, "w") as f:
        json.dump({"streak": streak, "last_date": date_str}, f)

def update_streak():
    """Updates steak based on today's activity. Called when a task is completed."""
    today = datetime.now().date()
    today_str = today.isoformat()
    
    streak, last_date_str = load_streak()
    
    if last_date_str == today_str:
        # Already active today, do nothing
        return streak, True # (streak, is_active_today)
    
    if last_date_str:
        last_date = datetime.fromisoformat(last_date_str).date()
        if last_date == today - timedelta(days=1):
            # Consecutive day
            streak += 1
        else:
            # Streak broken (or first time)
            streak = 1
    else:
        # First time ever
        streak = 1
        
    save_streak(streak, today_str)
    return streak, True

def get_streak_status():
    """Returns (streak, is_active_today) without updating."""
    today_str = datetime.now().date().isoformat()
    streak, last_date_str = load_streak()
    
    is_active = (last_date_str == today_str)
    
    # Check if streak is broken (yesterday was missed)
    if last_date_str and not is_active:
        last_date = datetime.fromisoformat(last_date_str).date()
        if last_date < datetime.now().date() - timedelta(days=1):
            # Streak is broken, effectively 0 for display purpose?
            # Or show stored streak but gray? Usually show 0 if broken.
            # But maybe user wants to see "Streak lost"?
            # Standard logic: if broken, effective streak is 0 until restored (start over).
            return 0, False
            
    return streak, is_active

def get_streak_display():
    """Returns a rich formatted string for streak display."""
    streak, is_active = get_streak_status()
    
    if is_active:
        # Lit fire
        if streak >= 10:
            return f"[bold red]🔥 {streak}[/]" # Super hot
        elif streak >= 3:
            return f"[bold orange1]🔥 {streak}[/]" # Heating up
        else:
            return f"[yellow]🔥 {streak}[/]" # Just started
    else:
        # Extinguished fire (gray)
        # If streak is 0, just show gray fire with 0 or empty?
        # User said "gray fire... lit up when finish 1 task".
        return f"[dim white]🔥 {streak}[/]"
