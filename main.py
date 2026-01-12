import typer
import os
from rich import print
from rich.table import Table
from rich.console import Console
from rich import box
from typing import Optional, List
from datetime import datetime
import questionary
from dateutil import parser as date_parser

from models import Task, Goal, Template
from storage import load_tasks, save_tasks
from goals_storage import load_goals, save_goals
from categories_storage import load_categories, save_categories
from history_storage import load_history, add_to_history, save_history
from notes_storage import load_notes, save_notes, Note
from templates_storage import load_templates, save_templates, get_template_by_alias
import ui
from rich.align import Align
from config_storage import load_config, save_config, get_theme

app = typer.Typer(help="Fast CLI TDL App with Rainbow Dashboard")
console = Console()

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string in format XXhXXmXXs to total seconds."""
    import re
    
    # Match pattern like "2h30m15s", "1h", "30m", "45s", etc.
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.fullmatch(pattern, duration_str.lower())
    
    if not match or not any(match.groups()):
        return None
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds

def resolve_category_input(input_str: str) -> List[str]:
    """
    Resolve category input which can be:
    - Category names: "Work, Health"
    - Category IDs: "1, 2" 
    - Mixed: "Work, 2"
    
    Returns list of resolved category names.
    """
    cats = load_categories()
    result = []
    
    parts = [p.strip() for p in input_str.split(',') if p.strip()]
    
    for part in parts:
        # Check if it's a number (category ID)
        if part.isdigit():
            idx = int(part) - 1  # Convert to 0-based index
            if 0 <= idx < len(cats):
                resolved = cats[idx]
                if "," in resolved:
                    result.extend([c.strip() for c in resolved.split(',') if c.strip()])
                else:
                    result.append(resolved)
            else:
                # ID out of range, treat as literal
                result.append(part.capitalize())
        else:
            # It's a category name
            result.append(part.capitalize())
    
    return result

def get_task_dashboard_order(tasks: List[Task]) -> List[Task]:
    """Sort tasks identically to ui.render_dashboard grouping and sorting."""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)
    
    grouped = {
        "non-assigned": [],
        "Today": [],
        "Tomorrow": [],
        "This week": [],
        "This month": [],
        "Future": []
    }
    
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
    
    # Sort buckets (Category -> Priority -> DueDate -> Title)
    for group in grouped.values():
        group.sort(key=lambda t: (
            (t.category[0].lower() if isinstance(t.category, list) and t.category else (t.category.lower() if isinstance(t.category, str) else "")) if t.category else "",
            -t.priority,
            t.due_date if t.due_date else datetime.max,
            t.title.lower()
        ))
    
    # Flatten
    ordered = []
    ordered.extend(grouped["non-assigned"])
    ordered.extend(grouped["Today"])
    ordered.extend(grouped["Tomorrow"])
    ordered.extend(grouped["This week"])
    ordered.extend(grouped["This month"])
    ordered.extend(grouped["Future"])
    
    return ordered

def resolve_task_target(identifier: str) -> Tuple[Task, List[Task]]:
    """
    Resolve task by '1' (Task) or '#1' (Event).
    Matches dashboard/event list display order.
    Returns (task, all_tasks) tuple.
    """
    import typer
    is_event_target = identifier.startswith("#")
    
    clean_id_str = identifier[1:] if is_event_target else identifier
    
    if not clean_id_str.isdigit():
        print(f"[red]Invalid ID format: {identifier}. Use 'N' for task or '#N' for event.[/]")
        raise typer.Exit(1)
         
    target_idx = int(clean_id_str)
    
    all_tasks = load_tasks()
    
    if is_event_target:
        candidates = [t for t in all_tasks if t.title.startswith("📅")]
    else:
        candidates = [t for t in all_tasks if not t.title.startswith("📅")]
        
    ordered = get_task_dashboard_order(candidates)
    
    if target_idx < 1 or target_idx > len(ordered):
        print(f"[red]ID {identifier} not found. (Available: 1-{len(ordered)})[/]")
        raise typer.Exit(1)
        
    return ordered[target_idx - 1], all_tasks

def configure_recurrence():
    """Interactive recurrence configuration. Returns (type, days, interval) or (None, None, 1) if cancelled."""
    
    recurrence_choices = [
        questionary.Choice("Daily", value="daily"),
        questionary.Choice("Weekly", value="weekly"),
        questionary.Choice("Monthly", value="monthly"),
        questionary.Choice("Custom days", value="custom"),
        questionary.Choice("Cancel", value="__CANCEL__")
    ]
    
    rec_type = questionary.select(
        "Select recurrence type:",
        choices=recurrence_choices
    ).ask()
    
    if rec_type == "__CANCEL__" or rec_type is None:
        return None, None, 1
    
    recurrence_days = None
    recurrence_interval = 1
    
    if rec_type == "custom":
        # Let user pick specific days
        day_choices = [
            questionary.Choice("Monday", value=0),
            questionary.Choice("Tuesday", value=1),
            questionary.Choice("Wednesday", value=2),
            questionary.Choice("Thursday", value=3),
            questionary.Choice("Friday", value=4),
            questionary.Choice("Saturday", value=5),
            questionary.Choice("Sunday", value=6)
        ]
        recurrence_days = questionary.checkbox(
            "Select days:",
            choices=day_choices
        ).ask()
        
        if not recurrence_days:
            return None, None, 1
    
    elif rec_type in ["weekly", "monthly"]:
        # Ask for interval
        interval_str = questionary.text(
            f"Repeat every how many {'weeks' if rec_type == 'weekly' else 'months'}? (default: 1)"
        ).ask()
        
        if interval_str and interval_str.isdigit():
            recurrence_interval = int(interval_str)
    
    return rec_type, recurrence_days, recurrence_interval


def get_recurrence_display(task) -> str:
    """Get human-readable recurrence description."""
    if not task.recurrent or not task.recurrence_type:
        return ""
    
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    if task.recurrence_type == "daily":
        return "Daily"
    elif task.recurrence_type == "weekly":
        interval = task.recurrence_interval or 1
        return f"Every {interval} week{'s' if interval > 1 else ''}"
    elif task.recurrence_type == "monthly":
        interval = task.recurrence_interval or 1
        return f"Every {interval} month{'s' if interval > 1 else ''}"
    elif task.recurrence_type == "custom" and task.recurrence_days:
        days_str = ", ".join([day_names[d] for d in task.recurrence_days])
        return f"Every {days_str}"
    
    return task.recurrence_type

@app.command()
def add(
    title: Optional[str] = typer.Argument(None, help="The task description"),
    category: Optional[str] = typer.Option(None, "-c", help="Category for the task"),
    due: Optional[str] = typer.Option(None, "-d", help="Due date/time (e.g. 'tomorrow', '2023-10-25')"),
    time: Optional[str] = typer.Option(None, "-t", help="Time duration (e.g. '2h30m', '45m', '1h30m15s')"),
    flag: Optional[int] = typer.Option(None, "-f", "--flag", help="Set priority: -1=unimportant, 0=normal, 1=important"),
    rc: bool = typer.Option(False, "-r", "--rc", help="Make this a recurring task"),
    description: Optional[str] = typer.Option(None, "-i", "--info", help="Additional description/info for the task")
):
    """Add a new task rapidly."""
    interactive = False
    template_loaded = None
    
    # Check if title starts with * (template alias)
    if title and title.startswith("*"):
        alias = title[1:]  # Remove the * prefix
        template_loaded = get_template_by_alias(alias)
        
        if not template_loaded:
            print(f"[red]Template '{alias}' not found. Use 'TDL template' to view available templates.[/]")
            return
        
        # Load template defaults (can be overridden by flags)
        print(f"[cyan]Loading template: {alias}[/]")
        title = template_loaded.title
        
        # Only use template values if not explicitly provided via flags
        if category is None and template_loaded.category:
            category = ",".join(template_loaded.category) if isinstance(template_loaded.category, list) else template_loaded.category
        
        if due is None and template_loaded.due_date_offset:
            due = template_loaded.due_date_offset
        
        if time is None and template_loaded.time_duration:
            time = None  # Will use template_loaded.time_duration directly later
        
        if flag is None:
            flag = template_loaded.priority
        
        if not rc:
            rc = template_loaded.recurrent
    
    if not title:
        interactive = True
        title = questionary.text("Task:").ask()
        if not title:
            return
    
    if not category and interactive:
        category = questionary.text("Category (Optional):").ask()
        if category == "":
            category = None
            
    if not description and interactive:
        add_desc = questionary.confirm("Add description?", default=False).ask()
        if add_desc:
            description = questionary.text("Description:").ask()
    
    # Parse categories - support IDs and names (comma-separated)
    parsed_categories = None
    if category:
        # Use helper to resolve IDs to names
        categories_list = resolve_category_input(category)
        parsed_categories = categories_list if categories_list else None
            
    due_date = None
    if due:
        lower_due = due.lower()
        now = datetime.now()
        if lower_due == "today":
            due_date = now
        elif lower_due == "tomorrow":
            from datetime import timedelta
            due_date = now + timedelta(days=1)
        else:
            try:
                due_date = date_parser.parse(due, fuzzy=True)
            except:
                print(f"[red]Could not parse date: {due}[/]")
                return
    elif interactive:
        # Only prompt in full interactive mode
        add_date = questionary.confirm("Add due date?", default=False).ask()
        if add_date:
            date_str = questionary.text("Due Date:").ask()
            if date_str:
                lower_due = date_str.lower()
                now = datetime.now()
                if lower_due == "today":
                    due_date = now
                elif lower_due == "tomorrow":
                    from datetime import timedelta
                    due_date = now + timedelta(days=1)
                else:
                    try:
                        due_date = date_parser.parse(date_str, fuzzy=True)
                    except:
                        print(f"[red]Could not parse date.[/]")
    
    # Parse time duration
    duration_seconds = None
    if time:
        duration_seconds = parse_duration(time)
        if duration_seconds is None:
            print(f"[red]Invalid duration format: {time}. Use format like '2h30m15s'[/]")
            return
    elif template_loaded and template_loaded.time_duration:
        # Use template duration if no explicit time provided
        duration_seconds = template_loaded.time_duration
            
    # Set priority from flag
    priority = 0
    if flag is not None:
        if flag not in [-1, 0, 1]:
            print(f"[red]Invalid priority: {flag}. Use -1 (unimportant), 0 (normal), or 1 (important)[/]")
            return
        priority = flag
    
    # Handle recurrence
    recurrence_type = None
    recurrence_days = None
    recurrence_interval = 1
    
    if rc:
        recurrence_type, recurrence_days, recurrence_interval = configure_recurrence()
        if recurrence_type is None:
            print("[yellow]Recurrence setup cancelled.[/]")
            rc = False
    elif template_loaded and template_loaded.recurrent:
        # Load template recurrence settings if no explicit -r flag
        recurrence_type = template_loaded.recurrence_type
        recurrence_days = template_loaded.recurrence_days
        recurrence_interval = template_loaded.recurrence_interval
    
    tasks = load_tasks()
    new_task = Task(
        title=title, 
        category=parsed_categories, 
        due_date=due_date, 
        time_duration=duration_seconds, 
        priority=priority,
        description=description,
        recurrent=rc,
        recurrence_type=recurrence_type,
        recurrence_days=recurrence_days,
        recurrence_interval=recurrence_interval
    )
    tasks.append(new_task)
    save_tasks(tasks)
    
    # Build display message
    msg = f"[bold green]Task added![/] :rocket: [dim]{new_task.id}[/]"
    if duration_seconds:
        msg += f" [yellow]Duration: {new_task.get_duration_str()}[/]"
    if parsed_categories:
        msg += f" [cyan]Categories: {', '.join(parsed_categories)}[/]"
    if priority != 0:
        priority_names = {-1: "Unimportant", 1: "IMPORTANT"}
        priority_colors = {-1: "dim", 1: "bold red"}
        msg += f" [{priority_colors[priority]}]Flag: {priority_names[priority]}[/]"
    if rc:
        msg += f" [magenta]🔁 Recurring ({recurrence_type})[/]"

    print(msg)

@app.command()
@app.command(name="db")  # Alias for fast typing
def dashboard():
    """Display all tasks in a dashboard view (Categories & Time)."""
    tasks = load_tasks()
    # Filter out calendar events (tasks starting with 📅)
    dashboard_tasks = [t for t in tasks if not t.title.startswith("📅")]
    ui.render_dashboard(dashboard_tasks)

@app.command()
def today():
    """Show only tasks due today."""
    from datetime import datetime
    tasks = load_tasks()
    now = datetime.now()
    today_date = now.date()
    
    # Filter tasks due today
    today_tasks = [t for t in tasks if t.due_date and t.due_date.date() == today_date]
    
    # Sort into Tasks and Events
    events = [t for t in today_tasks if t.title.startswith("📅")]
    tasks_only = [t for t in today_tasks if not t.title.startswith("📅")]

    console.print("\n[bold red]📅 TODAY[/bold red]")
    
    if events:
        console.print("[bold yellow]Events:[/]")
        ui.render_task_list(events)
        if tasks_only:
             console.print("[bold white]Tasks:[/]")
    
    if tasks_only:
        ui.render_task_list(tasks_only)
    elif not events:
        print("[yellow]No tasks due today![/]")

@app.command()
def tomorrow():
    """Show only tasks due tomorrow."""
    from datetime import datetime, timedelta
    tasks = load_tasks()
    now = datetime.now()
    tomorrow_date = (now + timedelta(days=1)).date()
    
    # Filter tasks due tomorrow
    tomorrow_tasks = [t for t in tasks if t.due_date and t.due_date.date() == tomorrow_date]
    
    # Sort into Tasks and Events
    events = [t for t in tomorrow_tasks if t.title.startswith("📅")]
    tasks_only = [t for t in tomorrow_tasks if not t.title.startswith("📅")]
    
    console.print("\n[bold yellow]📅 TOMORROW[/bold yellow]")
    
    if events:
        console.print("[bold yellow]Events:[/]")
        ui.render_task_list(events)
        if tasks_only:
             console.print("[bold white]Tasks:[/]")
             
    if tasks_only:
        ui.render_task_list(tasks_only)
    elif not events:
        print("[yellow]No tasks due tomorrow![/]")

@app.command(name="this-week")
def this_week():
    """Show only tasks due this week (excluding today and tomorrow)."""
    from datetime import datetime, timedelta
    tasks = load_tasks()
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    # Filter tasks due this week (excluding today and tomorrow)
    week_tasks = [t for t in tasks if t.due_date and tomorrow < t.due_date.date() <= week_end]
    
    # Sort into Tasks and Events
    events = [t for t in week_tasks if t.title.startswith("📅")]
    tasks_only = [t for t in week_tasks if not t.title.startswith("📅")]
    
    console.print("\n[bold green]📅 THIS WEEK[/bold green]")
    
    if events:
        console.print("[bold yellow]Events:[/]")
        ui.render_task_list(events)
        if tasks_only:
             console.print("[bold white]Tasks:[/]")

    if tasks_only:
        ui.render_task_list(tasks_only)
    elif not events:
        print("[yellow]No more tasks due this week![/]")

@app.command(name="this-month")
def this_month():
    """Show only tasks due this month (excluding this week)."""
    from datetime import datetime, timedelta
    tasks = load_tasks()
    now = datetime.now()
    today = now.date()
    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)
    
    # Filter tasks due this month (excluding this week)
    month_tasks = [t for t in tasks if t.due_date and week_end < t.due_date.date() <= month_end]
    
    # Sort into Tasks and Events
    events = [t for t in month_tasks if t.title.startswith("📅")]
    tasks_only = [t for t in month_tasks if not t.title.startswith("📅")]
    
    console.print("\n[bold blue]📅 THIS MONTH[/bold blue]")
    
    if events:
        console.print("[bold yellow]Events:[/]")
        ui.render_task_list(events)
        if tasks_only:
             console.print("[bold white]Tasks:[/]")

    if tasks_only:
        ui.render_task_list(tasks_only)
    elif not events:
        print("[yellow]No more tasks due this month![/]")

@app.command()
def calendar():
    """View the interactive calendar with arrow key navigation."""
    tasks = load_tasks()
    
    # Filter to show only events (strictly starting with 📅)
    events = [t for t in tasks if t.title.startswith("📅")]
    
    ui.render_calendar_interactive(events)
    
    # Refresh screen and show welcome on exit
    os.system('cls' if os.name == 'nt' else 'clear')
    ui.print_welcome_screen()


@app.command()
def event(
    name: List[str] = typer.Argument(..., help="Event name or subcommand (list, update <ID>)"),
    due: Optional[str] = typer.Option(None, "-d", help="Date/time (e.g. 'tomorrow 3pm')"),
    category: Optional[str] = typer.Option(None, "-c", help="Category"),
    description: Optional[str] = typer.Option(None, "-i", "--info", help="Description")
):
    """
    Manage calendar events.
    
    Usage:
    • Add:    TDL event "Meeting" -d tomorrow
    • List:   TDL event list
    • Update: TDL event update <ID> -d new-date
    """
    import uuid
    
    command = name[0].lower()
    
    # Handle 'list' subcommand
    if len(name) == 1 and command == "list":
        tasks = load_tasks()
        
        events = [t for t in tasks if t.title.startswith("📅")]
        events.sort(key=lambda t: t.due_date if t.due_date else datetime.max)
        
        # Use dashboard renderer for grouped view (Today, Tomorrow, etc.)
        ui.render_dashboard(events)
        return

    # Handle 'update' subcommand
    if command == "update" and len(name) >= 2 and name[1].isdigit():
        task_id = int(name[1])
        # Call the update command directly
        update(task_id, category, due, None, None, None, description)
        return

    # --- Standard Add Event Logic ---
    
    event_title = " ".join(name)
    
    # If no date provided, prompt for it
    if not due:
        due = questionary.text("Enter event date/time (e.g. 'tomorrow 3pm', '2026-01-15'):").ask()
        if not due:
            print("[yellow]Event cancelled.[/]")
            return
    
    # Parse the date
    try:
        lower_due = due.lower()
        now = datetime.now()
        
        if lower_due == "today":
            parsed_date = now
        elif lower_due == "tomorrow":
            from datetime import timedelta
            parsed_date = now + timedelta(days=1)
        else:
            parsed_date = date_parser.parse(due, fuzzy=True)
    except Exception:
        print(f"[red]Could not parse date: {due}[/]")
        return
    
    # Parse categories using helper
    categories = None
    if category:
        # Use helper to resolve IDs to names
        categories_list = resolve_category_input(category)
        categories = categories_list if categories_list else None
        
        # Original logic supported single string storage for events, but list is better
        # For consistency with Task logic, we keep list, but check if we need to flatten
        # The Task model supports List[str].
        pass # categories is already List[str] or None
    
    # Create the event as a task
    new_event = Task(
        id=str(uuid.uuid4()),
        title=f"📅 {event_title}",
        category=categories,
        due_date=parsed_date,
        completed=False,
        priority=0,
        description=description
    )
    
    tasks = load_tasks()
    tasks.append(new_event)
    save_tasks(tasks)
    
    date_str = parsed_date.strftime('%Y-%m-%d %H:%M') if parsed_date.hour or parsed_date.minute else parsed_date.strftime('%Y-%m-%d')
    print(f"[bold green]📅 Event added![/] {event_title}")
    print(f"[dim]Date: {date_str}[/]")
    if categories:
        if isinstance(categories, list):
            cat_display = " ".join([f"#{c}" for c in categories])
        else:
            cat_display = f"#{categories}"
        print(f"[dim]Categories: {cat_display}[/]")

@app.command()
def check():
    """Interactive task completion."""
    tasks = load_tasks()
    open_tasks = [t for t in tasks if not t.completed]
    
    if not open_tasks:
        print("[green]No pending tasks! Good job![/]")
        return

    # Create choices for checklist
    choices = []
    for t in open_tasks:
        display = f"{t.title}"
        if t.category:
            if isinstance(t.category, list):
                display += f" [{', '.join(t.category)}]"
            else:
                display += f" [{t.category}]"
        if t.due_date:
            display += f" ({t.due_date.strftime('%m-%d')})"
        choices.append(questionary.Choice(title=display, value=t.id))

    selected_ids = questionary.checkbox(
        "Select tasks to complete:",
        choices=choices,
    ).ask()

    if selected_ids:
        count = 0
        completion_time = datetime.now()
        for t in tasks:
            if t.id in selected_ids:
                t.completed = True
                t.completed_at = completion_time  # NEW: track completion time
                count += 1
        save_tasks(tasks)
        
        # Update streak
        from streak_storage import update_streak, get_streak_display
        from config_storage import get_show_streak
        
        streak, active = update_streak()
        
        if get_show_streak():
            print(f"[bold green]Completed {count} tasks![/] {get_streak_display()}")
        else:
            print(f"[bold green]Completed {count} tasks![/]")
    else:
        print("[yellow]No tasks completed.[/]")



@app.command()
def update(
    task_id: str = typer.Argument(..., help="Task ID (1-10) or Event ID (#1)"),
    category: Optional[str] = typer.Option(None, "-c", help="New category"),
    due: Optional[str] = typer.Option(None, "-d", help="New due date (e.g. 'today', 'tomorrow', '2023-10-25')"),
    time: Optional[str] = typer.Option(None, "-t", help="Time duration (e.g. '2h30m', '45m', '1h30m15s')"),
    flag: Optional[int] = typer.Option(None, "-f", "--flag", help="Set priority: -1=unimportant, 0=normal, 1=important"),
    rc: Optional[int] = typer.Option(None, "-r", help="Toggle recurrence: 0=off, 1=on (opens config)"),
    description: Optional[str] = typer.Option(None, "-i", "--info", help="Set or update task description")
):
    """Update a task's category, due date, duration, or importance by its ID."""
    # Ensure task_id is string
    task_id = str(task_id)
    
    # Handle multiple IDs (e.g. "1,2,#1")
    if "," in task_id:
        ids = [x.strip() for x in task_id.split(',') if x.strip()]
        if len(ids) > 1:
            print(f"[cyan]Batch updating {len(ids)} items...[/]")
            for i in ids:
                print(f"\n[dim]--- Updating {i} ---[/]")
                update(i, category, due, time, flag, rc, description)
            return

    task, all_tasks = resolve_task_target(task_id)
    
    if not task:
        print(f"[red]Task ID {task_id} not found.[/]")
        return
    
    # Update category
    if category is not None:
        if category == "":
            task.category = None
            print(f"[green]Removed categories[/]")
        else:
            # Use helper to resolve IDs to names
            categories_list = resolve_category_input(category)
            task.category = categories_list if categories_list else None
            print(f"[green]Updated categories to: {', '.join(categories_list) if categories_list else 'None'}[/]")
    
    # Update due date
    if due is not None:
        lower_due = due.lower()
        now = datetime.now()
        
        if lower_due == "today":
            task.due_date = now
        elif lower_due == "tomorrow":
            from datetime import timedelta
            task.due_date = now + timedelta(days=1)
        elif lower_due == "none" or lower_due == "":
            task.due_date = None
        else:
            try:
                task.due_date = date_parser.parse(due, fuzzy=True)
            except:
                print(f"[red]Could not parse date: {due}[/]")
                return
        
        date_str = task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else "None"
        print(f"[green]Updated due date to: {date_str}[/]")
    
    # Update time duration
    if time is not None:
        if time.lower() in ["none", "", "0"]:
            task.time_duration = None
            print(f"[green]Removed time duration[/]")
        else:
            duration_seconds = parse_duration(time)
            if duration_seconds is None:
                print(f"[red]Invalid duration format: {time}. Use format like '2h30m15s'[/]")
                return
            task.time_duration = duration_seconds
            print(f"[green]Updated time duration to: {Task.get_duration_str(task)}[/]")
    
    # Set priority
    if flag is not None:
        if flag not in [-1, 0, 1]:
            print(f"[red]Invalid priority: {flag}. Use -1 (unimportant), 0 (normal), or 1 (important)[/]")
            return
        task.priority = flag
        priority_names = {-1: "unimportant", 0: "normal", 1: "IMPORTANT"}
        priority_colors = {-1: "dim", 0: "green", 1: "bold red"}
        print(f"[{priority_colors[flag]}]Task priority set to: {priority_names[flag]}[/]")
    
    # Toggle recurrence
    if rc is not None:
        if rc == 0:
            task.recurrent = False
            task.recurrence_type = None
            task.recurrence_days = None
            task.recurrence_interval = 1
            print("[green]Recurrence disabled[/]")
        elif rc == 1:
            rec_type, rec_days, rec_interval = configure_recurrence()
            if rec_type:
                task.recurrent = True
                task.recurrence_type = rec_type
                task.recurrence_days = rec_days
                task.recurrence_interval = rec_interval
                print(f"[magenta]🔁 Recurrence enabled: {get_recurrence_display(task)}[/]")
            else:
                print("[yellow]Recurrence setup cancelled[/]")
        else:
            print("[red]Invalid rc value. Use 0 to disable, 1 to enable.[/]")
            return
    
    # Update description
    if description is not None:
        if description == "":
            task.description = None
            print(f"[green]Removed description[/]")
        else:
            task.description = description
            print(f"[green]Updated description[/]")
    
    save_tasks(all_tasks)
    print(f"[bold green]Task '{task.title}' updated![/] ✓")


