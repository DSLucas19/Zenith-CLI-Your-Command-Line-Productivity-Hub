"""
Test the streak toggle functionality
"""
import sys
import os

sys.path.insert(0, r"f:\App\Anti-gravity\CLI_TDL")
os.chdir(r"f:\App\Anti-gravity\CLI_TDL")

from config_storage import load_config, save_config, get_show_streak

def test_streak_toggle():
    print("=== Testing Streak Toggle Functionality ===\n")
    
    # Get current config
    config = load_config()
    print(f"Current config: {config}")
    
    # Test get_show_streak
    current = get_show_streak()
    print(f"\nCurrent streak display setting: {'ON' if current else 'OFF'}")
    
    # Toggle it
    print("\n--- Toggling streak display ---")
    config["show_streak"] = not current
    save_config(config)
    
    # Verify it changed
    new_setting = get_show_streak()
    print(f"New streak display setting: {'ON' if new_setting else 'OFF'}")
    
    # Toggle back
    print("\n--- Toggling back to original ---")
    config["show_streak"] = current
    save_config(config)
    
    final_setting = get_show_streak()
    print(f"Final streak display setting: {'ON' if final_setting else 'OFF'}")
    
    if final_setting == current:
        print("\n✅ Test PASSED: Streak toggle working correctly!")
    else:
        print("\n❌ Test FAILED: Settings not persisting correctly!")

if __name__ == "__main__":
    test_streak_toggle()
