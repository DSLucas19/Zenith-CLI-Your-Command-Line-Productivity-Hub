from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.align import Align
from rich.columns import Columns
from datetime import datetime
from models import Task
from typing import List
import calendar

from config_storage import get_theme, get_category_colors, update_category_color
from categories_storage import load_categories

def get_current_theme():
    # Helper to get theme dict
    import config_storage
    theme_name = config_storage.get_theme()
    return THEMES.get(theme_name, THEMES["rainbow"])

AVAILABLE_COLORS = [
    "bright_cyan", "bright_magenta", "bright_green", "bright_yellow", "bright_blue", "bright_red",
    "cyan", "magenta", "green", "yellow", "blue", "red",
    "orange1", "violet", "purple", "turquoise2", "chartreuse1", "gold1", "sky_blue1", "plum1",
    "spring_green1", "medium_orchid1", "deep_sky_blue1"
]

def get_category_color(category_name: str) -> str:
    """Get consistent, persistent color for a category."""
    if not category_name:
        return "white"
        
    colors = get_category_colors()
    if category_name in colors:
        return colors[category_name]
    
    # Assign new color (try to be unique)
    used_colors = set(colors.values())
    
    # Find first unused color
    for color in AVAILABLE_COLORS:
        if color not in used_colors:
            update_category_color(category_name, color)
            return color
            
    # If all used, cycle using hash
    import hashlib
    hash_val = int(hashlib.md5(category_name.encode()).hexdigest(), 16)
    idx = hash_val % len(AVAILABLE_COLORS)
    color = AVAILABLE_COLORS[idx]
    
    update_category_color(category_name, color)
    return color

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
        "error": "#ff69b4",   # light_red/pinkish
        "header_colors": ["#e0ffff", "#dda0dd", "#98fb98", "#ffffe0", "#add8e6", "#ffb5c5"],
        "rainbow_colors": ["#ffb5c5", "#d2b48c", "#ffffe0", "#98fb98", "#e0ffff", "#add8e6", "#dda0dd"]
    }
}

def get_current_theme():
    theme_name = get_theme().lower()
    return THEMES.get(theme_name, THEMES["rainbow"])

def get_rainbow_style(index: int) -> str:
    theme = get_current_theme()
    colors = theme["rainbow_colors"]
    return colors[index % len(colors)]