@app.command()
def delete(
    task_id: str = typer.Argument(..., help="Task ID (1-10) or #ID")
):
    """Delete a task (or multiple tasks) by ID (e.g. '1', '1,2', '#1')."""
    import typer
    
    ids = [x.strip() for x in task_id.split(',') if x.strip()]
    resolved_tasks = []
    all_tasks_ref = None
    
    for i in ids:
        try:
            task, all_tasks = resolve_task_target(i)
            resolved_tasks.append(task)
            if all_tasks_ref is None:
                all_tasks_ref = all_tasks
        except (typer.Exit, SystemExit):
            pass # Error message printed by resolve_task_target
            
    if not resolved_tasks:
        return
    
    # Confirm deletion
    count = len(resolved_tasks)
    titles = [t.title for t in resolved_tasks]
    display_titles = ", ".join(titles[:3])
    if count > 3: 
        display_titles += ", ..."
        
    confirm = questionary.confirm(
        f"Delete {count} task(s)? ({display_titles})",
        default=False
    ).ask()
    
    if confirm:
        deleted_count = 0
        for t in resolved_tasks:
            if t in all_tasks_ref:
                all_tasks_ref.remove(t)
                deleted_count += 1
        save_tasks(all_tasks_ref)
        print(f"[bold red]Deleted {deleted_count} task(s)![/] 🗑️")
    else:
        print("[yellow]Deletion cancelled.[/]")


