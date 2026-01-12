"""Test script to debug deep work quit behavior."""
import sys
import tempfile
from deep_work import run_deep_work_session

# Create a result file
result_file = tempfile.mktemp()

try:
    # Run a 10-minute session
    print("Starting deep work session...")
    print("Press Q after a few seconds to test quit behavior")
    print("If you see an error, it will be displayed here\n")
    
    run_deep_work_session("Test Quit Feature", 600, result_file)
    
except Exception as e:
    print(f"\n\nERROR CAUGHT: {e}")
    import traceback
    traceback.print_exc()
    print("\nPress Enter to close...")
    input()