def render_dashboard(tasks: List[Task]):
    """Render dashboard grouped by time relative to current date"""
    
    from collections import defaultdict
    from datetime import timedelta
    from streak_storage import get_streak_display
    from config_storage import get_show_streak
    
    # Show Streak at top right (compact)
    if get_show_streak():
        console.print(Align.right(get_streak_display() + " "))
    
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)
    
    # Group tasks by time bucket
    grouped = {
        "non-assigned": [],
        "Today": [],
        "Tomorrow": [],
        "This week": [],
        "This month": [],
        "Future": []
    }
    

    
    if not tasks:
        console.print(Align.center("[dim]No tasks to display.[/dim]"))
        console.print()
        return

    for task in tasks:
        if not task.due_date:
            grouped["non-assigned"].append(task)
        else:
            task_date = task.due_date.date()
            if task_date == today:
                grouped["Today"].append(task)
            elif task_date == tomorrow:
                grouped["Tomorrow"].append(task)
            elif task_date <= week_end:
                grouped["This week"].append(task)
            elif task_date <= month_end:
                grouped["This month"].append(task)
            else:
                grouped["Future"].append(task)
    
    # Sort each group by category (alphabetically), then priority, then due date
    for group in grouped.values():
        def get_sort_key(task):
            # Get primary category for sorting (first one if multiple, or empty string if none)
            if task.category:
                if isinstance(task.category, list) and task.category:
                    primary_category = task.category[0].lower()
                elif isinstance(task.category, str):
                    primary_category = task.category.lower()
                else:
                    primary_category = ""
            else:
                primary_category = ""
            
            return (
                primary_category,  # Group by category alphabetically
                -task.priority,     # Then by priority (important first)
                task.due_date if task.due_date else datetime.max,  # Then by due date
                task.title.lower()  # Finally alphabetically by title
            )
        
        group.sort(key=get_sort_key)
    
    # Define display order with rainbow colors for headers
    theme = get_current_theme()
    group_order = ["non-assigned", "Today", "Tomorrow", "This week", "This month", "Future"]
    group_colors = theme["header_colors"]
    
    # Count category frequency across all tasks
    from collections import Counter
    category_counter = Counter()
    for task in tasks:
        if task.category:
            if isinstance(task.category, list):
                for cat in task.category:
                    category_counter[cat.lower()] += 1
            else:
                category_counter[task.category.lower()] += 1
    
    # Create consistent color mapping for categories
    # Remove local helper, use global get_category_color

    
    # Track global task ID
    task_id = 1
    
    # Render each time group
    for idx, group_name in enumerate(group_order):
        group_tasks = grouped[group_name]
        
        # Skip empty groups
        if not group_tasks:
            continue
        
        # Print group header with rainbow color
        group_color = group_colors[idx % len(group_colors)]
        console.print(f"\n[bold {group_color}]{group_name}[/bold {group_color}]")
        
        # Print each task in the group
        for task in group_tasks:
            # Build task line: ID [ ] due_date #category task_title duration
            
            # ID
            theme = get_current_theme()
            id_str = f"[bold {theme['primary']}]{task_id}[/bold {theme['primary']}]"
            
            # Checkbox
            if task.title.startswith("📅"):
                check = "   "
            elif task.completed:
                check = "[dim][✓][/dim]"
            else:
                check = "[ ]"
            
            # Due date (if exists)
            if task.due_date:
                due_str = task.due_date.strftime('%a %b %d')
            else:
                due_str = ""
            
            # Category tags (support multiple) with consistent rainbow colors
            tags = ""
            if task.category:
                if isinstance(task.category, list):
                    # Sort categories by frequency (most common first), then alphabetically
                    sorted_cats = sorted(
                        task.category,
                        key=lambda cat: (-category_counter[cat.lower()], cat.lower())
                    )
                    tag_parts = []
                    for cat in sorted_cats:
                        cat_color = get_category_color(cat)
                        tag_parts.append(f"#[bold {cat_color}]{cat}[/bold {cat_color}]")
                    tags = " ".join(tag_parts)
                else:
                    # Backward compatibility with old single-category tasks
                    cat_color = get_category_color(task.category)
                    tags = f"#[bold {cat_color}]{task.category}[/bold {cat_color}]"
            
            # Task title
            title = task.title
            
            # Duration (if exists)
            duration = task.get_duration_str() or ""
            
            # Recurrence icon
            recurrence_icon = f"[{theme['secondary']}]🔁[/{theme['secondary']}]" if getattr(task, 'recurrent', False) else ""
            
            # Description icon
            description_icon = f"[{theme['warning']}]📝[/{theme['warning']}]" if getattr(task, 'description', None) else ""

            
            # Apply styling based on priority and completion
            if task.completed:
                # Completed tasks: dimmed and strikethrough
                line_parts = [
                    id_str,
                    check,
                    f"[dim strike]{due_str}[/dim strike]" if due_str else "",
                    f"[dim strike]{tags}[/dim strike]" if tags else "",
                    f"[dim strike]{title}[/dim strike]",
                    f"[dim strike]{duration}[/dim strike]" if duration else "",
                    recurrence_icon,
                    description_icon
                ]
            elif task.priority == 1:
                # Important tasks: red
                line_parts = [
                    id_str,
                    check,
                    f"[red]{due_str}[/red]" if due_str else "",
                    tags,
                    f"[bold red]{title}[/bold red]",
                    f"[red]{duration}[/red]" if duration else "",
                    recurrence_icon,
                    description_icon
                ]
            elif task.priority == -1:
                # Unimportant tasks: dimmed
                line_parts = [
                    id_str,
                    check,
                    f"[dim]{due_str}[/dim]" if due_str else "",
                    f"[dim]{tags}[/dim]" if tags else "",
                    f"[dim]{title}[/dim]",
                    f"[dim]{duration}[/dim]" if duration else "",
                    recurrence_icon,
                    description_icon
                ]
            else:
                # Normal tasks: white
                line_parts = [
                    id_str,
                    check,
                    due_str,
                    tags,
                    title,
                    duration,
                    recurrence_icon,
                    description_icon
                ]

            
            # Filter out empty parts and join
            line = "  ".join(part for part in line_parts if part)
            console.print(line)
            
            task_id += 1
    
    console.print()  # Final newline