@app.command()
def config(
    task_id: str = typer.Argument(..., help="Task ID to configure recurrence")
):
    """Configure recurrence settings for a task."""
    task, all_tasks = resolve_task_target(task_id)
    
    if not task:
        print(f"[red]Task ID {task_id} not found.[/]")
        return
    
    print(f"[cyan]Configuring recurrence for: {task.title}[/]")
    
    rec_type, rec_days, rec_interval = configure_recurrence()
    
    if rec_type:
        task.recurrent = True
        task.recurrence_type = rec_type
        task.recurrence_days = rec_days
        task.recurrence_interval = rec_interval
        save_tasks(all_tasks)
        print(f"[bold magenta]🔁 Recurrence set: {get_recurrence_display(task)}[/]")
    else:
        print("[yellow]Configuration cancelled.[/]")

@app.command(name="rc")
def rc():
    """List all recurring tasks."""
    tasks = load_tasks()
    recurring = [t for t in tasks if t.recurrent]
    
    if not recurring:
        print("[yellow]No recurring tasks found.[/]")
        return
    
    console.print("\n[bold magenta]🔁 RECURRING TASKS[/bold magenta]\n")
    
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("ID", width=4, style="bold cyan", justify="center")
    table.add_column("Task", style="white")
    table.add_column("Recurrence", style="magenta")
    table.add_column("Due", style="yellow")
    
    # Get display IDs
    unassigned = [t for t in tasks if not t.due_date]
    assigned = [t for t in tasks if t.due_date]
    all_visible = unassigned + assigned
    
    for task in recurring:
        display_id = all_visible.index(task) + 1 if task in all_visible else "?"
        due_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else "-"
        table.add_row(
            str(display_id),
            task.title,
            get_recurrence_display(task),
            due_str
        )
    
    console.print(table)
    console.print()

