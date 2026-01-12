from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.align import Align
from datetime import datetime
from models import Task
from typing import List, Dict, Tuple, Optional
import calendar

from config_storage import get_theme

console = Console(force_terminal=True)

THEMES = {
    "rainbow": {
        "primary": "#00ffff",  # cyan
        "secondary": "#ff00ff", # magenta
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "header_colors": ["cyan", "red", "yellow", "green", "blue", "magenta"],
        "rainbow_colors": ["red", "#ff8c00", "yellow", "green", "blue", "#800080", "#ee82ee"] # red, orange, yellow, green, blue, purple, violet
    },
    "dark": {
        "primary": "#ffffff",  # bright_white
        "secondary": "#666666", # bright_black (gray)
        "success": "green",
        "warning": "yellow",
        "error": "#ff0000", # bright_red
        "header_colors": ["white"] * 6,
        "rainbow_colors": ["white", "#666666", "white", "#666666", "white", "#666666", "white"]
    },
    "neon": {
        "primary": "#00ffff",  # bright_cyan
        "secondary": "#ff00ff", # bright_magenta
        "success": "#00ff00", # bright_green
        "warning": "#ffff00", # bright_yellow
        "error": "#ff0000",   # bright_red
        "header_colors": ["#00ffff", "#ff00ff", "#00ff00", "#ffff00", "#0000ff", "#ff0000"],
        "rainbow_colors": ["#ff0000", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ff00ff", "#ff69b4"]
    },
    "pastel": {
        "primary": "#e0ffff",  # light_cyan
        "secondary": "#dda0dd", # plum (pastel purple)
        "success": "#98fb98", # pale_green
        "warning": "#ffffe0", # light_yellow
        "error": "#ffb6c1",   # light_pink
        "header_colors": ["#e0ffff", "#ffb6c1", "#ffffe0", "#98fb98", "#dda0dd", "#ffb6c1"],
        "rainbow_colors": ["#ffb6c1", "#ffa07a", "#ffffe0", "#98fb98", "#add8e6", "#dda0dd", "#fff0f5"]
    }
}

def get_current_theme():
    """Get the current theme settings."""
    theme_name = get_theme().lower()
    return THEMES.get(theme_name, THEMES["rainbow"])


def render_statistics(
    daily_time: Dict[str, int],
    daily_count: Dict[str, int],
    longest_day: Optional[Tuple[str, int]],
    most_productive_day: Optional[Tuple[str, int]],
    longest_task: Optional[Tuple[Task, int]],
    date_range: List[str]
):
    """
    Render task statistics with 30-day bar chart and key metrics.
    
    Args:
        daily_time: Dict mapping dates to total seconds worked
        daily_count: Dict mapping dates to number of tasks completed
        longest_day: Tuple of (date, total_seconds) for day with most time
        most_productive_day: Tuple of (date, task_count) for day with most tasks
        longest_task: Tuple of (task, duration) for longest task
        date_range: List of date strings for last 30 days
    """
    from stats_calculator import format_duration
    
    theme = get_current_theme()
    rainbow_colors = theme["rainbow_colors"]
    
    # console.clear() # Removed to prevent clearing command history
    
    # Header
    header = Text()
    header.append("📊 TASK STATISTICS", style=f"bold {theme['primary']}")
    
    console.print(Panel(
        header,
        border_style=theme["primary"],
        padding=(0, 2)
    ))
    console.print()
    
    # === BAR CHART ===
    # Calculate max value for scaling in seconds
    max_seconds = max(daily_time.values()) if daily_time else 1
    
    # Calculate max minutes for display
    max_minutes = max_seconds / 60
    
    # Round up max value for nice Y-axis
    # If max is 45m, round to 50m. If 125m, round to 150m.
    if max_minutes <= 10:
        y_max = 10
    elif max_minutes <= 60:
        y_max = ((int(max_minutes) // 10) + 1) * 10
    elif max_minutes <= 180:
        y_max = ((int(max_minutes) // 30) + 1) * 30
    else:
        y_max = ((int(max_minutes) // 60) + 1) * 60
        
    y_max_seconds = y_max * 60
    
    # Create bar chart (30 days)
    chart_lines = []
    bar_height = 10  # Height of chart in lines
    
    # Title
    chart_lines.append(Text("Last 30 Days - Time Spent", style="bold white", justify="center"))
    chart_lines.append(Text())  # Empty line
    
    # Calculate bar heights (0-bar_height) relative to y_max_seconds
    bar_heights = []
    for date_str in date_range:
        time_value = daily_time.get(date_str, 0)
        if y_max_seconds > 0:
            # Calculate height proportional to y_max
            # If time_value >= y_max_seconds, it fills the chart (shouldn't happen due to rounding up)
            height = int((time_value / y_max_seconds) * bar_height)
            # Ensure nice visualization for small non-zero values
            if time_value > 0 and height == 0:
                height = 1
            if height > bar_height:
                height = bar_height
        else:
            height = 0
        bar_heights.append(height)
    
    # Width of Y-axis label area (e.g., "120m ┤")
    # Max width needs to account for number + "m"
    max_label_len = len(str(y_max)) + 1
    y_label_width = max_label_len + 1  # +1 for spacing
    
    # Generate chart from top to bottom
    for level in range(bar_height, 0, -1):
        line = Text()
        
        # Y-axis Label
        # Show label at top, middle, and occasionally others
        minutes_at_level = int((level / bar_height) * y_max)
        
        should_label = False
        if level == bar_height: # Top
            should_label = True
        elif level == bar_height // 2: # Middle
            should_label = True
        elif level == 1 and y_max > 0: # Bottom non-zero
            should_label = False # Skip bottom to avoid clutter with x-axis
            
        if should_label:
            label = f"{minutes_at_level}m"
            line.append(f"{label:>{y_label_width}} ┤ ", style="dim")
        else:
            line.append(f"{'':>{y_label_width}} │ ", style="dim")
            
        # Draw Bars
        for i, height in enumerate(bar_heights):
            color = rainbow_colors[i % len(rainbow_colors)]
            if height >= level:
                line.append("█", style=color)
            else:
                line.append(" ", style="dim")
        chart_lines.append(line)
    
    # Axis line
    # Indent for Y-axis: label width + " ┤ " is space-char-space
    # We want " └─" to align. " ┤ " has length 3.
    # Previous line ends with " ┤ ".
    # We need padding equal to y_label_width + 1 (for the space before ┤)
    axis_indent = " " * (y_label_width) + " └─"
    chart_lines.append(Text(f"{axis_indent}" + "─" * 30, style="dim"))
    
    # Date labels (show every 5 days)
    # Alignment: y_label_width + " ┤ " (3 chars)
    date_labels = Text(" " * (y_label_width + 3)) # Indent to align with bars
    for i, date_str in enumerate(date_range):
        if i % 5 == 0:
            day = date_str.split("-")[2]  # Get day
            date_labels.append(day, style="dim")
        else:
            date_labels.append(" ", style="dim")
    chart_lines.append(date_labels)
    
    # Combine all chart lines
    chart_content = Text()
    for line in chart_lines:
        chart_content.append(line)
        chart_content.append("\n")
    
    # === STATISTICS PANEL ===
    stats = Text()
    
    # Day with longest time
    if longest_day:
        date_str, total_seconds = longest_day
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%b %d, %Y")
        stats.append("🏆 ", style="yellow")
        stats.append("Most Time in One Day\n", style="bold yellow")
        stats.append(f"   {format_duration(total_seconds)}", style=f"bold {rainbow_colors[0]}")
        stats.append(f" on {formatted_date}\n\n", style="white")
    else:
        stats.append("🏆 ", style="yellow")
        stats.append("Most Time in One Day\n", style="bold yellow")
        stats.append("   No data yet\n\n", style="dim")
    
    # Day with most tasks
    if most_productive_day:
        date_str, task_count = most_productive_day
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%b %d, %Y")
        stats.append("⚡ ", style="cyan")
        stats.append("Most Productive Day\n", style="bold cyan")
        stats.append(f"   {task_count} tasks", style=f"bold {rainbow_colors[2]}")
        stats.append(f" on {formatted_date}\n\n", style="white")
    else:
        stats.append("⚡ ", style="cyan")
        stats.append("Most Productive Day\n", style="bold cyan")
        stats.append("   No data yet\n\n", style="dim")
    
    # Longest task
    if longest_task:
        task, duration = longest_task
        if task.completed_at:
            formatted_date = task.completed_at.strftime("%b %d, %Y")
        else:
            formatted_date = "Unknown date"
        task_title = task.title[:25] + "..." if len(task.title) > 25 else task.title
        stats.append("🎯 ", style="green")
        stats.append("Longest Task\n", style="bold green")
        stats.append(f"   {task_title}\n", style="white")
        stats.append(f"   {format_duration(duration)}", style=f"bold {rainbow_colors[4]}")
        stats.append(f" on {formatted_date}\n", style="white")
    else:
        stats.append("🎯 ", style="green")
        stats.append("Longest Task\n", style="bold green")
        stats.append("   No data yet\n", style="dim")
    
    # Create columns layout
    from rich.columns import Columns
    
    chart_panel = Panel(
        Align.center(chart_content),
        border_style=rainbow_colors[3],
        padding=(1, 2),
        title="[bold white]Activity Chart[/]"
    )
    
    stats_panel = Panel(
        stats,
        border_style=rainbow_colors[5],
        padding=(1, 2),
        title="[bold white]Key Metrics[/]"
    )
    
    columns = Columns([chart_panel, stats_panel], equal=False, expand=True)
    console.print(columns)
    console.print()
