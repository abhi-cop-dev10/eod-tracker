# EOD Task Tracker — Desktop App (Claude Code Build Instructions)

## Overview

Build a modern offline desktop application for an organisation where employees track their daily tasks and export a filled Excel EOD report. The app runs silently in the system tray, shows a floating sidebar panel, includes a fun "Gorilla Interruption" reminder feature, and exports a styled Excel file at end of day.

---

## Technology Stack

- **Language**: Python 3.11+
- **GUI Framework**: PyQt6 (modern, supports system tray, floating windows, animations)
- **Excel Generation**: openpyxl (read template + fill values with styles preserved)
- **Database**: SQLite via sqlite3 (local, offline, zero setup)
- **Packaging**: PyInstaller (bundle into a single `.exe` for Windows)
- **Animation**: Qt animations (QPropertyAnimation) for gorilla slide-up
- **Tray Icon**: PyQt6 QSystemTrayIcon

### Why Python + PyQt6?
- Fully offline, no internet needed
- Single `.exe` distributable across organisation
- openpyxl preserves Excel template styles perfectly
- PyQt6 supports custom frameless floating windows
- Easy to maintain by any Python developer

---

## Project Structure

```
eod_tracker/
├── main.py                  # Entry point
├── app/
│   ├── __init__.py
│   ├── tray.py              # System tray icon + menu
│   ├── floating_panel.py    # Main floating sidebar UI
│   ├── task_form.py         # Add task form (inside panel)
│   ├── task_table.py        # Task list table widget
│   ├── gorilla.py           # Gorilla popup animation widget
│   ├── settings.py          # Settings panel
│   ├── excel_export.py      # Excel fill + download logic
│   └── database.py          # SQLite operations
├── assets/
│   ├── tray_icon.png        # App tray icon (32x32)
│   ├── gorilla.png          # Gorilla image/animation frames
│   ├── toggle_on.png
│   └── toggle_off.png
├── templates/
│   └── eod_template.xlsx    # The organisation's Excel template (user provides)
├── data/
│   └── tasks.db             # Auto-created SQLite database
├── requirements.txt
└── build.spec               # PyInstaller spec
```

---

## Database Schema

Create `data/tasks.db` with SQLite on first run.

### Table: `tasks`

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    client_name TEXT NOT NULL,
    assigned_to TEXT NOT NULL,        -- Employee's own name (pre-filled from settings)
    assigned_by TEXT NOT NULL,
    timer_status TEXT DEFAULT 'inactive',  -- Internal: 'inactive', 'running', 'finished'
    eod_status TEXT DEFAULT 'In Progress', -- Excel Status column: 'Update Sent', 'In Progress', 'Pending'
    start_time TEXT,                  -- HH:MM format for display + Excel
    end_time TEXT,
    duration TEXT,                    -- e.g. "6 Hours" or "2h 15m"
    what_done TEXT DEFAULT '',
    date TEXT NOT NULL                -- YYYY-MM-DD
);
```

### Table: `settings`

```sql
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

Default settings rows to insert on first run:
- `gorilla_enabled` = `true`
- `gorilla_interval_type` = `fixed`  (values: `fixed` or `random`)
- `gorilla_interval_seconds` = `120`  (2 minutes default)
- `gorilla_random_min` = `120`
- `gorilla_random_max` = `300`
- `gorilla_message` = `What are you doing?`

---

## Feature 1: System Tray

**File**: `app/tray.py`

- App starts minimised — no window shown, only a tray icon appears in Windows taskbar
- Tray icon should pulse/glow green to show it is active
- Right-click tray icon shows context menu:
  - "Open Panel" — shows the floating panel
  - "Settings" — opens settings window
  - "Exit" — quits the app
- Double-click tray icon also opens the floating panel
- On startup, show a tray notification: "EOD Tracker is running. Click the side button to open."

---

## Feature 2: Floating Side Panel

**File**: `app/floating_panel.py`

### Panel Behaviour