@app.command(name="rcdel")
def rc_del(
    task_id: str = typer.Argument(..., help="Task ID to remove from recurring")
):
    """Remove recurrence from a task (keeps the task)."""
    task, all_tasks = resolve_task_target(task_id)
    
    if not task:
        print(f"[red]Task ID {task_id} not found.[/]")
        return
    
    if not task.recurrent:
        print(f"[yellow]Task '{task.title}' is not recurring.[/]")
        return
    
    task.recurrent = False
    task.recurrence_type = None
    task.recurrence_days = None
    task.recurrence_interval = 1
    save_tasks(all_tasks)
    
    print(f"[green]Recurrence removed from '{task.title}'[/]")


@app.command(name="cat")
def categories():
    """Display all available categories."""


    cats = load_categories()
    
    if not cats:
        print("[yellow]No categories defined yet. Use 'TDL add cat <name>' to create one.[/]")
        return
    

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold bright_yellow on black", title="[bold yellow]📁 CATEGORIES[/]")
    table.add_column("ID", width=4, style="bold cyan", justify="center")
    table.add_column("Category Name", style="bold yellow")
    
    for i, cat in enumerate(cats, start=1):
        color = ["red", "orange1", "yellow", "green", "blue", "purple", "violet"][(i-1) % 7]
        table.add_row(
            f"[bold cyan]{i}[/bold cyan]",
            f"[bold {color}]{cat}[/bold {color}]"
        )
    
    console.print(table)

# Modify the add command to handle 'cat' subcommand
@app.command()
def addcat(
    name: str = typer.Argument(..., help="Category name(s) to add"),
    group: bool = typer.Option(False, "--group", "-g", help="Treat input as a single grouped category")
):
    """Add new category(ies). Use -g to create a category group (e.g. 'Work, Study')."""
    cats = load_categories()
    
    # Check for group intent if comma present
    if "," in name and not group:
        # Prompt user logic
        print(f"[yellow]Input contains commas: '{name}'[/]")
        is_group = questionary.confirm(
            "Do you want to create this as a single GROUP category?",
            default=False
        ).ask()
        if is_group:
            group = True

    if group:
        new_cats = [name.strip()] # Create as single entry
    else:
        # Parse comma-separated categories (Original behavior)
        new_cats = [c.strip().capitalize() for c in name.split(',') if c.strip()]
    
    added = []
    skipped = []
    
    for cat in new_cats:
        cat_clean = cat.strip() 
        # Don't capitalize if group? Maybe Capitalize whole string?
        # User might want "Work, Study".
        # Let's capitalize strictly if not group.
        # If group, maybe keep as is or Title Case? 
        # Line 967 used .capitalize().
        
        if not group:
             cat_clean = cat_clean.capitalize()
        
        if cat_clean in cats:
            skipped.append(cat_clean)
        else:
            cats.append(cat_clean)
            added.append(cat_clean)
    
    if added:
        save_categories(cats)
        print(f"[bold green]Added: {', '.join(added)}[/] ✓")
    
    if skipped:
        print(f"[yellow]Already exists: {', '.join(skipped)}[/]")

