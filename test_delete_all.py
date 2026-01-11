"""
Test script to verify the delete all functionality
"""
import os
import json

def check_data_files():
    """Check if data files exist and contain data"""
    files = [
        "tasks.json",
        "history.json", 
        "categories.json",
        "goals.json",
        "notes.json",
        "recurrent_tasks.json",
        "streak.json"
    ]
    
    print("\n=== Current Data Files Status ===")
    for file in files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f"✓ {file}: {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"✓ {file}: {data}")
                    else:
                        print(f"✓ {file}: exists (unknown format)")
            except:
                print(f"✓ {file}: exists (can't parse)")
        else:
            print(f"✗ {file}: not found")
    print()

if __name__ == "__main__":
    os.chdir(r"f:\App\Anti-gravity\CLI_TDL")
    check_data_files()
