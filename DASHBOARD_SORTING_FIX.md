# Dashboard Task Sorting Fix

## Issue
Tasks in the dashboard (`TDL db`) were not grouped by category/tag. Users wanted tasks with the same tag to be grouped together, sorted alphabetically by tag.

## Solution

### Updated Sorting Logic ([ui.py](file:///f:/App/Anti-gravity/CLI_TDL/ui.py#L117-L138))

**Before:**
```python
# Sort by priority, then due date, then title
group.sort(key=lambda x: (
    -x.priority,
    x.due_date if x.due_date else datetime.max,
    x.title.lower()
))
```

**After:**
```python
# Sort by category (alphabetically), then priority, then due date, then title
def get_sort_key(task):
    # Get primary category for sorting
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
        primary_category,  # Group by category alphabetically
        -task.priority,     # Then by priority (important first)
        task.due_date if task.due_date else datetime.max,
        task.title.lower()
    )

group.sort(key=get_sort_key)
```

## Sort Order

Tasks are now sorted in this order:

1. **Category/Tag** (alphabetically A-Z)
   - Tasks with no category appear first (empty string sorts first)
   - Tasks with the same category are grouped together
   - Categories are sorted alphabetically

2. **Priority** (within each category group)
   - Important (flag 1) first
   - Normal (flag 0) next
   - Unimportant (flag -1) last

3. **Due Date** (within each priority level)
   - Earlier dates first
   - Tasks without due dates last

4. **Title** (alphabetically)
   - Final tie-breaker

## Example

### Before (Priority-first sorting):
```
Today
1  [ ]  Sun Jan 11  🚩 Important Workout Task
2  [ ]  Sun Jan 11  #Shopping  Buy groceries
3  [ ]  Sun Jan 11  #Work  Team meeting
4  [ ]  Sun Jan 11  #Work  Code review
```

### After (Category-first sorting):
```
Today
1  [ ]  Sun Jan 11  #Shopping  Buy groceries
2  [ ]  Sun Jan 11  #Work  Code review
3  [ ]  Sun Jan 11  #Work  Team meeting
4  [ ]  Sun Jan 11  🚩 Important Workout Task
```

Now all #Work tasks are grouped together, #Shopping tasks are grouped together, etc.

## Multi-Category Tasks

For tasks with multiple categories (e.g., `#Work #Personal`), the **first category** is used for sorting:

```python
task.category = ["Work", "Personal"]
# Will be sorted under "W" (Work)
```

## Benefits

✅ **Better Organization** - Tasks with same category are visually grouped  
✅ **Easier Scanning** - Find all work tasks, shopping tasks, etc. quickly  
✅ **Alphabetical Order** - Predictable category order  
✅ **Maintains Priority** - Important tasks still appear first within their category  
✅ **Backwards Compatible** - Works with both single and multi-category tasks  

## Files Modified

- [`ui.py`](file:///f:/App/Anti-gravity/CLI_TDL/ui.py#L117-L138) - Updated `render_dashboard()` sorting logic

## Testing

Run `TDL db` to see tasks now grouped by category alphabetically, with same-tagged tasks appearing together.