def render_task_list(tasks: List[Task], global_id_map: dict = None):
    """Render a simple list of tasks without grouping.
    
    Args:
        tasks: List of tasks to render
        global_id_map: Optional dict mapping task.id -> display_id for consistent IDs across views
    """
    from collections import Counter
    
    # Count category frequency across all tasks for consistent coloring
    category_counter = Counter()
    for task in tasks:
        if task.category:
            if isinstance(task.category, list):
                for cat in task.category:
                    category_counter[cat.lower()] += 1
            else:
                category_counter[task.category.lower()] += 1
    

    
    # Sort by priority then due date
    sorted_tasks = sorted(tasks, key=lambda x: (
        -x.priority,
        x.due_date if x.due_date else datetime.max,
        x.title.lower()
    ))
    
    # Render each task
    local_id = 1
    for task in sorted_tasks:
        # Use global ID if provided, otherwise use local numbering
        if global_id_map and task.id in global_id_map:
            display_id = global_id_map[task.id]
        else:
            display_id = local_id
        
        # ID
        theme = get_current_theme()
        id_str = f"[bold {theme['primary']}]{display_id}[/bold {theme['primary']}]"
        
        # Checkbox
        if task.title.startswith("📅"):
            check = "   "
        elif task.completed:
            check = "[dim][✓][/dim]"
        else:
            check = "[ ]"
        
        # Due date
        due_str = task.due_date.strftime('%a %b %d') if task.due_date else ""
        
        # Category tags with consistent colors
        tags = ""
        if task.category:
            if isinstance(task.category, list):
                sorted_cats = sorted(
                    task.category,
                    key=lambda cat: (-category_counter[cat.lower()], cat.lower())
                )
                tag_parts = []
                for cat in sorted_cats:
                    cat_color = get_category_color(cat)
                    tag_parts.append(f"#[bold {cat_color}]{cat}[/bold {cat_color}]")
                tags = " ".join(tag_parts)
            else:
                cat_color = get_category_color(task.category)
                tags = f"#[bold {cat_color}]{task.category}[/bold {cat_color}]"
        
        # Task title
        title = task.title
        
        # Duration
        duration = task.get_duration_str() or ""
        
        # Recurrence icon
        recurrence_icon = f"[{theme['secondary']}]🔁[/{theme['secondary']}]" if getattr(task, 'recurrent', False) else ""
        
        # Description icon
        description_icon = f"[{theme['warning']}]📝[/{theme['warning']}]" if getattr(task, 'description', None) else ""
        
        # Apply styling based on priority and completion
        if task.completed:
            line_parts = [
                id_str, check,
                f"[dim strike]{due_str}[/dim strike]" if due_str else "",
                f"[dim strike]{tags}[/dim strike]" if tags else "",
                f"[dim strike]{title}[/dim strike]",
                f"[dim strike]{duration}[/dim strike]" if duration else "",
                recurrence_icon,
                description_icon
            ]
        elif task.priority == 1:
            line_parts = [
                id_str, check,
                f"[red]{due_str}[/red]" if due_str else "",
                tags,
                f"[bold red]{title}[/bold red]",
                f"[red]{duration}[/red]" if duration else "",
                recurrence_icon,
                description_icon
            ]
        elif task.priority == -1:
            line_parts = [
                id_str, check,
                f"[dim]{due_str}[/dim]" if due_str else "",
                f"[dim]{tags}[/dim]" if tags else "",
                f"[dim]{title}[/dim]",
                f"[dim]{duration}[/dim]" if duration else "",
                recurrence_icon,
                description_icon
            ]
        else:
            line_parts = [
                id_str, check, due_str, tags, title, duration, recurrence_icon, description_icon
            ]
        
        line = "  ".join(part for part in line_parts if part)
        console.print(line)
        local_id += 1
    
    console.print()