# Update del to handle both task IDs and category names
@app.command(name="del")
def del_alias(
    identifier: str = typer.Argument(..., help="Task ID (1-10) or category name to delete")
):
    """Delete a task by ID or a category by name."""
    
    # Check if it's a list of IDs (contains comma) or single ID
    is_list = "," in identifier
    parts = identifier.split(',')
    looks_like_ids = all(p.strip().isdigit() or p.strip().startswith("#") for p in parts if p.strip())
    
    if looks_like_ids:
        delete(identifier)
    else:
        # It's a category name - case insensitive search
        cats = load_categories()
        
        # Find matching category (case-insensitive)
        match = None
        for cat in cats:
            if cat.lower() == identifier.lower():
                match = cat
                break
        
        if not match:
            print(f"[red]Category '{identifier}' not found.[/]")
            return
        
        # Confirm deletion
        confirm = questionary.confirm(
            f"Delete category '{match}'?",
            default=False
        ).ask()
        
        if confirm:
            cats.remove(match)
            save_categories(cats)
            print(f"[bold green]Category '{match}' deleted![/] ✓")
        else:
            print("Deletion cancelled.")


@app.command(name="clear")
def clear():
    """Archive all completed tasks to history."""
    tasks = load_tasks()
    completed = [t for t in tasks if t.completed]
    
    if not completed:
        print("[yellow]No completed tasks to clean.[/]")
        return
    
    print(f"[yellow]Found {len(completed)} completed task(s):[/]")
    for t in completed:
        print(f"  - {t.title}")
    
    confirm = questionary.confirm(
        f"Archive all {len(completed)} completed tasks to history?",
        default=False
    ).ask()
    
    if confirm:
        # Add to history
        add_to_history(completed)
        # Remove from active tasks
        tasks = [t for t in tasks if not t.completed]
        save_tasks(tasks)
        print(f"[bold green]{len(completed)} task(s) archived to history![/]")
    else:
        print("[yellow]Cleaning cancelled.[/]")


@app.command(name="clear-all")
def clear_all():
    """Delete ALL tasks, history, and categories. Use with caution!"""
    import os
    import json
    from rich.console import Console
    console = Console()
    
    # Show warning
    console.print("[bold red]⚠️  WARNING ⚠️[/bold red]")
    console.print("[yellow]This will permanently delete:[/yellow]")
    console.print("  • All active tasks")
    console.print("  • All completed tasks in history")
    console.print("  • All categories")
    console.print()
    

    
    # Double confirmation
    confirm1 = questionary.confirm(
        "Are you absolutely sure you want to delete EVERYTHING?",
        default=False
    ).ask()
    
    if not confirm1:
        print("[green]Operation cancelled. Nothing was deleted.[/]")
        return
    
    confirm2 = questionary.text(
        "Type 'DELETE EVERYTHING' to confirm:",
    ).ask()
    
    if not confirm2 or confirm2 != "DELETE EVERYTHING":
        print("[green]Operation cancelled. Nothing was deleted.[/]")
        return
    
    # Delete everything
    try:
        # Clear tasks
        save_tasks([])
        
        # Clear history
        save_history([])
        
        # Clear categories
        save_categories([])

        # Clear goals
        if os.path.exists("goals.json"):
            save_goals([])
            
        # Clear recurrent tasks
        if os.path.exists("recurrent_tasks.json"):
            with open("recurrent_tasks.json", "w") as f:
                json.dump([], f)
        
        # Clear notes
        if os.path.exists("notes.json"):
            save_notes([])
        
        # Clear streak data
        if os.path.exists("streak.json"):
            os.remove("streak.json")

        print("[bold green]✓ All data deleted successfully![/]")
        print("[dim]Your TDL is now completely clean.[/dim]")
    except Exception as e:
        print(f"[red]Error deleting data: {e}[/]")

@app.command()
def hist():
    """Display history of archived completed tasks."""


    history = load_history()
    
    if not history:
        print("[yellow]No tasks in history. Complete some tasks and run 'TDL clear' to archive them.[/]")
        return
    

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold bright_green on black", title="[bold green]✓ COMPLETED TASKS HISTORY[/]")
    table.add_column("ID", width=4, style="bold cyan", justify="center")
    table.add_column("Category", style="bold green")
    table.add_column("Task", style="bold white")
    table.add_column("Due Date", style="bold magenta")
    
    for i, task in enumerate(history, start=1):
        color = ["red", "orange1", "yellow", "green", "blue", "purple", "violet"][(i-1) % 7]
        due = task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A"
        table.add_row(
            f"[bold cyan]{i}[/bold cyan]",
            f"[{color}]{task.category or 'General'}[/{color}]",
            f"[{color}]{task.title}[/{color}]",
            f"[{color}]{due}[/{color}]"
        )
    
    console.print(table)
    print(f"\n[dim]Total: {len(history)} archived tasks[/]")

@app.command(name="info")
def task_info(
    task_id: str = typer.Argument(..., help="Task ID to view details (1-10) or #ID")
):
    """Display detailed information about a task."""
    task, all_tasks = resolve_task_target(task_id)
    
    if not task:
        print(f"[red]Task ID {task_id} not found.[/]")
        return
    
    console = Console()
    
    # Create info panel
    from rich.panel import Panel
    from rich.text import Text
    
    info_text = Text()
    info_text.append(f"Task ID: ", style="bold cyan")
    info_text.append(f"{task.id}\n", style="dim")
    
    info_text.append(f"Title: ", style="bold cyan")
    info_text.append(f"{task.title}\n", style="bold white")
    
    info_text.append(f"Category: ", style="bold cyan")
    info_text.append(f"{task.category or 'None'}\n", style="yellow")
    
    info_text.append(f"Due Date: ", style="bold cyan")
    if task.due_date:
        info_text.append(f"{task.due_date.strftime('%Y-%m-%d %H:%M')}\n", style="magenta")
    else:
        info_text.append("Not set\n", style="dim")
    
    info_text.append(f"Duration: ", style="bold cyan")
    if task.time_duration:
        info_text.append(f"{task.get_duration_str()}\n", style="green")
    else:
        info_text.append("Not set\n", style="dim")
    
    info_text.append(f"Status: ", style="bold cyan")
    if task.completed:
        info_text.append("✓ Completed\n", style="bold green")
    else:
        info_text.append("○ Pending\n", style="yellow")
    
    info_text.append(f"Priority: ", style="bold cyan")
    priority_names = {-1: "Unimportant", 0: "Normal", 1: "🚩 IMPORTANT"}
    priority_colors = {-1: "dim", 0: "white", 1: "bold red"}
    priority_value = task.priority if hasattr(task, 'priority') else (1 if getattr(task, 'important', False) else 0)
    info_text.append(priority_names.get(priority_value, "Normal") + "\n", style=priority_colors.get(priority_value, "white"))
    
    # Recurrence info
    if getattr(task, 'recurrent', False):
        info_text.append(f"\n🔁 Recurring: ", style="bold magenta")
        info_text.append(f"{get_recurrence_display(task)}\n", style="magenta")
        if task.recurrence_days:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            days = ", ".join([day_names[d] for d in task.recurrence_days])
            info_text.append(f"   Days: ", style="bold cyan")
            info_text.append(f"{days}\n", style="white")
    
    title_style = "bold red" if priority_value == 1 else "bold blue"
    panel = Panel(info_text, title=f"[{title_style}]Task #{task_id} Details[/]", border_style="blue", padding=(1, 2))
    console.print(panel)


