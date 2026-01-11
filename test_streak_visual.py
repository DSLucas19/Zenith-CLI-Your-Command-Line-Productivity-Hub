"""
Visual test showing dashboard with and without streak display
"""
import sys
import os

sys.path.insert(0, r"f:\App\Anti-gravity\CLI_TDL")
os.chdir(r"f:\App\Anti-gravity\CLI_TDL")

from config_storage import load_config, save_config
from storage import load_tasks
import ui

def visual_test():
    print("=== Visual Test: Streak Toggle ===\n")
    
    tasks = load_tasks()
    config = load_config()
    original_setting = config.get("show_streak", True)
    
    # Show with streak ON
    print("\n" + "="*60)
    print("DASHBOARD WITH STREAK DISPLAY ON")
    print("="*60 + "\n")
    config["show_streak"] = True
    save_config(config)
    ui.render_dashboard(tasks[:5])  # Show only first 5 tasks for clarity
    
    input("\nPress Enter to see dashboard with streak OFF...")
    
    # Show with streak OFF
    print("\n" + "="*60)
    print("DASHBOARD WITH STREAK DISPLAY OFF")
    print("="*60 + "\n")
    config["show_streak"] = False
    save_config(config)
    ui.render_dashboard(tasks[:5])
    
    # Restore original setting
    config["show_streak"] = original_setting
    save_config(config)
    
    print(f"\n✅ Restored original setting: {'ON' if original_setting else 'OFF'}")

if __name__ == "__main__":
    visual_test()