- A small circular/pill floating button is permanently anchored to the **absolute right edge of the screen**, vertically centred (50% of screen height)
- This button is always on top (`setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)`)
- Button appearance: rounded pill, dark background, white arrow icon `‹` pointing left
- When clicked, the panel slides in from the right side, covering exactly **half the screen width**, full screen height
- Panel slides in with smooth animation (300ms ease-in-out using QPropertyAnimation on geometry)
- Panel can be closed by:
  1. Clicking the floating button again (arrow flips to `›`)
  2. Clicking a small `×` minimize icon at the top of the panel

### Panel Layout (top to bottom)

```
┌─────────────────────────────────────┐
│  [×]   EOD Task Tracker    [⚙ Settings] │  ← Header bar
├─────────────────────────────────────┤
│  ┌────────────────────────────────┐ │
│  │ Task Name:  [________________] │ │  ← Add Task Form
│  │ Client:     [________________] │ │
│  │ Assigned By:[________________] │ │
│  │           [+ Add Task]         │ │
│  └────────────────────────────────┘ │
├─────────────────────────────────────┤
│  Task List Table (scrollable)       │  ← Task Table
│  (see table spec below)             │
├─────────────────────────────────────┤
│  [📥 Download Today's Excel Report] │  ← Bottom export button
└─────────────────────────────────────┘
```

### Panel Visual Style

- Background: `#1a1a2e` (deep navy dark)
- Header: `#16213e`
- Cards/inputs: `#0f3460` with subtle border `#e94560`
- Accent colour: `#e94560` (red-pink)
- Text: `#eaeaea`
- Font: Segoe UI or Inter, 13px
- Rounded corners on all elements: 8px
- Subtle box shadows on the panel itself

---

## Feature 3: Add Task Form

**File**: `app/task_form.py`

Four fields inside the panel:
1. **Task Name** — text input, placeholder "e.g. Login Page Development"
2. **Client Name** — text input, placeholder "e.g. ATB Media"
3. **Assigned To** — text input, **pre-filled automatically** from `employee_name` in settings (user can override)
4. **Assigned By** — text input, placeholder "e.g. Abhijeet Da"

**[+ Add Task]** button:
- Validates all three fields are non-empty
- Inserts a new row into `tasks` table with today's date, status `inactive`
- Refreshes the task table
- Clears the form

---

## Feature 4: Task List Table

**File**: `app/task_table.py`

### Table Columns

| Column | Width | Notes |
|---|---|---|
| Timer | 70px | Toggle pill — Running (green) / Stopped (grey) — controls the clock |
| Task Name | 170px | Text, truncated with tooltip on hover if long |
| Client | 100px | Client name |
| Start Time | 75px | Blank until started, shows HH:MM |
| End Time | 75px | Blank until finished |
| Duration | 70px | e.g. "2h 15m", calculated automatically |
| What done? | 180px | Text summary, appended by gorilla or manual edit |
| Action | 130px | Start ▶ / Finish ■ button + Delete 🗑 button |

> **Note**: The "Status" column in Excel (Update Sent / In Progress / Pending) is NOT shown as a separate column in the app table — it is set via the gorilla "Finished This Task" dropdown and defaults to "In Progress" for running tasks. It is always correctly written to Excel on export.

### Row Behaviour

**Timer Toggle Pill**:
- Shows a pill toggle: grey "Stopped" / green "Running"
- Clicking it is a shortcut — same as pressing Start or Finish
- Running rows get a subtle green left border accent (3px)
- Finished rows get a subtle blue left border accent

**Start button (▶)**:
- Only shown if task has no start time yet
- On click: records current time as `start_time` in DB (HH:MM format), sets `timer_status = 'running'`, sets `eod_status = 'In Progress'`
- Button changes to "Finish ■" after start

**Finish button (■)**:
- On click: records current time as `end_time`, calculates duration, sets `timer_status = 'finished'`
- Duration format: "Xh Ym" — e.g. "1h 30m" or "45m"
- `eod_status` stays as whatever was last set (default "In Progress" unless gorilla set it to "Update Sent" or "Pending")

