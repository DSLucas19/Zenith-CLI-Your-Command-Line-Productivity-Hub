"""
Deep Work Terminal Mode - Always-on-top terminal-based focus timer.

This module spawns a new terminal window with the deep work session,
sets it to always-on-top, and provides a Rich-based timer UI.
"""
import subprocess
import sys
import os
import ctypes
import time
import json
import tempfile
from pathlib import Path

# Windows notification support
try:
    from win11toast import toast
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Status codes for return values
STATUS_COMPLETED = 0
STATUS_DISMISSED = 1
STATUS_SAVED = 2
STATUS_CANCELLED = 3


def set_window_always_on_top():
    """Set the current console window to always stay on top (Windows only)."""
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get console window handle
        hwnd = kernel32.GetConsoleWindow()
        
        if hwnd:
            # Constants for SetWindowPos
            HWND_TOPMOST = -1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            
            # Set window to topmost
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            return True
    except Exception:
        pass
    return False


def bring_window_to_foreground():
    """Bring the console window to the foreground and focus it."""
    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            # Constants
            SW_RESTORE = 9
            
            # Restore window if minimized
            user32.ShowWindow(hwnd, SW_RESTORE)
            
            # Bring to foreground
            user32.SetForegroundWindow(hwnd)
            
            # Flash the window to get attention
            user32.FlashWindow(hwnd, True)
            return True
    except Exception:
        pass
    return False


def send_completion_notification(task_title, elapsed_seconds):
    """Send a Windows toast notification when the session completes."""
    # Always bring window to foreground first (most reliable action)
    bring_window_to_foreground()
    
    try:
        # Format duration
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        
        if hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m"
        
        # Truncate long task titles
        display_title = task_title[:50] + "..." if len(task_title) > 50 else task_title
        
        if NOTIFICATIONS_AVAILABLE:
            try:
                # Send Windows toast notification
                # Wrapped in separate try-except due to win11toast library bugs
                toast(
                    "Deep Work Session Complete! 🎉",
                    f"{display_title}\n\nTime worked: {duration_str}",
                    duration="short",
                    on_click=None
                )
            except Exception:
                # win11toast library has known bugs with click handlers
                # Silently ignore notification errors
                pass
        
    except Exception:
        # Any other errors in notification preparation
        pass


def set_console_size(width, height):
    """Set console window size."""
    try:
        os.system(f'mode con: cols={width} lines={height}')
    except Exception:
        pass


def check_key_press():
    """Check for key press using msvcrt (Windows built-in, no admin needed)."""
    import msvcrt
    if msvcrt.kbhit():
        key = msvcrt.getch()
        # Handle special keys (arrow keys, etc.)
        if key == b'\xe0' or key == b'\x00':
            msvcrt.getch()  # Consume the second byte
            return None
        return key.decode('utf-8', errors='ignore').lower()
    return None