@app.command()
def work(
    task_id: str = typer.Argument(..., help="Task ID to enter deep work mode (1-10)")
):
    """Enter deep work mode for a task."""
    task, all_tasks = resolve_task_target(task_id)
    
    if not task:
        print(f"[red]Task ID {task_id} not found.[/]")
        return
    
    # Confirm entry into deep work mode
    print(f"[bold cyan]Task:[/] {task.title}")
    if task.time_duration:
        duration_str = task.get_duration_str()
        print(f"[bold green]Duration:[/] {duration_str}")
    else:
        print(f"[yellow]No duration set for this task.[/]")
    
    confirm = questionary.confirm(
        "Enter deep work mode?",
        default=True
    ).ask()
    
    if not confirm:
        print("[yellow]Deep work mode cancelled.[/]")
        return
    
    # Check for duration
    duration_seconds = task.time_duration
    if not duration_seconds:
        print("[yellow]Please set a duration for this task.[/]")
        time_str = questionary.text("Duration (e.g. '2h', '45m', '1h30m'):").ask()
        
        if not time_str:
            print("[red]Deep work mode cancelled.[/]")
            return
        
        duration_seconds = parse_duration(time_str)
        if duration_seconds is None:
            print(f"[red]Invalid duration format: {time_str}[/]")
            return
        
        # Save duration to task
        task.time_duration = duration_seconds
        save_tasks(all_tasks)
        print(f"[green]Duration set to: {task.get_duration_str()}[/]")
    
    # Launch deep work GUI
    print(f"[bold green]🚀 Launching deep work mode...[/]")
    
    gif_path = "f:/App/Anti-gravity/CLI TDL/ascii-animation.gif"
    
    try:
        from deep_work import start_deep_work
        task_completed, task_dismissed, saved_remaining = start_deep_work(task.title, duration_seconds, gif_path)
        
        # Mark task complete if user chose to complete it
        if task_completed:
            task.completed = True
            save_tasks(all_tasks)
            print(f"[bold green]✓ Task '{task.title}' completed![/]")
        elif task_dismissed:
            print(f"[yellow]Deep work session dismissed.[/]")
        elif saved_remaining is not None:
            # Update task duration with remaining time
            task.time_duration = saved_remaining
            save_tasks(all_tasks)
            print(f"[cyan]Progress saved! Remaining time: {task.get_duration_str()}[/]")
        else:
            print(f"[yellow]Deep work session ended.[/]")
        
    except Exception as e:
        print(f"[red]Error launching deep work mode: {e}[/]")


# --- GOAL CHECKLIST FEATURE ---

def get_goal_by_display_id(display_id: int):
    """Helper to get a goal by its display ID (1-based index)."""
    goals = load_goals()
    # Sort same as display: Incomplete first, then by creation date
    sorted_goals = sorted(goals, key=lambda g: (g.completed, g.created_date))
    
    if 1 <= display_id <= len(sorted_goals):
        return sorted_goals[display_id - 1], goals
    return None, goals

@app.command(name="goal")
def goal_view():
    """View the Goal Checklist notebook."""
    goals = load_goals()
    ui.render_goals(goals)

@app.command(name="goaladd")
def goal_add(
    name: List[str] = typer.Argument(..., help="The goal description")
):
    """Add a new goal to the checklist."""
    title = " ".join(name)
    goals = load_goals()
    
    new_goal = Goal(title=title)
    goals.append(new_goal)
    save_goals(goals)
    
    print(f"[bold green]Goal added![/] 🎯 [dim]{new_goal.title}[/]")

@app.command(name="goalcheck")
def goal_check(
    goal_id: int = typer.Argument(..., help="Goal display ID to check/uncheck")
):
    """Toggle completion status of a goal."""
    goal, all_goals = get_goal_by_display_id(goal_id)
    
    if not goal:
        print(f"[red]Goal ID {goal_id} not found.[/]")
        return
        
    # Toggle status
    goal.completed = not goal.completed
    if goal.completed:
        goal.completed_date = datetime.now()
        print(f"[bold green]Goal checked![/] ✓ [dim]{goal.title}[/]")
    else:
        goal.completed_date = None
        print(f"[bold yellow]Goal unchecked.[/] [dim]{goal.title}[/]")
        
    save_goals(all_goals)

@app.command(name="goaldel")
def goal_del(
    goal_id: int = typer.Argument(..., help="Goal display ID to delete")
):
    """Delete a goal."""
    # ... existing implementation

@app.command(name="dump")
def dump(
    content: List[str] = typer.Argument(None, help="The note content (optional). If empty, shows all notes.")
):
    """Quickly dump a note or view all notes."""
    notes = load_notes()
    
    # If no content provided, show notes
    if not content:
        ui.render_notes(notes)
        return
        
    # Combined content
    
    # Check if user meant "dump del <ids>"
    if len(content) >= 2 and content[0].lower() == "del":
        # Pass the rest of the arguments as a single string (e.g., "1,2,3" or "1 2 3")
        # Handle cases like "del 1,2" (len=2, content[1]="1,2") or "del 1 2" (len=3)
        ids_str = "".join(content[1:])
        dump_del(ids_str)
        return

    # Combine content into one string
    text = " ".join(content)
    
    new_note = Note(content=text)
    notes.append(new_note)
    save_notes(notes)
    
    print(f"[bold green]Note dumped![/] 🧠 [dim]#{new_note.id}[/]")

@app.command(name="dump_del")
def dump_del(
    note_ids_str: str = typer.Argument(..., help="Note ID(s) to delete (comma separated, e.g., 1,2,3)")
):
    """Delete note(s) by ID (supports multiple like 1,2,3)."""
    notes = load_notes()
    
    # Parse IDs
    try:
        # Handle commas and spaces
        cleaned = note_ids_str.replace(",", " ")
        target_ids = [int(x) for x in cleaned.split() if x.isdigit()]
    except ValueError:
        print("[red]Invalid format. Use IDs like 1,2,3[/]")
        return

    if not target_ids:
        print("[red]No valid IDs found.[/]")
        return
        
    # Find matching notes
    to_delete = [n for n in notes if n.id in target_ids]
    
    if not to_delete:
        print(f"[red]No notes found with IDs: {target_ids}[/]")
        return
        
    confirm = questionary.confirm(
        f"Delete {len(to_delete)} note(s)? (IDs: {', '.join(map(str, target_ids))})",
        default=False
    ).ask()
    
    if confirm:
        for note in to_delete:
            notes.remove(note)
        save_notes(notes)
        print(f"[bold red]{len(to_delete)} note(s) deleted![/] 🗑️")
    else:
        print("[yellow]Deletion cancelled.[/]")

@app.command(name="goaldel")
def goal_del(
    goal_id: int = typer.Argument(..., help="Goal display ID to delete")
):
    """Delete a goal."""
    goal, all_goals = get_goal_by_display_id(goal_id)
    
    if not goal:
        print(f"[red]Goal ID {goal_id} not found.[/]")
        return
        
    confirm = questionary.confirm(
        f"Delete goal '{goal.title}'?",
        default=False
    ).ask()
    
    if confirm:
        # We need to remove the exact goal instance from all_goals list
        # Since 'goal' ref came from a sorted list, we need to find it in all_goals by ID
        target = next((g for g in all_goals if g.id == goal.id), None)
        if target:
            all_goals.remove(target)
            save_goals(all_goals)
            print(f"[bold red]Goal deleted![/] 🗑️")
    else:
        print("[yellow]Deletion cancelled.[/]")