**Delete button (🗑)**:
- Shows a confirmation popup dialog:
  - Title: "Delete Task?"
  - Message: "Are you sure you want to delete '[Task Name]'? This cannot be undone."
  - Buttons: [Cancel] [Delete]
- On confirm: removes from DB, refreshes table

### Table Styling
- Alternating row colours: `#0f3460` and `#16213e`
- Header row: `#e94560` background, white bold text
- Hover row: slight brightness increase
- Active task row: green left border 3px accent
- No horizontal scrollbar — columns sized to fit panel width

---

## Feature 5: Excel Export

**File**: `app/excel_export.py`

## Feature 5: Excel Export

**File**: `app/excel_export.py`

### Your Confirmed Excel Column Layout

Based on the provided EOD template, the columns are mapped as follows:

```
Column A = Task Name
Column B = Status          ← eod_status: "Update Sent", "In Progress", "Pending"
Column C = Client
Column D = Start Time      ← HH:MM format
Column E = End Time        ← HH:MM format
Column F = Duration        ← e.g. "6 Hours" or "2h 15m"
Column G = Assigned To     ← employee_name from settings
Column H = Assigned By
Column I = What Have Done?
```

Hardcode this mapping in `excel_export.py`:

```python
COLUMN_MAP = {
    "task_name":   "A",
    "eod_status":  "B",
    "client_name": "C",
    "start_time":  "D",
    "end_time":    "E",
    "duration":    "F",
    "assigned_to": "G",
    "assigned_by": "H",
    "what_done":   "I",
}
DATA_START_ROW = 2   # Row 1 is the header row in the template
```

> The user can override `DATA_START_ROW` in Settings if their template has additional header rows above the data.

### Template Handling

- Load `templates/eod_template.xlsx` using `openpyxl.load_workbook(path, keep_vba=False)`
- This preserves all existing cell styles, borders, fill colours, merged cells, and fonts
- Do NOT recreate the file from scratch — only write values into existing cells

### What to Fill

Query today's tasks from SQLite:

```sql
SELECT task_name, eod_status, client_name, start_time, end_time,
       duration, assigned_to, assigned_by, what_done
FROM tasks
WHERE date = date('now')
ORDER BY id ASC
```

### Export Process

1. Load the template workbook (keep all styles intact)
2. Get today's tasks from SQLite
3. Starting at `DATA_START_ROW`, write each task into the mapped columns
4. Only set `.value` on each cell — never touch `.font`, `.fill`, `.border`, or `.alignment`
5. Duration formatting: if under 60 minutes write "X Minutes", else write "Xh Ym" — e.g. "6 Hours", "1h 30m", "45 Minutes"
6. Save as: `EOD_{EmployeeName}_{YYYY-MM-DD}.xlsx`
7. Open a Qt "Save As" file dialog so user picks save location
8. On success: show toast notification "Excel saved! ✓"

### Employee Name
- Ask for employee name on first launch via a simple dialog and store in `settings` table as `employee_name`
- This is used in both the "Assigned To" column and the exported filename

---

## Feature 6: Gorilla Interruption

**File**: `app/gorilla.py`

This is the fun feature. A gorilla character periodically pops up to ask what the user is working on.

### Animation Sequence

1. A gorilla character (use a PNG image of a cartoon gorilla or emoji-style art) slides **up from the bottom-right corner** of the screen
2. Animation: gorilla starts at y = screen_height + gorilla_height, animates to y = screen_height - gorilla_height - 80px (so only upper body + head is visible above screen bottom)
3. The gorilla's eyes animate up and down (simple QPropertyAnimation on a property or swap between two eye images — eyes-up.png and eyes-down.png — on 1 second interval)
4. Slide-up animation: 800ms ease-out using QPropertyAnimation

### Gorilla Widget Layout

