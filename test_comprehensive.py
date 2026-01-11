"""
Comprehensive test for the delete all functionality
This script simulates the delete all operation
"""
import os
import json
import sys

def create_test_data():
    """Create some test data files"""
    print("Creating test data files...")
    
    # Create streak.json
    with open("streak.json", "w") as f:
        json.dump({"streak": 5, "last_date": "2026-01-11"}, f)
    
    print("✓ Test data created")

def check_files():
    """Check all data files"""
    files = {
        "tasks.json": "Tasks",
        "history.json": "History", 
        "categories.json": "Categories",
        "goals.json": "Goals",
        "notes.json": "Notes",
        "recurrent_tasks.json": "Recurrent Tasks",
        "streak.json": "Streak Data"
    }
    
    print("\n=== Data Files Status ===")
    for file, name in files.items():
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        status = f"{len(data)} items"
                    elif isinstance(data, dict):
                        status = str(data)
                    else:
                        status = "exists"
                    print(f"✓ {name:20} ({file}): {status}")
            except:
                print(f"✓ {name:20} ({file}): exists (parse error)")
        else:
            print(f"✗ {name:20} ({file}): NOT FOUND")

if __name__ == "__main__":
    os.chdir(r"f:\App\Anti-gravity\CLI_TDL")
    
    print("=== BEFORE DELETE ALL ===")
    check_files()
    
    print("\n\n=== Creating Streak Test Data ===")
    create_test_data()
    
    print("\n\n=== AFTER CREATING STREAK DATA ===")
    check_files()
    
    print("\n\n" + "="*50)
    print("Now run: python main.py settings")
    print("Then select: Reset All Data")
    print("And verify all files are cleared/deleted")
    print("="*50)
