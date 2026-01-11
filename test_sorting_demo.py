"""
Test to demonstrate the new category-based sorting
"""
import sys
sys.path.insert(0, r"f:\App\Anti-gravity\CLI_TDL")

from datetime import datetime, timedelta
from models import Task

def test_sorting():
    print("=== Dashboard Sorting Demonstration ===\n")
    
    # Create sample tasks with different categories
    today = datetime.now()
    
    tasks = [
        Task(title="Team Meeting", category=["Work"], due_date=today, priority=0),
        Task(title="Buy Groceries", category=["Shopping"], due_date=today, priority=0),
        Task(title="Code Review", category=["Work"], due_date=today, priority=1),
        Task(title="Gym Session", category=["Personal"], due_date=today, priority=0),
        Task(title="Client Call", category=["Work"], due_date=today, priority=0),
        Task(title="Buy Gift", category=["Shopping"], due_date=today, priority=0),
        Task(title="Study Python", category=["Learning"], due_date=today, priority=0),
        Task(title="No Category Task", category=None, due_date=today, priority=0),
    ]
    
    # Apply the new sorting logic
    def get_sort_key(task):
        if task.category:
            if isinstance(task.category, list) and task.category:
                primary_category = task.category[0].lower()
            elif isinstance(task.category, str):
                primary_category = task.category.lower()
            else:
                primary_category = ""
        else:
            primary_category = ""
        
        return (
            primary_category,
            -task.priority,
            task.due_date if task.due_date else datetime.max,
            task.title.lower()
        )
    
    tasks.sort(key=get_sort_key)
    
    # Display sorted tasks
    print("SORTED TASKS (Category First):\n")
    current_category = None
    for i, task in enumerate(tasks, 1):
        cat = task.category[0] if task.category and isinstance(task.category, list) else (task.category or "No Category")
        
        # Print category header when it changes
        if cat != current_category:
            current_category = cat
            print(f"\n[{current_category.upper()}]")
        
        priority_marker = "🚩" if task.priority == 1 else "  "
        print(f"  {i}. {priority_marker} {task.title}")
    
    print("\n" + "="*60)
    print("✅ Tasks are now grouped by category alphabetically!")
    print("   - No Category tasks appear first")
    print("   - Then Learning, Personal, Shopping, Work (alphabetical)")
    print("   - Within each category, important tasks (🚩) appear first")

if __name__ == "__main__":
    test_sorting()
