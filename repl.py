"""
TDL Interactive REPL (Read-Eval-Print Loop)
============================================
Provides an interactive shell experience for TDL.
Type 'TDL' to enter, then use commands directly without the 'TDL' prefix.
"""

import sys
import os
import subprocess
import shlex
from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text
from rich.panel import Panel

console = Console()

# Import theme
try:
    import ui
    from config_storage import get_theme
except ImportError:
    ui = None
    get_theme = lambda: "rainbow"


def get_prompt_style():
    """Get styled prompt based on current theme."""
    if ui:
        theme = ui.get_current_theme()
        return f"[bold {theme['primary']}]TDL[/bold {theme['primary']}] [dim]>[/dim] "
    return "[bold cyan]TDL[/bold cyan] [dim]>[/dim] "


def print_ascii_header():
    """Print the TDL MANAGER ASCII art header."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if ui:
        theme = ui.get_current_theme()
        rainbow_colors = theme.get("rainbow_colors", ["cyan", "magenta", "green", "yellow", "blue", "red"])
    else:
        rainbow_colors = ["cyan", "magenta", "green", "yellow", "blue", "red"]
    
    title_lines = [
        "████████╗██████╗ ██╗         ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ ",
        "╚══██╔══╝██╔══██╗██║         ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗",
        "   ██║   ██║  ██║██║         ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝",
        "   ██║   ██║  ██║██║         ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗",
        "   ██║   ██████╔╝███████╗    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║",
        "   ╚═╝   ╚═════╝ ╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝"
    ]
    
    for i, line in enumerate(title_lines):
        console.print(line, style=f"bold {rainbow_colors[i % len(rainbow_colors)]}")
    console.print()


def show_repl_welcome():
    """Show welcome message for REPL mode."""
    print_ascii_header()
    
    if ui:
        theme = ui.get_current_theme()
    else:
        theme = {"primary": "cyan", "secondary": "magenta", "success": "green"}
    
    console.print(f"[dim]Type commands directly (e.g., 'db', 'add \"Task\"', 'cat')[/dim]")
    console.print(f"[dim]Type 'help' for available commands, 'exit' or 'q' to quit[/dim]")
    console.print()


def show_quick_help():
    """Show quick command reference."""
    help_text = """
[bold cyan]Quick Commands:[/bold cyan]
  [green]db[/green]              - View all tasks (dashboard)
  [green]add "Task"[/green]      - Add a new task
  [green]add "Task" -c 1[/green] - Add task with category #1
  [green]check[/green]           - Mark tasks complete
  [green]1 -c 2[/green]          - Update task #1 with category #2
  [green]del 1[/green]           - Delete task #1
  [green]cat[/green]             - List categories
  [green]cat add "Work"[/green]  - Add category
  [green]calendar[/green]        - View calendar
  [green]stat[/green]            - View statistics
  [green]settings[/green]        - App settings
  [green]welcome[/green]         - Show full help
  [green]clear[/green]            - Archive completed tasks
  [green]cls[/green]              - Clear screen
  [green]exit[/green] / [green]q[/green]         - Exit REPL
"""
    console.print(help_text)


def execute_command(cmd_line: str) -> bool:
    """
    Execute a TDL command.
    Returns False if should exit REPL, True to continue.
    """
    cmd_line = cmd_line.strip()
    
    if not cmd_line:
        return True
    
    # Handle REPL-specific commands
    lower_cmd = cmd_line.lower()
    
    if lower_cmd in ['exit', 'quit', 'q', ':q', ':q!']:
        console.print("[dim]Goodbye! 👋[/dim]")
        return False
    
    if lower_cmd in ['cls']:
        os.system('cls' if os.name == 'nt' else 'clear')
        return True
    
    if lower_cmd in ['help', '?', 'h']:
        show_quick_help()
        return True
    
    if lower_cmd == 'welcome':
        # Run welcome command
        try:
            subprocess.run([sys.executable, 'main.py', 'welcome'], 
                          cwd=os.path.dirname(os.path.abspath(__file__)) or '.')
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        return True
    
    # Parse command and execute via main.py
    try:
        # Split command line respecting quotes
        parts = shlex.split(cmd_line)
        
        if not parts:
            return True
        
        # Build full command
        script_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
        full_cmd = [sys.executable, os.path.join(script_dir, 'main.py')] + parts
        
        # Execute
        result = subprocess.run(full_cmd, cwd=script_dir)
        
        # Add spacing after command output
        console.print()
        
    except ValueError as e:
        console.print(f"[red]Invalid command syntax: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error executing command: {e}[/red]")
    
    return True


def run_repl():
    """Main REPL loop."""
    # Show initial welcome with ASCII header
    show_repl_welcome()
    
    # Main loop
    while True:
        try:
            # Get prompt
            prompt_text = get_prompt_style()
            
            # Read input
            cmd = Prompt.ask(prompt_text)
            
            # Execute
            if not execute_command(cmd):
                break
                
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' or 'q' to quit[/dim]")
        except EOFError:
            console.print("\n[dim]Goodbye! 👋[/dim]")
            break


if __name__ == "__main__":
    run_repl()