def render_calendar(tasks: List[Task], year: int = None, month: int = None):
    """Render a monthly calendar view with rainbow styling."""
    import os
    
    # Use current date if not specified
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    month_cal = calendar.monthcalendar(year, month)
    month_name = datetime(year, month, 1).strftime('%B %Y')
    
    # Rainbow colors for day headers
    theme = get_current_theme()
    rainbow_colors = theme["rainbow_colors"]
    
    # Create table with colorful styling
    table = Table(
        title=f"[bold white]📅 {month_name}[/bold white]",
        box=box.DOUBLE_EDGE,
        expand=True,
        border_style=theme["primary"],
        title_style="bold white"
    )
    
    # Add columns with rainbow colors for each day
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, day in enumerate(days):
        color = rainbow_colors[i % len(rainbow_colors)]
        table.add_column(day, justify="center", header_style=f"bold {color}", width=12)

    # Map dates to tasks
    tasks_by_date = {}
    for task in tasks:
        if task.due_date and not task.completed:
            d = task.due_date.date()
            if d not in tasks_by_date:
                tasks_by_date[d] = []
            tasks_by_date[d].append(task)
            
    # Category color helper
    def get_task_color(task):
        if not task.category:
             return "white"
             
        cat_to_use = task.category[0] if isinstance(task.category, list) and task.category else task.category
        if isinstance(cat_to_use, list):
            cat_to_use = cat_to_use[0]
            
        if not cat_to_use:
            return "white"
            
        return get_category_color(cat_to_use)

    for week in month_cal:
        row_cells = []
        for day_idx, day in enumerate(week):
            if day == 0:
                row_cells.append("")
                continue
                
            cell_text = Text()
            # Highlight today
            try:
                current_date = datetime(year, month, day).date()
                if current_date == now.date():
                    cell_text.append(f"{day}\n", style="bold yellow underline")
                else:
                    cell_text.append(f"{day}\n", style="bold white")
            except ValueError:
                cell_text.append(f"{day}\n", style="bold white")
                current_date = None
            
            # Check for tasks on this day
            if current_date and current_date in tasks_by_date:
                for idx, task in enumerate(tasks_by_date[current_date]):
                    color = get_task_color(task)
                    
                    # Add description indicator
                    has_desc = getattr(task, 'description', None) is not None
                    desc_mark = "📝" if has_desc else ""
                    
                    # Truncate title to fit
                    limit = 8 if has_desc else 10
                    title_trunc = task.title[:limit] + ".." if len(task.title) > limit else task.title
                    
                    cell_text.append(f"• {title_trunc}{desc_mark}\n", style=color)
            
            row_cells.append(cell_text)
        
        table.add_row(*row_cells, end_section=True)

    console.print(table)
    console.print("[dim]← / → navigate months  |  Type day (1-31) to view events  |  q to exit[/dim]", justify="center")
    
    return year, month