```
┌──────────────────────────────────────┐   ← Floating window, bottom-right
│  [🦍 gorilla image — upper body]     │   ← Gorilla peeks up from bottom
│                                      │
│  ┌──────────────────────────────┐    │
│  │  "What are you doing?"       │    │  ← Heading (customisable in settings)
│  │  ┌────────────────────────┐  │    │
│  │  │ Type what you're doing │  │    │  ← Text area (multiline)
│  │  │                        │  │    │
│  │  └────────────────────────┘  │    │
│  │                              │    │
│  │  [✔ Confirm]                 │    │  ← Top buttons
│  │  [🔁 Doing Same Thing]       │    │
│  │  ─────────────────────────── │    │  ← Divider
│  │  Task Status:                │    │  ← Status section
│  │  [Update Sent        ▼]      │    │  ← Dropdown (default: Update Sent)
│  │  [✅ Finished This Task]     │    │  ← Finish button with status
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

### Status Dropdown (above "Finished This Task" button)

- Label: "Task Status:" in small muted text
- Dropdown (QComboBox) with options:
  - `Update Sent` ← **default selection**
  - `In Progress`
  - `Pending`
- Styled to match dark theme: dark background, white text, accent border
- This dropdown value is what gets written to the Excel **Status (Column B)** when "Finished This Task" is clicked

### Button Behaviours

**[✔ Confirm]**:
- Takes the text from the textarea (must not be empty — show red border if empty and don't proceed)
- Appends to the `what_done` column of the **currently running task** in the DB
- Append format: if `what_done` is empty, just set it; if not empty, append with ` | ` separator
- Example result: `"Do the landing page content change | Fix checkout page variant"`
- Does NOT change `eod_status` or end the task
- Closes gorilla with slide-down animation
- Shows brief toast notification: "Logged! ✓"

**[🔁 Doing Same Thing]**:
- Does nothing to DB at all
- Closes gorilla with slide-down animation — no toast

**[✅ Finished This Task]**:
- Reads the selected value from the status dropdown (`Update Sent`, `In Progress`, or `Pending`)
- If textarea has text: appends to `what_done` first (same append logic as Confirm)
- Sets `end_time` = current time (HH:MM)
- Calculates `duration` from `start_time` to now
- Sets `timer_status = 'finished'`
- Sets `eod_status` = the dropdown value selected
- Saves all to DB
- Refreshes the task table in the panel
- Closes gorilla with slide-down animation
- Shows toast: "Task finished! Status: [Update Sent/In Progress/Pending] ✓"

### Gorilla Timer

Runs in a background QTimer. Checks settings from DB:
- If `gorilla_interval_type` = `fixed`: fire every `gorilla_interval_seconds`
- If `gorilla_interval_type` = `random`: fire after a random delay between `gorilla_random_min` and `gorilla_random_max` seconds
- Only shows gorilla if `gorilla_enabled` = `true`
- Only shows gorilla if there is at least one started (running) task
- After gorilla closes, immediately reschedule next appearance

---

## Feature 7: Settings Panel

**File**: `app/settings.py`

Opens as a separate window from the header "⚙ Settings" button.

### Settings Sections

#### General
- **Employee Name**: text input (used in Excel filename)
- **Excel Template Path**: file picker button — "Browse" to select the `.xlsx` template file (stores path in settings DB)
- **Excel Column Mapping**: table showing field → column letter mapping (editable)
- **Data Start Row**: number input for first data row

#### Gorilla Settings 🦍
- **Enable Gorilla Reminders**: checkbox toggle (on/off)
- **Interval Type**: radio buttons — `Fixed Interval` / `Random Interval`
- **Fixed Interval**: dropdown — `30 seconds (demo)`, `2 minutes`, `5 minutes`, `10 minutes`, `15 minutes`, `30 minutes`, `1 hour`
- **Random Interval Range**: "Between" [min dropdown] "and" [max dropdown]
- **Gorilla Message Heading**: text input, default `What are you doing?`
- **Preview Gorilla**: button that immediately triggers the gorilla popup

#### About
- App version, developer info, organisation name field

### Save Button
- Saves all settings to `settings` table in SQLite
- Shows "Settings saved ✓" toast

---

## Feature 8: Startup & Packaging

### Auto-Start with Windows
- On first launch, ask user: "Start EOD Tracker automatically when Windows starts?" [Yes] [No]
- If yes: add registry key `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