# --- TEMPLATE SYSTEM ---

@app.command(name="template")
def template_cmd(
    title: List[str] = typer.Argument(None, help="Template title (leave empty to list templates)"),
    alias: Optional[str] = typer.Option(None, "-a", help="Alias/shortname for the template"),
    category: Optional[str] = typer.Option(None, "-c", help="Category for the template"),
    due: Optional[str] = typer.Option(None, "-d", help="Due date offset (e.g. 'today', 'tomorrow', '+2d')"),
    time: Optional[str] = typer.Option(None, "-t", help="Time duration (e.g. '2h30m', '45m')"),
    flag: Optional[int] = typer.Option(None, "-f", "--flag", help="Set priority: -1=unimportant, 0=normal, 1=important"),
    rc: bool = typer.Option(False, "-r", "--rc", help="Make this a recurring template")
):
    """Create a new task template or list all templates."""
    templates = load_templates()
    
    # If no title provided, list all templates
    if not title:
        if not templates:
            print("[yellow]No templates found. Create one with 'TDL template <title> -a <alias>'[/]")
            return
        
        console.print("\n[bold magenta]📋 TASK TEMPLATES[/bold magenta]\n")
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Alias", width=15, style="bold cyan")
        table.add_column("Title", style="white")
        table.add_column("Category", style="yellow")
        table.add_column("Due", style="green")
        table.add_column("Duration", style="blue")
        table.add_column("Priority", style="red")
        
        for template in templates:
            cat_str = ", ".join(template.category) if template.category else "-"
            due_str = template.due_date_offset or "-"
            
            # Format duration
            if template.time_duration:
                hours = template.time_duration // 3600
                minutes = (template.time_duration % 3600) // 60
                parts = []
                if hours > 0:
                    parts.append(f"{hours}h")
                if minutes > 0:
                    parts.append(f"{minutes}m")
                duration_str = "".join(parts) if parts else "-"
            else:
                duration_str = "-"
            
            priority_names = {-1: "Low", 0: "Normal", 1: "HIGH"}
            priority_str = priority_names.get(template.priority, "Normal")
            if template.recurrent:
                priority_str += " 🔁"
            
            table.add_row(
                f"*{template.alias}",
                template.title,
                cat_str,
                due_str,
                duration_str,
                priority_str
            )
        
        console.print(table)
        console.print(f"\n[dim]Use with: TDL add *alias[/dim]")
        console.print(f"[dim]Example: TDL add *{templates[0].alias if templates else 'workout'}[/dim]\n")
        return
    
    # Create new template
    if not alias:
        print("[red]Alias is required. Use -a flag to set an alias.[/]")
        print("[dim]Example: TDL template 'Daily Standup' -a standup -d today -t 15m[/dim]")
        return
    
    # Check if alias already exists
    existing = get_template_by_alias(alias)
    if existing:
        print(f"[red]Template with alias '{alias}' already exists. Delete it first or use a different alias.[/]")
        return
    
    template_title = " ".join(title)
    
    # Parse categories
    parsed_categories = None
    if category:
        categories_list = [c.strip().capitalize() for c in category.split(',') if c.strip()]
        parsed_categories = categories_list if categories_list else None
    
    # Parse time duration
    duration_seconds = None
    if time:
        duration_seconds = parse_duration(time)
        if duration_seconds is None:
            print(f"[red]Invalid duration format: {time}. Use format like '2h30m15s'[/]")
            return
    
    # Set priority
    priority = 0
    if flag is not None:
        if flag not in [-1, 0, 1]:
            print(f"[red]Invalid priority: {flag}. Use -1 (unimportant), 0 (normal), or 1 (important)[/]")
            return
        priority = flag
    
    # Handle recurrence
    recurrence_type = None
    recurrence_days = None
    recurrence_interval = 1
    
    if rc:
        recurrence_type, recurrence_days, recurrence_interval = configure_recurrence()
        if recurrence_type is None:
            print("[yellow]Recurrence setup cancelled.[/]")
            rc = False
    
    # Create template
    new_template = Template(
        alias=alias,
        title=template_title,
        category=parsed_categories,
        due_date_offset=due,
        time_duration=duration_seconds,
        priority=priority,
        recurrent=rc,
        recurrence_type=recurrence_type,
        recurrence_days=recurrence_days,
        recurrence_interval=recurrence_interval
    )
    
    templates.append(new_template)
    save_templates(templates)
    
    print(f"[bold green]Template created![/] ✓")
    print(f"[cyan]Alias:[/] *{alias}")
    print(f"[dim]Use with: TDL add *{alias}[/dim]")

@app.command(name="templatedel")
def template_del(
    alias: str = typer.Argument(..., help="Template alias to delete")
):
    """Delete a template by its alias."""
    templates = load_templates()
    
    # Remove * prefix if provided
    if alias.startswith("*"):
        alias = alias[1:]
    
    template = get_template_by_alias(alias)
    
    if not template:
        print(f"[red]Template '{alias}' not found.[/]")
        return
    
    confirm = questionary.confirm(
        f"Delete template '*{alias}' ({template.title})?",
        default=False
    ).ask()
    
    if confirm:
        templates = [t for t in templates if t.alias.lower() != alias.lower()]
        save_templates(templates)
        print(f"[bold red]Template '*{alias}' deleted![/] 🗑️")
    else:
        print("[yellow]Deletion cancelled.[/]")



@app.command(name="welcome")
@app.command(name="home")
@app.command(name="main")
def welcome():
    """Show welcome screen with available commands."""
    ui.print_welcome_screen()