def render_calendar_interactive(tasks: List[Task], global_id_map: dict = None):
    """Interactive calendar with arrow key navigation and day selection."""
    import msvcrt
    import os
    import calendar as cal_module
    
    now = datetime.now()
    year = now.year
    month = now.month
    digit_buffer = ""
    
    # Sort tasks by date to ensure IDs match other views
    tasks.sort(key=lambda t: t.due_date if t.due_date else datetime.max)
    
    def get_task_color(task):
        theme = get_current_theme()
        if not task.category:
             return "white"
             
        cat_to_use = task.category[0] if isinstance(task.category, list) and task.category else task.category
        if isinstance(cat_to_use, list):
            cat_to_use = cat_to_use[0]
            
        if not cat_to_use:
            return "white"
            
        return get_category_color(cat_to_use)
    
    def show_day_events(day: int):
        """Display events for a specific day."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        try:
            target_date = datetime(year, month, day).date()
        except ValueError:
            console.print(f"[red]Invalid day: {day}[/]")
            console.print("[dim]Press any key to continue...[/]")
            msvcrt.getch()
            return
        
        # Find tasks for this day
        day_tasks = [t for t in tasks if t.due_date and t.due_date.date() == target_date and not t.completed]
        
        date_str = target_date.strftime('%A, %B %d, %Y')
        theme = get_current_theme()
        console.print(f"\n[bold {theme['primary']}]📅 {date_str}[/bold {theme['primary']}]\n")
        
        if not day_tasks:
            console.print("[dim]No events scheduled for this day.[/dim]")
        else:
            for i, task in enumerate(day_tasks):
                color = get_task_color(task)
                time_str = task.due_date.strftime('%H:%M') if task.due_date.hour or task.due_date.minute else ""
                
                # Check for description
                has_desc = getattr(task, 'description', None) is not None
                desc_icon = " 📝" if has_desc else ""
                
                # Calculate ID
                if global_id_map and task.id in global_id_map:
                    display_id = global_id_map[task.id]
                else:
                    # Fallback to local index if not found
                    display_id = f"#{tasks.index(task) + 1}"
                
                if time_str:
                    console.print(f"  [dim]{display_id}[/dim] [{color}]• {time_str}[/{color}] [{color}]{task.title}{desc_icon}[/{color}]")
                else:
                    console.print(f"  [dim]{display_id}[/dim] [{color}]•[/{color}] [{color}]{task.title}{desc_icon}[/{color}]")
                    
                if task.category:
                    if isinstance(task.category, list):
                        cat_str = " ".join([f"#{c}" for c in task.category])
                    else:
                        cat_str = f"#{task.category}"
                    console.print(f"    [dim]{cat_str}[/dim]")
                
                # Show description under the event
                if has_desc:
                    console.print(f"    [italic white]{task.description}[/italic white]")
                    console.print() # Extra spacing
        
        console.print("\n[dim]Press any key to return to calendar...[/dim]")
        msvcrt.getch()
    
    while True:
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Render current month
        render_calendar(tasks, year, month)
        
        # Show digit buffer if typing
        if digit_buffer:
            console.print(f"[bold yellow]Day: {digit_buffer}_[/bold yellow]", justify="center")
        
        # Wait for key press
        try:
            key = msvcrt.getch()
            
            # Handle arrow keys (they come as two bytes on Windows)
            if key == b'\xe0':  # Special key prefix
                key2 = msvcrt.getch()
                if key2 == b'K':  # Left arrow
                    month -= 1
                    if month < 1:
                        month = 12
                        year -= 1
                    digit_buffer = ""
                elif key2 == b'M':  # Right arrow
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    digit_buffer = ""
            elif key == b'q' or key == b'Q' or key == b'\x1b':  # q, Q, or Escape
                break
            elif key in [b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9']:
                # Numeric input for day selection
                digit_buffer += key.decode()
                if len(digit_buffer) >= 2:
                    # Try to show events for this day
                    day = int(digit_buffer)
                    max_day = cal_module.monthrange(year, month)[1]
                    if 1 <= day <= max_day:
                        show_day_events(day)
                    digit_buffer = ""
            elif key == b'\r':  # Enter key
                if digit_buffer:
                    day = int(digit_buffer)
                    max_day = cal_module.monthrange(year, month)[1]
                    if 1 <= day <= max_day:
                        show_day_events(day)
                    digit_buffer = ""
            else:
                digit_buffer = ""  # Clear buffer on other keys
        except KeyboardInterrupt:
            break
    
    # Just print newline on exit, don't clear screen
    console.print()

def render_goals(goals: List[Task]): # Type hint matches List[Goal] actually
    from rich.columns import Columns
    


    # Notebook Page Style
    if not goals:
        empty_text = Text()
        empty_text.append("\n\n\n", style="dim")
        empty_text.append("Your notebook is empty...\n", style="italic white")
        empty_text.append("Start adding some goals!\n", style="bold yellow")
        empty_text.append("\n\n\n", style="dim")
        
        panel = Panel(
            Align.center(empty_text),
            title="[bold white]📓 GOAL NOTEBOOK[/]",
            border_style="white",
            padding=(1, 2)
        )
        console.print(panel)
        return

    # List Display
    content = Text()
    
    # Sort: Incomplete first, then by creation date
    sorted_goals = sorted(goals, key=lambda g: (g.completed, g.created_date))
    
    page_content = Table(box=None, show_header=False, expand=True, padding=(0, 2))
    page_content.add_column("Status", width=4)
    page_content.add_column("Content", ratio=1)
    
    for i, goal in enumerate(sorted_goals, 1):
        theme = get_current_theme()
        idx_str = f"[bold {theme['primary']}]{i}.[/]"
        
        if goal.completed:
            status = Text.from_markup("[bold green]✓[/]")
            title_style = "dim strike white"
            date_str = f" [dim]({goal.completed_date.strftime('%Y-%m-%d')})[/]"
        else:
            status = Text.from_markup("[bold red]□[/]")
            title_style = "bold white"
            date_str = ""
            
        row_text = Text()
        row_text.append(f"{goal.title}", style=title_style)
        if date_str:
            row_text.append(Text.from_markup(date_str))
        
        page_content.add_row(
            f"{i}.", 
            Text.assemble(status, " ", row_text)
        )

    panel = Panel(
        page_content,
        title="[bold white]📓 GOAL NOTEBOOK[/]",
        border_style="white",
        subtitle="[dim]TDL goal add/check/del[/]",
        subtitle_align="right",
        padding=(1, 2)
    )
    console.print(panel)

def render_notes(notes: List):
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    
    theme = get_current_theme()
    
    if not notes:
        console.print(f"[dim]No thoughts dumped yet. Use 'TDL dump <text>' to add one.[/dim]", justify="center")
        return

    table = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 2))
    table.add_column("ID", width=4, justify="right")
    table.add_column("Date", width=12, justify="center")
    table.add_column("Content", ratio=1)
    
    # Sort notes by newest first
    sorted_notes = sorted(notes, key=lambda n: n.created_at, reverse=True)
    
    current_date_str = None
    
    for note in sorted_notes:
        date_str = note.created_at.strftime('%Y-%m-%d')
        time_str = note.created_at.strftime('%H:%M')
        
        display_date = f"[dim]{date_str}[/]" if date_str != current_date_str else ""
        current_date_str = date_str
        
        table.add_row(
            f"[bold {theme['primary']}]{note.id}.[/]",
            f"[{theme['secondary']}]{date_str}[/]\n[dim]{time_str}[/]",
            f"[white]{note.content}[/]"
        )
        table.add_row("", "", "") 

    panel = Panel(
        table,
        title=f"[bold {theme['warning']}]🧠 BRAIN DUMP[/]",
        border_style=theme["warning"],
        subtitle=f"[dim]Total: {len(notes)} | TDL dump <text> | TDL dump del <id>[/]",
        subtitle_align="right",
        padding=(1, 2)
    )
    console.print(panel)

def render_activity_heatmap():
    """Render Current Year activity heatmap (Jan 1 - Dec 31)."""
    from history_storage import load_history
    from config_storage import get_show_heatmap, get_theme
    from datetime import datetime, timedelta
    
    if not get_show_heatmap():
        return

    history = load_history()
    # Count per date
    counts = {}
    for t in history:
        if t.completed_at:
             d = t.completed_at.date()
             counts[d] = counts.get(d, 0) + 1
             
    # Grid logic: Current Year
    now = datetime.now()
    year = now.year
    jan1 = datetime(year, 1, 1).date()
    
    # Prepare rows
    rows = [""] * 7
    theme = get_current_theme()
    
    # 54 columns is safe max for any year layout (53 weeks + partial)
    for c in range(54):
        for r in range(7):
             # Calculate date
             # Grid starts at first week's Monday. 
             # jan1 might be Wed (2). So offset 0-1 are empty. Offset 2 is Jan 1.
             offset = c * 7 + r - jan1.weekday()
             date = jan1 + timedelta(days=offset)
             
             if offset < 0 or date.year != year:
                 # Outside current year boundaries -> Empty space
                 rows[r] += "  " 
                 continue
                 
             # Get count
             cnt = counts.get(date, 0)
             
             # Determine style
             if cnt == 0:
                 color_tag = "[#444444]" # Dim gray
                 symbol = "□"
             else:
                 symbol = "■"
                 if cnt <= 2:
                     color_tag = f"[dim {theme['success']}]"
                 elif cnt <= 5:
                     color_tag = f"[{theme['success']}]"
                 else:
                     color_tag = f"[bold {theme['success']}]" # Hot!
             
             rows[r] += f"{color_tag}{symbol}[/] "
             
    # Join rows
    heatmap_str = "\n".join(rows)
    
    # Panel
    panel = Panel(
        Align.center(heatmap_str),
        title=f"[bold {theme['success']}]🔥 {year} Activity[/]",
        border_style=theme["warning"],
        padding=(1, 2)
    )
    console.print(panel)

def print_welcome_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    from rich.panel import Panel
    from rich.text import Text
    from streak_storage import get_streak_display
    from config_storage import get_show_streak, get_simplicity
    
    # ASCII Art Title with rainbow gradient
    title_lines = [
        "████████╗██████╗ ██╗         ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ ",
        "╚══██╔══╝██╔══██╗██║         ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗",
        "   ██║   ██║  ██║██║         ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝",
        "   ██║   ██║  ██║██║         ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗",
        "   ██║   ██████╔╝███████╗    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║",
        "   ╚═╝   ╚═════╝ ╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"
    ]
    
    # Theme-based colors for each line
    theme = get_current_theme()
    rainbow_colors = theme["rainbow_colors"]
    
    # Streak Display (Compact & Right Aligned)
    if get_show_streak():
        console.print(Align.right(get_streak_display() + " "), style="bold")
    
    for i, line in enumerate(title_lines):
        console.print(line, style=f"bold {rainbow_colors[i % len(rainbow_colors)]}")
    console.print()
    
    # Check if simplicity mode is enabled
    simplicity_mode = get_simplicity()
    
    if not simplicity_mode:
        # Welcome message with theme gradient
        welcome_text = Text()
        welcome_text.append("✨ ", style=f"bold {theme['warning']}")
        welcome_text.append("Welcome to ", style="bold white")
        welcome_text.append("T", style=f"bold {theme['primary']}")
        welcome_text.append("D", style=f"bold {theme['secondary']}")
        welcome_text.append("L", style=f"bold {theme['success']}")
        welcome_text.append(" - Your ", style="bold white")
        welcome_text.append(f"{get_theme().capitalize()}", style=f"bold {theme['secondary']}")
        welcome_text.append(" Terminal Task Manager! ", style="bold white")
        welcome_text.append("✨", style=f"bold {theme['warning']}")
        console.print(Panel(welcome_text, style=f"bold {theme['secondary']}", padding=(1, 2)))
        console.print()
        
        # Commands organized by category
        task_commands = Panel(
            f"[bold {theme['error']}]Task Management[/]\n\n"
            f"[{theme['success']}]TDL db[/]              - View all tasks\n"
            f"[{theme['success']}]TDL add[/]             - Add new task\n"
            f"[{theme['success']}]TDL add ... -r[/]      - Add recurring task\n"
            f"[{theme['success']}]TDL <ID> -d/-c/-t[/]   - Update task\n"
            f"[{theme['success']}]TDL del <ID>[/]        - Delete task\n"
            f"[{theme['success']}]TDL check[/]           - Mark tasks complete\n"
            f"[{theme['success']}]TDL info <ID>[/]       - View task details",
            title=f"[bold {theme['error']}]📝 Tasks[/]",
            border_style=theme["error"],
            padding=(1, 2)
        )
        
        focus_commands = Panel(
            "[bold orange1]Deep Work[/]\n\n"
            f"[{theme['success']}]TDL work <ID>[/]      - Start deep work session\n"
            "[dim]  • Timer with GIF animation[/]\n"
            "[dim]  • Press SPACE to pause[/]\n"
            "[dim]  • Extend or complete after[/]\n\n",
            title="[bold orange1]⏱ Focus[/]",
            border_style="orange1",
            padding=(1, 2)
        )
        
        org_commands = Panel(
            f"[bold {theme['success']}]Organization & Stats[/]\n\n"
            f"[{theme['success']}]TDL add cat <name>[/] - Add category\n"
            f"[{theme['success']}]TDL cat[/]            - List categories\n"
            f"[{theme['success']}]TDL stat[/]           - View statistics\n"
            f"[{theme['success']}]TDL settings[/]       - App settings\n"
            f"[{theme['success']}]TDL clear[/]          - Archive done\n"
            f"[{theme['success']}]TDL hist[/]           - View history",
            title=f"[bold {theme['success']}]🗂 Organize[/]",
            border_style=theme["success"],
            padding=(1, 2)
        )

        filter_commands = Panel(
            f"[bold {theme['primary']}]Views & Filters[/]\n\n"
            f"[{theme['success']}]TDL calendar[/]       - Interactive Calendar\n"
            f"[{theme['success']}]TDL rc[/]             - Recurring tasks\n"
            f"[{theme['success']}]TDL today[/]          - Due today\n"
            f"[{theme['success']}]TDL tomorrow[/]       - Due tomorrow\n"
            f"[{theme['success']}]TDL this-week[/]     - Due this week\n"
            f"[{theme['success']}]TDL this-month[/]    - Due this month",
            title=f"[bold {theme['primary']}]📅 Views[/]",
            border_style=theme["primary"],
            padding=(1, 2)
        )

        
        # Display in columns (2x2 grid)
        console.print(Columns([task_commands, focus_commands], equal=True, expand=True))
        console.print(Columns([org_commands, filter_commands], equal=True, expand=True))
        console.print()
        
        # Quick tips
        tips = Panel(
            f"[bold {theme['secondary']}]💡 Quick Tips:[/]\n\n"
            f"• Use [{theme['error']}]-f 1[/] for important, [dim]-f -1[/] unimportant\n"
            "• Set duration: [orange1]-t 2h30m[/]\n"
            f"• Relative dates: [{theme['success']}]today[/], [{theme['success']}]tomorrow[/]\n"
            f"• Type [{theme['primary']}]TDL <ID>[/] to update tasks",
            title=f"[bold {theme['secondary']}]✨ Tips[/]",
            border_style=theme["secondary"],
            padding=(1, 2)
        )
        console.print(tips)

        console.print()
    
    # Activity Heatmap (shown independently based on its own toggle)
    render_activity_heatmap()
    console.print()
    
    # Theme footer (always shown)
    footer_text = Text()
    footer_words = ["✨", "Type", "TDL", "db", "to", "view", "your", "tasks", "✨"]
    footer_colors = theme["rainbow_colors"]
    
    for i, word in enumerate(footer_words):
        if word == "TDL" or word == "db":
            footer_text.append(word, style=f"bold {footer_colors[i % len(footer_colors)]}")
        else:
            footer_text.append(word, style=footer_colors[i % len(footer_colors)])
        footer_text.append(" ")
    
    console.print(Align.center(footer_text))
    console.print()
