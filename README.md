# Water Tracker

A simple Python desktop app that helps you track daily water intake. Log water amounts in ml, liters, or ounces—or use preset buttons for common can/bottle sizes. Includes customizable reminders and local storage.

## Features

- **Manual Logging**: Enter any amount in ml, L, or oz
- **Preset Buttons**: Built-in presets for Can (355 ml), Bottle (1L), and Cup (240 ml)
- **Custom Presets**: Save your own preset sizes for quick logging
- **Unit Conversion**: Automatically converts between ml, liters, and ounces
- **Daily Goal Tracking**: Set and track progress toward your daily water goal
- **Progress Bar**: Visual progress indicator toward your daily goal with color coding (green=complete, yellow=75%+, red=<75%)
- **Goal Estimates**: Shows how many of each preset (cans, bottles, etc.) you need to reach your daily goal
- **Daily Stats**: See your total water intake for today
- **Scheduled Reminders**: Set periodic reminders (configurable minutes)
- **History**: View all logged entries with timestamps
- **Local Storage**: All data persists to JSON files (`water_log.json`, `presets.json`, `settings.json`)
- **Export**: Export your full log to a timestamped JSON file

## Files

- `water_tracker.py` : Main application (Tkinter GUI)
- `test_water_tracker.py` : Unit tests for conversion functions and progress bar colors
- `water_log.json` : Created at runtime; stores all logged entries
- `presets.json` : Created at runtime; stores custom presets
- `settings.json` : Created at runtime; stores user settings (daily goal)
- `requirements.txt` : Dependencies (none; uses Python standard library)
- `run_water_tracker.bat` : Windows batch launcher (see Desktop Shortcut section)
- `launch_water_tracker.ps1` : PowerShell launcher

## Installation & Setup

### Requirements
- **Python 3.6+** (Tkinter is included in the standard library)

### Run the App

**Option 1: Direct Python command**
```bash
python water_tracker.py
```

**Option 2: Using the batch launcher** (Windows)
```bash
run_water_tracker.bat
```

**Option 3: Desktop shortcut** (Windows)
See [Desktop Shortcut](#desktop-shortcut) section below.

## Usage

### Setting Your Daily Goal

1. In the "Daily goal" section, enter your target water intake in ml
2. Click **Set** to save your goal (default: 2000 ml = 2 liters)
3. The progress bar will show your current progress toward the goal
4. Progress bar colors:
   - 🟢 **Green**: Goal achieved (100%+)
   - 🟡 **Yellow**: Good progress (75-99%)
   - 🔴 **Red**: Needs more water (<75%)

### Logging Water

1. **Manual Entry**: Enter an amount and select a unit (ml, L, oz), then click **Add**.
2. **Quick Presets**: Click any preset button (Can, Bottle, Cup, or your custom presets) to instantly log that amount.
3. **Save Custom Preset**:
   - Enter an amount and unit
   - Enter a name in the "Save as preset" field
   - Click **Add Preset**
   - Your new preset appears as a button for quick access

### Goal Estimates

The "To reach goal:" section shows exactly how many of each preset you need to consume to reach your daily goal. For example:

```
Need 1500 ml more:

• 4.2 × Can 355 ml
• 1.3 × Bottle 1180 ml
• 6.2 × Cup 240 ml
• 4.2 × Coffee 12 oz
```

This helps you plan how many drinks you need based on your available containers.

### Reminders

1. Enter the interval (in minutes) in the "Reminder" field (default: 60)
2. Click **Start reminders**
3. A popup will appear at the specified interval
4. Click **Stop reminders** to turn them off

### History & Stats

- **Today's total**: Shows the sum of today's logged water
- **Progress bar**: Visual indicator of goal completion
- **History list**: Displays all entries (newest first) with timestamps and ml/oz conversions
- **Clear Today**: Removes today's entries (older history remains)
- **Export JSON**: Saves your entire log to a timestamped file

## Testing

### Run Unit Tests (requires pytest)

```bash
pip install pytest
pytest test_water_tracker.py
```

Or without pytest:
```bash
python test_water_tracker.py
```

The test suite includes:
- Unit conversion tests (ml ↔ liters ↔ ounces)
- Progress bar color tests (red/yellow/green based on completion percentage)

Tests cover unit conversions (ml ↔ L ↔ oz).

## Desktop Shortcut (Windows)

### Method 1: Using the batch launcher (Recommended)

1. Open File Explorer and navigate to your Water Tracker folder
2. Right-click `run_water_tracker.bat`
3. Select **Send to** → **Desktop (create shortcut)**
4. Right-click the new shortcut on your desktop
5. Select **Properties**
6. (Optional) Click **Change Icon** to customize the icon
7. Click **OK**
8. Double-click the shortcut to launch the app

### Method 2: Create a shortcut manually

1. Right-click an empty area on your desktop
2. Select **New** → **Shortcut**
3. In the location field, paste:
   ```
   python "c:\Users\[username]\OneDrive - Microsoft\Code\water_tracker.py"
   ```
   (Replace `[username]` with your actual username)
4. Click **Next**, name it "Water Tracker", then **Finish**
5. (Optional) Right-click → **Properties** → **Change Icon** to customize

### Method 3: Create a PowerShell script shortcut

Create a file named `launch_water_tracker.ps1` in your workspace folder with:
```powershell
Start-Process python "c:\Users\[username]\OneDrive - Microsoft\Code\water_tracker.py"
```

Then create a shortcut to this `.ps1` file.

## Data Storage

All data is stored as JSON in your workspace folder:

- **`water_log.json`**: Array of entries with `timestamp` (ISO format) and `amount_ml`
- **`presets.json`**: Array of presets with `label` and `ml` fields

Example `water_log.json`:
```json
[
  {
    "timestamp": "2026-03-13T14:30:00.123456",
    "amount_ml": 355
  }
]
```

You can manually edit these files or export new snapshots via the app.

## Learning Notes (for Python learners)

This app demonstrates:
- **Tkinter GUI**: Layout with frames, labels, buttons, entry fields
- **File I/O**: Reading/writing JSON with error handling
- **Threading**: Background reminders without blocking the GUI
- **Object-Oriented Design**: `WaterTrackerApp` class with organized methods
- **Unit Conversion**: Simple math with constants and error handling
- **Testing**: Unit tests with pytest
- **Comments & Docstrings**: Explained throughout for learning

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'tkinter'` | Tkinter is not installed with your Python version. Install it: `python -m pip install tk` |
| App won't start | Make sure Python 3.6+ is installed and in your PATH |
| Reminders not showing | Check that the app window is in focus; reminders are popup dialogs |
| Data not saving | Ensure the workspace folder has write permissions |

## Future Enhancements

- Statistics dashboard (weekly/monthly trends)
- System notifications instead of popups
- Custom styling options
- Edit/delete log entries
- Backup to cloud storage

## License

Free to use and modify for personal use.

## Support

For questions or issues, check the code comments or test file for usage examples.