@app.command(name="intro")
def intro():
    """Show introduction, usage, features, and motivation behind TDL."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.console import Group
    from rich.text import Text
    from rich import box
    from rich.align import Align
    
    theme = ui.get_current_theme()
    
    # -- Header Section --
    header = Text()
    header.append("🚀 Welcome to TDL (Terminal Task Manager)\n\n", style=f"bold {theme['primary']}")
    header.append("🎯 What is TDL?\n", style=f"bold {theme['secondary']}")
    header.append("TDL is a lightning-fast, keyboard-centric task manager built specifically for the command line interface. It is designed to be lightweight, beautiful, and highly efficient, keeping you laser-focused on what truly matters. By eliminating the bloat of traditional GUI applications, TDL ensures that managing your tasks feels like a natural extension of your terminal workflow.\n", style="white")
    
    # -- Motivation Section --
    motivation_text = (
        "I was struggling with keeping track of my work, constantly switching between heavy applications that slowed down my workflow. "
        "I wanted something that could handle time management effectively directly on my laptop, "
        "without any lag or distractions. TDL was born out of the need for a tool that is as fast as thought, "
        "providing a smooth, efficient, and visually pleasing experience for developers and power users."
    )
    motivation_panel = Panel(
        Text(motivation_text, style="italic white"),
        title=f"[bold {theme['warning']}]💡 Why TDL?[/]",
        border_style=theme["secondary"],
        padding=(1, 2)
    )

    # -- Features Section (Table) --
    feature_table = Table(box=None, expand=True, show_header=False, padding=(0, 2))
    feature_table.add_column("Icon", style="bold", width=4)
    feature_table.add_column("Description", style="white")
    
    features = [
        ("🌈", f"[bold {theme['rainbow_colors'][0]}]Rainbow Dashboard[/]: Visualize all your tasks at a glance with a vibrant, auto-organized dashboard that groups items by timeline (Today, Tomorrow, Upcoming)."),
        ("🔁", f"[bold {theme['rainbow_colors'][1]}]Recurrent Tasks[/]: Automate your routine. Easily configure tasks to repeat daily, weekly, on specific weekdays, or on custom schedules so you never miss a beat."),
        ("⏱️", f"[bold {theme['rainbow_colors'][2]}]Deep Work Mode[/]: Enter a distraction-free zone for single-tasking. Features a dedicated timer, visual progress bar, and completion tracking to boost your productivity."),
        ("🗂️", f"[bold {theme['rainbow_colors'][3]}]Advanced Organization[/]: Keep everything structured with custom categories, comprehensive history tracking, and a dedicated goal setting notebook."),
        ("⚡", f"[bold {theme['rainbow_colors'][4]}]Blazing Speed[/]: Built for instant startup and immediate command execution. No loading screens, no waiting—just efficiency.")
    ]
    
    for icon, desc in features:
        feature_table.add_row(icon, desc)
        import time 
        # Adding a small row for spacing
        feature_table.add_row("", "")

    # -- Usage Section (Table) --
    usage_table = Table(box=None, expand=True, show_header=False, padding=(0, 2))
    usage_table.add_column("Command", style=f"bold {theme['success']}", width=25)
    usage_table.add_column("Action", style="dim white")
    
    commands = [
        ("TDL db", "View your main Dashboard"),
        ("TDL add \"Task Name\"", "Quickly add a new task"),
        ("TDL add \"Task\" -r", "Add a recurring task (interactive setup)"),
        ("TDL work <ID>", "Start a Deep Work focus session"),
        ("TDL check", "Open the interactive checklist to complete tasks"),
        ("TDL rc", "Manage your recurring tasks"),
        ("TDL info <ID>", "View detailed task information")
    ]
    
    for cmd, act in commands:
        usage_table.add_row(cmd, act)

    # -- Assemble Content --
    content_group = Group(
        header,
        Text("\n"),
        motivation_panel,
        Text("\n✨ Key Features\n", style=f"bold {theme['warning']}"),
        feature_table,
        Text("\n⌨️  Quick Usage Guide\n", style=f"bold {theme['primary']}"),
        usage_table
    )
    
    console.print()
    console.print(Panel(
        content_group,
        title=f"[bold {theme['primary']}]About TDL[/]",
        border_style=theme["secondary"],
        padding=(1, 2),
        box=box.ROUNDED,
        expand=False # Disable expand to avoid forcing width calculation issues
    ))
    console.print()

@app.command(name="stat")
def statistics():
    """Display task completion statistics."""
    from stat_command import stat
    stat()

@app.command(name="settings")
@app.command(name="st", hidden=True)
def settings():
    """Configure TDL settings and view information."""
    from rich.panel import Panel
    from rich.text import Text
    from rich.console import Console
    
    console = Console()
    
    while True:
        # Clear screen for a clean menu
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        theme = ui.get_current_theme()
        
        # Settings Header
        header = Text()
        header.append("⚙️  SETTINGS", style=f"bold {theme['primary']}")
        console.print(Panel(header, border_style=theme["primary"], padding=(0, 2)))
        console.print()
        
        choices = [
            "🎨 Change Theme",
            "📊 Toggle Activity Heatmap",
            "� Toggle Streak Display",
            "�📖 View Manual",
            "🗑️  Reset All Data",
            "ℹ️  About Developer",
            "🚪 Exit Settings"
        ]
        
        action = questionary.select(
            "Select an option:",
            choices=choices,
            style=questionary.Style([
                ('pointer', f'fg:{theme["primary"]} bold'),
                ('highlighted', f'fg:{theme["primary"]} bold'),
                ('selected', 'fg:white'),
            ])
        ).ask()
        
        if not action or "Exit" in action:
            break
            
        if "Change Theme" in action:
            theme_choices = ["Rainbow", "Dark", "Neon", "Pastel"]
            current = get_theme().capitalize()
            
            new_theme = questionary.select(
                "Choose a theme:",
                choices=theme_choices,
                default=current
            ).ask()
            
            if new_theme:
                config = load_config()
                config["theme"] = new_theme.lower()
                save_config(config)
                print(f"[bold green]Theme updated to {new_theme}![/]")
                import time
                time.sleep(1)
        
        elif "Toggle Streak" in action:
            config = load_config()
            current_state = config.get("show_streak", True)
            
            toggle_choice = questionary.confirm(
                f"Show streak icon? (Currently: {'ON' if current_state else 'OFF'})",
                default=current_state
            ).ask()
            
            if toggle_choice is not None:
                config["show_streak"] = toggle_choice
                save_config(config)
                status = "enabled" if toggle_choice else "disabled"
                print(f"[bold green]Streak display {status}![/]")
                import time
                time.sleep(1)

        elif "Toggle Activity Heatmap" in action:
            config = load_config()
            current_state = config.get("show_heatmap", True)
            
            toggle_choice = questionary.confirm(
                f"Show activity heatmap? (Currently: {'ON' if current_state else 'OFF'})",
                default=current_state
            ).ask()
            
            if toggle_choice is not None:
                config["show_heatmap"] = toggle_choice
                save_config(config)
                status = "enabled" if toggle_choice else "disabled"
                print(f"[bold green]Heatmap {status}![/]")
                import time
                time.sleep(1)
        
        elif "View Manual" in action:
            welcome()
            print("\n[dim]Press Enter to return to settings...[/dim]")
            input()
            
        elif "Reset All Data" in action:
            clear_all()
            print("\n[dim]Press Enter to return to settings...[/dim]")
            input()
            
        elif "About" in action:
            dev_info = Text()
            dev_info.append("Developer: ", style=f"bold {theme['primary']}")
            dev_info.append("LucasDoCoding\n", style="white")
            dev_info.append("Contact:   ", style=f"bold {theme['primary']}")
            dev_info.append("huylostnickagain@gmail.com\n", style="white")
            dev_info.append("\nThank you for using TDL! 🚀", style="italic")
            
            panel = Panel(
                dev_info,
                title="[bold white]Developer Information[/bold white]",
                border_style=theme["secondary"],
                padding=(1, 2)
            )
            console.print(panel)
            print("\n[dim]Press Enter to return to settings...[/dim]")
            input()








if __name__ == "__main__":
    import sys
    # If no arguments provided, launch REPL interactive mode
    if len(sys.argv) == 1:
        from repl import run_repl
        run_repl()
        sys.exit(0)
    
    # Handle shortcut: if first arg is a digit or #ID, insert 'update' command
    elif sys.argv[1].isdigit() or sys.argv[1].startswith("#"):
        sys.argv.insert(1, "update")
        
    # Handle 'add cat' shortcut
    elif len(sys.argv) >= 3 and sys.argv[1] == "add" and sys.argv[2] == "cat":
        sys.argv[1] = "addcat"
        sys.argv.pop(2)
    
    # Handle 'cat add' shortcut (alternative syntax)
    elif len(sys.argv) >= 3 and sys.argv[1] == "cat" and sys.argv[2] == "add":
        sys.argv[1] = "addcat"
        sys.argv.pop(2)
        
    # Handle 'goal' shortcuts
    elif len(sys.argv) >= 2 and sys.argv[1] == "goal":
        # TDL goal add ...
        if len(sys.argv) >= 3:
            sub = sys.argv[2]
            if sub == "add":
                sys.argv[1] = "goaladd"
                sys.argv.pop(2)
            elif sub == "check":
                sys.argv[1] = "goalcheck"
                sys.argv.pop(2)
            elif sub == "del":
                sys.argv[1] = "goaldel"
                sys.argv.pop(2)
    
    # Handle 'rc del' shortcut
    elif len(sys.argv) >= 3 and sys.argv[1] == "rc" and sys.argv[2] == "del":
        sys.argv[1] = "rcdel"
        sys.argv.pop(2)
    
    # Handle 'template del' shortcut
    elif len(sys.argv) >= 3 and sys.argv[1] == "template" and sys.argv[2] == "del":
        sys.argv[1] = "templatedel"
        sys.argv.pop(2)
        
    # Handle '?' shortcut for intro
    elif len(sys.argv) > 1 and sys.argv[1] == "?":
        sys.argv[1] = "intro"
    
    app()