def run_deep_work_session(task_title, duration_seconds, result_file):
    """Run the deep work session in the current terminal."""
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    
    console = Console()
    
    # Set window always on top (Reinforced)
    if set_window_always_on_top():
        # Get screen dimensions
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        # Target size
        width = 450
        height = 180
        
        # Calculate position (Bottom Right with padding)
        x = screen_width - width - 20
        y = screen_height - height - 60  # Account for taskbar
        
        # Move window
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        user32.MoveWindow(hwnd, x, y, width, height, True)
    
    # Set smaller console grid
    set_console_size(50, 11)
    
    # Timer state
    remaining_seconds = duration_seconds
    total_seconds = duration_seconds
    elapsed_seconds = 0
    is_paused = False
    session_result = {"status": "cancelled", "remaining": None}
    
    def format_time(seconds):
        """Format seconds as HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def create_display():
        """Create the deep work display panel."""
        nonlocal is_paused, elapsed_seconds, total_seconds, remaining_seconds
        
        # Calculate progress
        if total_seconds > 0:
            progress_percent = int((elapsed_seconds / total_seconds) * 100)
        else:
            progress_percent = 0
        
        # Create progress bar
        bar_length = 20
        filled = int((progress_percent / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Status indicator
        status_text = "[bold yellow]⏸ PAUSED[/]" if is_paused else "[bold green]▶ RUNNING[/]"
        
        # Build display content
        content = Text(justify="center")
        
        # Task title (compact)
        display_title = task_title[:30] + "..." if len(task_title) > 30 else task_title
        content.append(f"📋 {display_title}\n", style="bold cyan")
        
        # Timer (large display, essentially the main focus)
        content.append(f"\n{format_time(remaining_seconds)}\n\n", style="bold white on black")
        
        # Progress bar
        content.append(f"[{bar}] {progress_percent}%\n", style="bold blue")
        
        # Help text (inside panel)
        content.append("\nSPACE: Pause | Q: Quit", style="dim italic")
        
        panel = Panel(
            content,
            title="[bold magenta]⏱ DEEP WORK[/]",
            subtitle=status_text,
            border_style="magenta",
            padding=(0, 1)
        )
        return panel
    
    def show_completion_screen():
        """Show the completion screen with options."""
        nonlocal session_result
        
        console.clear()
        
        # Simple Completion Header
        console.print("\n[bold green]🎉 SESSION COMPLETE! 🎉[/]", justify="center")
        console.print(f"[dim]{task_title[:40]}[/]", justify="center")
        console.print(f"[bold white]Worked: {format_time(elapsed_seconds)}[/]\n", justify="center")
        
        console.print("[1] Verify  [2] Extend  [3] Dismiss", justify="center", style="bold")
        
        while True:
            try:
                choice = input("Select option (1-3): ").strip()
                
                if choice == "1":
                    session_result = {"status": "completed", "remaining": None}
                    console.print("\n[bold green]✓ Task marked as complete![/]")
                    time.sleep(1)
                    return
                    
                elif choice == "2":
                    # Extend by 5 minutes
                    session_result = {"status": "extended", "remaining": 300}
                    return "extend"
                    
                elif choice == "3":
                    session_result = {"status": "dismissed", "remaining": None}
                    console.print("\n[yellow]Session dismissed.[/]")
                    time.sleep(1)
                    return
                    
            except (KeyboardInterrupt, EOFError):
                session_result = {"status": "dismissed", "remaining": None}
                return
    
    def show_extend_screen():
        """Show screen to extend the timer."""
        nonlocal remaining_seconds, total_seconds, elapsed_seconds, is_paused
        
        console.clear()
        # Compact Extend Screen
        console.print("\n[bold blue]⏱ EXTEND TIME[/]", justify="center")
        console.print("[dim]Add time:[/dim] [cyan][1] 5m  [2] 15m  [3] 30m[/cyan]", justify="center")
        console.print("[dim]Or:[/dim]       [cyan][4] Custom[/cyan]   [red][0] Cancel[/red]", justify="center")
        
        choice = input("Option: ").strip()
        
        extend_seconds = 0
        if choice == "1":
            extend_seconds = 5 * 60
        elif choice == "2":
            extend_seconds = 15 * 60
        elif choice == "3":
            extend_seconds = 30 * 60
        elif choice == "4":
            time_str = input("Enter time (e.g. '10m', '1h'): ").strip()
            extend_seconds = parse_duration(time_str)
        elif choice == "0":
            return 0
        
        if extend_seconds > 0:
            # Reset timer with new duration
            remaining_seconds = extend_seconds
            total_seconds = extend_seconds
            elapsed_seconds = 0
            is_paused = False
            return extend_seconds
        
        return 0
    
    def parse_duration(time_str):
        """Parse duration string like '1h30m' to seconds."""
        import re
        pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
        match = re.fullmatch(pattern, time_str.lower())
        
        if match and any(match.groups()):
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    
    # Main timer loop
    console.clear()
    # Removed separate headers to prevent scrolling in compact window
    
    try:
        with Live(create_display(), console=console, refresh_per_second=2, transient=True) as live:
            last_update = time.time()
            
            while remaining_seconds > 0:
                current_time = time.time()
                
                # Check for key presses using msvcrt
                key = check_key_press()
                if key == ' ':
                    is_paused = not is_paused
                    time.sleep(0.2)  # Debounce
                elif key == 'q':
                    # Ask about what to do with progress
                    live.stop()
                    
                    # Clear any pending input from the buffer
                    import msvcrt
                    while msvcrt.kbhit():
                        msvcrt.getch()
                    
                    # Small delay to ensure console is ready
                    time.sleep(0.3)
                    
                    # Always show interrupt menu
                    console.print("\n[bold yellow]⏸ INTERRUPTED[/]")
                    if elapsed_seconds > 0:
                        console.print(f"[dim]Worked: {format_time(elapsed_seconds)}[/]")
                    console.print("[1] Save progress")
                    console.print("[2] Quit (discard)")
                    console.print("[3] Resume")
                    
                    try:
                        choice = input("Option (1-3, default=3): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        choice = '3'  # Default to resume on error
                    
                    if choice == '1':
                        # Save progress - remaining time will be the new duration
                        session_result = {"status": "saved", "remaining": remaining_seconds}
                        console.print(f"\n[green]✓ Progress saved! Remaining: {format_time(remaining_seconds)}[/]")
                        time.sleep(1)
                        break
                    elif choice == '2':
                        # Quit/Erase session
                        session_result = {"status": "cancelled", "remaining": None}
                        console.print("\n[yellow]Session ended.[/]")
                        time.sleep(1)
                        break
                    else:
                        # Resume (default)
                        console.print("\n[green]Resuming...[/]")
                        is_paused = False
                        last_update = time.time()
                        
                        # Clear any pending input again before resuming
                        while msvcrt.kbhit():
                            msvcrt.getch()
                        
                        live.start()
                        continue
                
                # Update timer every second
                if current_time - last_update >= 1.0 and not is_paused:
                    remaining_seconds -= 1
                    elapsed_seconds += 1
                    last_update = current_time
                
                live.update(create_display())
                time.sleep(0.1)
            
            # Timer finished
            if remaining_seconds <= 0:
                live.stop()
                
                # Send notification and bring window to foreground
                send_completion_notification(task_title, elapsed_seconds)
                
                result = show_completion_screen()
                
                # Handle extend
                while result == "extend":
                    new_time = show_extend_screen()
                    if new_time > 0:
                        console.clear()
                        console.print("\n[bold magenta]⏱ DEEP WORK MODE[/]", justify="center")
                        console.print("[dim]Press SPACE to pause/resume | Press Q to quit[/]\n", justify="center")
                        
                        with Live(create_display(), console=console, refresh_per_second=2, transient=True) as live2:
                            last_update = time.time()
                            
                            while remaining_seconds > 0:
                                current_time = time.time()
                                
                                key = check_key_press()
                                if key == ' ':
                                    is_paused = not is_paused
                                    time.sleep(0.2)
                                elif key == 'q':
                                    live2.stop()
                                    session_result = {"status": "saved", "remaining": remaining_seconds}
                                    break
                                
                                if current_time - last_update >= 1.0 and not is_paused:
                                    remaining_seconds -= 1
                                    elapsed_seconds += 1
                                    last_update = current_time
                                
                                live2.update(create_display())
                                time.sleep(0.1)
                            
                            if remaining_seconds <= 0:
                                live2.stop()
                                
                                # Send notification for extended session completion
                                send_completion_notification(task_title, elapsed_seconds)
                                
                                result = show_completion_screen()
                            else:
                                result = None
                    else:
                        result = show_completion_screen()
                        
    except KeyboardInterrupt:
        session_result = {"status": "cancelled", "remaining": None}
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        session_result = {"status": "cancelled", "remaining": None}
        time.sleep(2)
    
    # Write result to file
    try:
        with open(result_file, 'w') as f:
            json.dump(session_result, f)
    except Exception as e:
        print(f"Error saving result: {e}")
    
    # Return the session result so subprocess handler can display it
    return session_result


def start_deep_work(task_title, duration_seconds, gif_path=None):
    """
    Launch deep work mode in a new terminal window.
    
    Returns: (task_completed, task_dismissed, saved_remaining)
    """
    # Create temp file for result communication
    result_file = os.path.join(tempfile.gettempdir(), f"tdl_deepwork_{os.getpid()}.json")
    
    # Get the path to this script
    script_path = os.path.abspath(__file__)
    
    # Build command arguments as a list (safer, no escaping needed)
    cmd = [
        sys.executable,
        script_path,
        "--run-session",
        "--title", task_title,
        "--duration", str(duration_seconds),
        "--result-file", result_file
    ]
    
    try:
        # Use Popen with CREATE_NEW_CONSOLE to spawn in a new window
        CREATE_NEW_CONSOLE = 0x00000010
        
        process = subprocess.Popen(
            cmd,
            creationflags=CREATE_NEW_CONSOLE
        )
        
        # Wait for the process to complete
        process.wait()
        
        # Read result from temp file
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                result = json.load(f)
            os.remove(result_file)
            
            status = result.get("status", "cancelled")
            remaining = result.get("remaining")
            
            if status == "completed":
                return True, False, None
            elif status == "dismissed":
                return False, True, None
            elif status == "saved":
                return False, False, remaining
            else:
                return False, True, None
        else:
            return False, True, None
            
    except Exception as e:
        print(f"Error launching deep work: {e}")
        return False, True, None


# Entry point for subprocess
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-session", action="store_true")
    parser.add_argument("--title", type=str, default="Deep Work")
    parser.add_argument("--duration", type=int, default=1500)
    parser.add_argument("--result-file", type=str, required=False)
    
    args = parser.parse_args()
    
    if args.run_session:
        result_file = args.result_file or os.path.join(tempfile.gettempdir(), "tdl_result.json")
        session_result = None
        try:
            session_result = run_deep_work_session(args.title, args.duration, result_file)
            
            # If session was interrupted (saved/cancelled), give user time to see the message
            if session_result and session_result.get("status") in ["saved", "cancelled"]:
                print("\n[Press Enter to close]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    pass
                    
        except Exception as e:
            print(f"\n\nFATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("\nPress Enter to close...")
            try:
                input()
            except:
                pass
            sys.exit(1)
        sys.exit(0)  # Ensure terminal closes on success