### PyInstaller Build

`requirements.txt`:
```
PyQt6>=6.6.0
openpyxl>=3.1.2
pyinstaller>=6.0.0
```

Build command:
```bash
pyinstaller --onefile --windowed --icon=assets/tray_icon.ico --name="EODTracker" --add-data="assets;assets" --add-data="templates;templates" main.py
```

The `--windowed` flag hides the terminal. `--onefile` makes a single `.exe`.

---

## Visual Design Summary

### Colour Palette
```
Background Deep:    #1a1a2e
Background Mid:     #16213e
Background Light:   #0f3460
Accent Red-Pink:    #e94560
Accent Green:       #4caf50
Text Primary:       #eaeaea
Text Secondary:     #a0aec0
Border:             #2d3748
```

### Typography
- Font: `Segoe UI` (Windows built-in), fallback `Arial`
- Sizes: 13px body, 15px headings, 11px metadata

### Component Styles (apply via Qt stylesheets)
- All input fields: dark bg, rounded 6px, light border, white text
- Buttons: filled accent colour, rounded 6px, hover darkens by 10%
- Toggle pills: 40px × 20px, animated slide
- Table: no gridlines visible, alternating rows, hover highlight
- Panel: drop shadow on left edge (simulated with border)

---

## Implementation Order for Claude Code

Build in this exact order so each step is testable:

1. **Setup** — project structure, SQLite init, requirements.txt
2. **Tray Icon** — app starts in tray, right-click menu, basic open/close
3. **Floating Button** — always-on-top pill button on screen right edge
4. **Panel Slide** — panel slides in/out from right with animation
5. **Add Task Form** — form inside panel, saves to DB
6. **Task Table** — display tasks from DB in styled table
7. **Start/Finish Timers** — start time, end time, duration calculation
8. **Delete with Confirm** — popup confirmation dialog
9. **Status Toggle** — active/inactive pill toggle per row
10. **Excel Export** — load template, fill cells, save dialog
11. **Gorilla Popup** — animated slide-up, form, all 3 buttons
12. **Gorilla Timer** — background timer with fixed/random modes
13. **Settings Panel** — all settings saved to DB
14. **Packaging** — PyInstaller .exe build

---

## Notes for Development

- All data is stored locally in `data/tasks.db` — fully offline
- The Excel template file is read-only as a template; never overwrite it
- Tasks are per-day — each day starts fresh (but old data remains in DB for history)
- If no task is currently "started" (has start_time but no end_time), gorilla should not appear
- The floating button must remain visible even when panel is closed
- Panel must stay within screen bounds — use `QScreen.availableGeometry()`
- Use `Qt.Tool` window flag so the panel doesn't appear as a separate taskbar item
- Test on 1920×1080 and 1366×768 screen resolutions
- All times stored and displayed in local system time (no timezone conversion needed)

---

## Handoff Checklist

Before calling the app complete, verify:

- [ ] App starts silently in system tray
- [ ] Floating button always visible on screen right edge
- [ ] Panel opens/closes with smooth animation
- [ ] Tasks can be added with all 3 fields
- [ ] Start timer records correct time
- [ ] Finish timer calculates correct duration
- [ ] Delete shows confirmation popup
- [ ] Status toggle changes between active/inactive
- [ ] Gorilla appears at set intervals
- [ ] Gorilla Confirm appends to what_done column
- [ ] "Doing Same Thing" dismisses without changes
- [ ] "Finished This Task" closes active task with end time
- [ ] Excel export fills template without breaking styles
- [ ] Excel saves with today's date in filename
- [ ] Settings panel saves and loads from DB
- [ ] App packaged as single .exe with PyInstaller

---

*Generated for internal organisation use. All data stays local — no internet connection required.*