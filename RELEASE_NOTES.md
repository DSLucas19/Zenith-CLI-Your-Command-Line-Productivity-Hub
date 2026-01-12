# TDL - Color & Consistency Update (v2.3) 🎨

## Version Comparison
| Feature | v2.2 | v2.3 (New) |
|---------|------|------------|
| **Category Colors** | Random/Inconsistent | **Persistent & Editable** (`TDL color`) consistent across all views 🌈 |
| **Notifications** | None | **Windows Toast Notification** when Deep Work ends 🔔 |
| **Calendar** | Standard Dot | **Colored Title & Grid** matching category 📅 |
| **Recurring** | buggy/clogged | **Clean Spawning** (Correctly generates next instance) 🔁 |

## 🌟 Key New Features

### 1. Persistent Category Colors
Finally, your colors stick!
- **Auto-Assign**: New categories get a unique color automatically.
- **Fully Customizable**: Use `TDL color Work red` to set your vibe.
- **Everywhere**: The same color appears in Dashboard, Calendar (Grid & List), and Task Lists.
- **Smart Listing**: `TDL color` discovers all used tags and hides overlapping duplicates.

### 2. Deep Work Notifications
- Get a native **Windows Notification** when your focus session completes.
- The window automatically pops to the foreground so you never miss the break.

### 3. Consistency Fixes
- **Unified IDs**: No more mismatched IDs between Calendar and Dashboard.
- **Recurring Tasks**: Completing a recurring task now cleanly spawns the next one without ID conflicts.
- **Persistent Header**: The "TDL MANAGER" header stays put in interactive mode.

---


## Version Comparison
| Feature | v2.1 | v2.2 (New) |
|---------|------|------------|
| **Categories** | Single tags | **Group Aliases** (`Work, Study`) 🏷️ |
| **Updating** | One at a time | **Batch Update** (`update 1,2 -c Work`) ⚡ |
| **Shortcuts** | `TDL welcome` | `TDL home`, `TDL main` 🏠 |
| **UI** | Random colors | **Consistent/Fixed Colors** for categories 🎨 |
| **Cleanliness** | Events checked? | **Smart Icons** (No checkbox for events) 🗓️ |

## 🌟 Key New Features

### 1. Grouped Categories
Assign multiple tags instantly!
- Create a group: `TDL add cat "Work, Study"`
- Use it: `TDL add "Task" -c <GroupID>` -> Automatically applies both tags.

### 2. Batch Update
Modify multiple tasks at once.
- `TDL update 1,2,3 -d tomorrow` sets all to tomorrow.
- Works for events too: `TDL update #1,#2 -c Meeting`.

### 3. Visual Polish
- **Fixed Colors**: Categories now keep their assigned rainbow color permanently (e.g. "Work" is always Red).
- **Cleaner Events**: Events in `today`, `list`, and dashboard no longer show a confusing `[ ]` checkbox.
- **Calendar Fix**: Interactive calendar now shows correct `#IDs` and sorts events properly.

---

# TDL - Heatmap & ID Overhaul Update (v2.1) 🔥

## Version Comparison

| Feature | v2.0 (Previous) | v2.1 (New) |
|---------|-----------------|------------|
| **Visualization** | 30-Day Bar Chart | **365-Day Heatmap** (Yearly Activity) 🔥 |
| **Task IDs** | Shared/Global IDs (Confusing) | **Separate Namespaces** (`1` vs `#1`) 🏷️ |
| **Deletion** | Single Item Only | **Batch Deletion** (`del 1,2,3`) 🗑️ |
| **Events** | Mixed with Tasks | **Distinct Handling** (`TDL info #1`) 📅 |
| **Repl** | `clear` clears screen | `clear` = **Archive**, `cls` = Clear Screen 🖥️ |

## 🌟 Key New Features

### 1. Activity Heatmap
Track your productivity consistency with a GitHub-style heatmap on the welcome screen:
- **Yearly View**: Visualizes Jan 1 - Dec 31.
- **Dynamic Intensity**: Cubes brighten as you complete more tasks.
- **Customizable**: Toggle on/off in Settings. Yellow border for high visibility.

### 2. ID System Overhaul
No more ID shuffling confusion!
- **Numeric IDs**: `1`, `2`, `3` strictly for Tasks.
- **Event IDs**: `#1`, `#2`, `#3` strictly for Calendar Events.
- **Targeting**: Use `TDL update #1` or `TDL info #1` to target events specifically.

### 3. Batch Actions
- **Multi-Delete**: Clean up faster with `TDL del 1,2,3`.
- **Mixed Batching**: `TDL del 1,#1` handles tasks and events in one go.

### 4. REPL Improvements
- **Clear Command**: Typing `clear` now properly archives completed tasks (TDL function).
- **CLS**: Use `cls` to clear the terminal window.

---

# TDL - Rainbow Statistics Update 🌈 (v2.0)

## Version Comparison

| Feature | Original Version | New Update (v2.0) |
|---------|------------------|-------------------|
| **Statistics** | None | **30-Day Activity Chart** with rainbow bar graphs 📊 |
| **Analytics** | None | Tracks **Longest Day**, **Most Productive Day**, & **Longest Task** 🏆 |
| **Deep Work** | Basic text timer | **Optimized UI** with stable, centered layout (Performance fixed) ⚡ |
| **Welcome Screen**| Cluttered with shortcuts | **Clean Command Center** - Pure CLI focus 🚀 |
| **Dashboard** | Simple list | **Smart Sorting** - Groups by Category automatically 🗂 |
| **Data Safety** | Incomplete deletion | **Full Reset** - "Delete All" now completely wipes all data & streaks 🗑 |
| **Customization** | Basic Theme | **Streak Toggle** - Option to hide/show streak icon 🔥 |

## 🌟 Key New Features

### 1. Statistics Command (`TDL stat`)
Visualize your productivity like never before:
- **Interactive Bar Chart**: Shows time spent on tasks for the last 30 days.
- **Dynamic Y-Axis**: Auto-scales to minutes/hours depending on your activity.
- **Rainbow Integration**: Fully themed statistics that match your app's look.
- **Insight Metrics**: Automatically calculates your best days and longest focus sessions.

### 2. Deep Work Refinement
- **Performance Boost**: Removed heavy image processing to ensure the timer never lags.
- **Stable Layout**: Reverted to a rock-solid centered design that prevents display glitches.
- **Compact API**: Smaller footprint for the "Always On Top" window.

### 3. UX Enhancements
- **Category Grouping**: Your dashboard now neatly organizes tasks by their tags.
- **Clean Welcome**: Removed the "Quick Navigation" numbers for a professional terminal look.
- **Streak Control**: Don't want the pressure? Toggle off the streak display in Settings.

## 🛠 Technical Improvements
- Added `completed_at` timestamps to Task model for accurate historical tracking.
- Fixed `streak.json` persistence issues during reset.
- Optimized render loops for smoother UI interactions.
