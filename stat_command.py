"""
Statistics command for TDL - Display task completion statistics
"""
from history_storage import load_history
from stats_calculator import (
    calculate_daily_time,
    calculate_daily_task_count,
    find_longest_day,
    find_most_productive_day,
    find_longest_task,
    get_date_range
)
from ui_stats import render_statistics


def stat():
    """Display task completion statistics with 30-day chart and metrics."""
    # Load history
    history = load_history()
    
    if not history:
        print("[yellow]No task history found yet![/]")
        print("[dim]Complete some tasks to see statistics.[/dim]")
        return
    
    # Calculate statistics
    daily_time = calculate_daily_time(history, days=30)
    daily_count = calculate_daily_task_count(history, days=30)
    longest_day = find_longest_day(daily_time)
    most_productive_day = find_most_productive_day(daily_count)
    longest_task = find_longest_task(history)
    date_range = get_date_range(days=30)
    
    # Render visualization
    render_statistics(
        daily_time,
        daily_count,
        longest_day,
        most_productive_day,
        longest_task,
        date_range
    )


# Export for main.py integration
__all__ = ['stat']
