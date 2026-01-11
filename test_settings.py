import os
import json
from config_storage import load_config, save_config, get_theme

def test_config():
    print("Testing config storage...")
    original_config = load_config()
    
    test_theme = "neon"
    config = {"theme": test_theme}
    save_config(config)
    
    loaded = load_config()
    assert loaded["theme"] == test_theme
    assert get_theme() == test_theme
    
    # Restore original
    save_config(original_config)
    print("Config storage test passed!")

def test_reset_logic():
    print("Testing reset preparation...")
    # Just check if files are accessible as expected by the logic in main.py
    files = ["tasks.json", "history.json", "categories.json", "goals.json", "recurrent_tasks.json"]
    for f in files:
        if os.path.exists(f):
            print(f"File {f} exists and is accessible.")
        else:
            print(f"File {f} does not exist (will be skipped during reset).")

if __name__ == "__main__":
    test_config()
    test_reset_logic()
