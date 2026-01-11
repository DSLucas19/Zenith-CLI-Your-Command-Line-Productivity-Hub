# Statistics Feature Documentation

## Overview
Added a new `TDL stat` command that provides insights into task productivity through visual statistics and key metrics.

## Features
1. **30-Day Activity Chart**: Visual bar chart showing time spent on tasks over the last 30 days.
2. **Key Metrics**:
   - 🏆 **Most Time in One Day**: The date with the highest total duration of completed tasks.
   - ⚡ **Most Productive Day**: The date with the highest number of completed tasks.
   - 🎯 **Longest Task**: The single task that took the most time to complete.
3. **Rainbow Theming**: Full integration with the app's rainbow theme system.

## Command
```bash
TDL stat
```

## Data Tracking
- Added `completed_at` timestamp to Task model.
- Updated `check` command to record completion time when tasks are marked done.
- Statistics are calculated based on task history from the last 30 days.
- **Note**: Currently uses estimated task duration (`-t` flag) as a proxy for time spent.

## Implementation Details

### Files Created/Modified
- `main.py`: Added `stat` command.
- `models.py`: Added `completed_at` field to Task model.
- `stats_calculator.py`: Logic for aggregating daily time, counting tasks, and finding extrema.
- `ui_stats.py`: Visualization logic using Rich for the bar chart and metrics panel.
- `stat_command.py`: Command handler grouping data loading, calculation, and rendering.

### Dependencies
- **Rich**: Used for bar chart generation and colorful panel layout.
- **Datetime/Calendar**: Used for temporal calculations and date formatting.

## Usage Example
1. Add tasks with duration: `TDL add "Coding" -t 2h`
2. Complete tasks: `TDL check`
3. View stats: `TDL stat`
