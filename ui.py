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
from typing import List
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
    
    # Show Streak at top right (compact)
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
    
    # Sort each group by priority (important first), then due date/title
    for group in grouped.values():
        group.sort(key=lambda x: (
            -x.priority,  # Important first
            x.due_date if x.due_date else datetime.max,  # Then by due date
            x.title.lower()  # Then alphabetically
        ))
    
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
    def get_category_color(category_name):
        """Get consistent color for a category using hash"""
        theme = get_current_theme()
        colors = theme["rainbow_colors"]
        # Use hash of lowercase to get consistent index regardless of capitalization
        color_index = hash(category_name.lower()) % len(colors)
        return colors[color_index]
    
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
            if task.completed:
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
                    recurrence_icon
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
                    recurrence_icon
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
                    recurrence_icon
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
                    recurrence_icon
                ]

            
            # Filter out empty parts and join
            line = "  ".join(part for part in line_parts if part)
            console.print(line)
            
            task_id += 1
    
    console.print()  # Final newline

def render_task_list(tasks: List[Task]):
    """Render a simple list of tasks without grouping"""
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
    
    # Create consistent color mapping for categories
    def get_category_color(category_name):
        """Get consistent color for a category using hash"""
        theme = get_current_theme()
        colors = theme["rainbow_colors"]
        color_index = hash(category_name.lower()) % len(colors)
        return colors[color_index]
    
    # Sort by priority then due date
    sorted_tasks = sorted(tasks, key=lambda x: (
        -x.priority,
        x.due_date if x.due_date else datetime.max,
        x.title.lower()
    ))
    
    # Render each task
    task_id = 1
    for task in sorted_tasks:
        # ID
        theme = get_current_theme()
        id_str = f"[bold {theme['primary']}]{task_id}[/bold {theme['primary']}]"
        
        # Checkbox
        check = "[dim][✓][/dim]" if task.completed else "[ ]"
        
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
        
        # Apply styling based on priority and completion
        if task.completed:
            line_parts = [
                id_str, check,
                f"[dim strike]{due_str}[/dim strike]" if due_str else "",
                f"[dim strike]{tags}[/dim strike]" if tags else "",
                f"[dim strike]{title}[/dim strike]",
                f"[dim strike]{duration}[/dim strike]" if duration else ""
            ]
        elif task.priority == 1:
            line_parts = [
                id_str, check,
                f"[red]{due_str}[/red]" if due_str else "",
                tags,
                f"[bold red]{title}[/bold red]",
                f"[red]{duration}[/red]" if duration else ""
            ]
        elif task.priority == -1:
            line_parts = [
                id_str, check,
                f"[dim]{due_str}[/dim]" if due_str else "",
                f"[dim]{tags}[/dim]" if tags else "",
                f"[dim]{title}[/dim]",
                f"[dim]{duration}[/dim]" if duration else ""
            ]
        else:
            line_parts = [
                id_str, check, due_str, tags, title, duration
            ]
        
        line = "  ".join(part for part in line_parts if part)
        console.print(line)
        task_id += 1
    
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
        theme = get_current_theme()
        if not task.category:
             return "white"
             
        cat_to_use = task.category[0] if isinstance(task.category, list) and task.category else task.category
        if isinstance(cat_to_use, list): # Should not happen based on logic above but safety check
            cat_to_use = cat_to_use[0]
            
        if not cat_to_use:
            return "white"
            
        colors = theme["rainbow_colors"]
        color_index = hash(cat_to_use.lower()) % len(colors)
        return colors[color_index]

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
                    cell_text.append(f"• {task.title[:10]}...\n", style=color)
            
            row_cells.append(cell_text)
        
        table.add_row(*row_cells, end_section=True)

    console.print(table)
    console.print("[dim]← / → navigate months  |  Type day (1-31) to view events  |  q to exit[/dim]", justify="center")
    
    return year, month

def render_calendar_interactive(tasks: List[Task]):
    """Interactive calendar with arrow key navigation and day selection."""
    import msvcrt
    import os
    import calendar as cal_module
    
    now = datetime.now()
    year = now.year
    month = now.month
    digit_buffer = ""
    
    def get_task_color(task):
        theme = get_current_theme()
        if not task.category:
             return "white"
             
        cat_to_use = task.category[0] if isinstance(task.category, list) and task.category else task.category
        if isinstance(cat_to_use, list):
            cat_to_use = cat_to_use[0]
            
        if not cat_to_use:
            return "white"
            
        colors = theme["rainbow_colors"]
        color_index = hash(cat_to_use.lower()) % len(colors)
        return colors[color_index]
    
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
                
                if time_str:
                    console.print(f"  [{color}]• {time_str}[/{color}] {task.title}")
                else:
                    console.print(f"  [{color}]•[/{color}] {task.title}")
                    
                if task.category:
                    if isinstance(task.category, list):
                        cat_str = " ".join([f"#{c}" for c in task.category])
                    else:
                        cat_str = f"#{task.category}"
                    console.print(f"    [dim]{cat_str}[/dim]")
        
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
