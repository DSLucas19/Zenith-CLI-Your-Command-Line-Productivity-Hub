"""
Direct test of the clear_all function logic
"""
import os
import json
import sys

# Add current directory to path
sys.path.insert(0, r"f:\App\Anti-gravity\CLI_TDL")

from storage import save_tasks
from history_storage import save_history
from categories_storage import save_categories
from goals_storage import save_goals
from notes_storage import save_notes

def manual_clear_all():
    """Manually execute the clear_all logic"""
    print("Executing clear_all logic...")
    
    try:
        # Clear tasks
        save_tasks([])
        print("✓ Cleared tasks.json")
        
        # Clear history
        save_history([])
        print("✓ Cleared history.json")
        
        # Clear categories
        save_categories([])
        print("✓ Cleared categories.json")

        # Clear goals
        if os.path.exists("goals.json"):
            save_goals([])
            print("✓ Cleared goals.json")
            
        # Clear recurrent tasks
        if os.path.exists("recurrent_tasks.json"):
            with open("recurrent_tasks.json", "w") as f:
                json.dump([], f)
            print("✓ Cleared recurrent_tasks.json")
        
        # Clear notes
        if os.path.exists("notes.json"):
            save_notes([])
            print("✓ Cleared notes.json")
        
        # Clear streak data
        if os.path.exists("streak.json"):
            os.remove("streak.json")
            print("✓ Deleted streak.json")

        print("\n[SUCCESS] All data deleted successfully!")
    except Exception as e:
        print(f"\n[ERROR] Error deleting data: {e}")

def check_files():
    """Check all data files"""
    files = [
        "tasks.json",
        "history.json", 
        "categories.json",
        "goals.json",
        "notes.json",
        "recurrent_tasks.json",
        "streak.json"
    ]
    
    print("\n=== Data Files Status ===")
    all_empty = True
    for file in files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) == 0:
                        print(f"✓ {file}: EMPTY LIST (good)")
                    elif isinstance(data, list):
                        print(f"✗ {file}: {len(data)} items (should be empty!)")
                        all_empty = False
                    else:
                        print(f"✗ {file}: {data} (should be empty!)")
                        all_empty = False
            except:
                print(f"✗ {file}: exists but can't parse")
                all_empty = False
        else:
            if file == "streak.json":
                print(f"✓ {file}: DELETED (good)")
            else:
                print(f"✓ {file}: DELETED or never existed")
    
    return all_empty

if __name__ == "__main__":
    os.chdir(r"f:\App\Anti-gravity\CLI_TDL")
    
    print("=== TESTING DELETE ALL FUNCTIONALITY ===\n")
    
    manual_clear_all()
    
    print("\n" + "="*50)
    all_clear = check_files()
    print("="*50)
    
    if all_clear:
        print("\n✅ TEST PASSED: All data successfully cleared!")
    else:
        print("\n❌ TEST FAILED: Some data still remains!")
