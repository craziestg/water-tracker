#!/usr/bin/env python3
"""
Simple Water Tracker desktop app using Tkinter.

Features:
- Log water amounts in ml, L, or oz
- Preset buttons for common can/bottle sizes (bottle changed to 1L)
- Add user-defined presets (saved to disk as presets.json)
- Unit conversion helpers (documented)
- Persists log to `water_log.json`
- Shows basic stats for today's total
- Simple scheduled reminders (in-app popups)
- Timestamps use system local time (not UTC)
"""

import json
import os
import threading
import time
from datetime import datetime, date, timedelta
from functools import partial
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Filenames for persistence
LOG_FILENAME = os.path.join(os.path.dirname(__file__), "water_log.json")
PRESETS_FILENAME = os.path.join(os.path.dirname(__file__), "presets.json")
SETTINGS_FILENAME = os.path.join(os.path.dirname(__file__), "settings.json")

# Conversion constant
ML_PER_OUNCE = 29.5735295625


# -----------------------------
# Persistence helpers
# -----------------------------
def load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        try:
            os.rename(path, path + ".bak")
        except Exception:
            pass
        return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_log():
    return load_json_file(LOG_FILENAME, [])


def save_log(log):
    save_json_file(LOG_FILENAME, log)


def load_presets():
    """Load custom presets; fall back to built-in defaults if none exist."""
    saved = load_json_file(PRESETS_FILENAME, None)
    if saved is not None:
        return saved
    # Default built-in presets (bottle changed to 1000 ml = 1 L)
    return [
        {"label": "Can 355 ml", "ml": 355},
        {"label": "Bottle 1000 ml", "ml": 1000},
        {"label": "Cup 240 ml", "ml": 240},
    ]


def save_presets(presets):
    save_json_file(PRESETS_FILENAME, presets)


def load_settings():
    """Load user settings; fall back to defaults if none exist."""
    saved = load_json_file(SETTINGS_FILENAME, None)
    if saved is not None:
        return saved
    # Default settings
    return {
        "daily_goal_ml": 2000,  # 2 liters default
    }


def save_settings(settings):
    save_json_file(SETTINGS_FILENAME, settings)


# -----------------------------
# Unit conversion helpers
# -----------------------------
def to_ml(amount, unit):
    if amount is None:
        raise ValueError("amount is required")
    unit = unit.strip().lower()
    if unit in ("ml", "milliliter", "milliliters"):
        return int(round(float(amount)))
    if unit in ("l", "liter", "liters"):
        return int(round(float(amount) * 1000.0))
    if unit in ("oz", "ounce", "ounces"):
        return int(round(float(amount) * ML_PER_OUNCE))
    raise ValueError(f"unsupported unit: {unit}")


def ml_to_oz(ml):
    return float(ml) / ML_PER_OUNCE


# -----------------------------
# Reminder thread
# -----------------------------
class ReminderThread:
    def __init__(self, interval_minutes, callback, app):
        self.interval = max(1, int(interval_minutes))
        self.callback = callback
        self.app = app
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.wait(self.interval * 60):
            try:
                self.app.after(0, self.callback)
            except Exception:
                pass


# -----------------------------
# GUI app
# -----------------------------
class WaterTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Water Tracker")
        self.geometry("900x640")  # Increased size for full layout
        self.minsize(850, 620)

        # Load data
        self.log = load_log()
        self.presets = load_presets()
        self.settings = load_settings()

        # Build UI
        self._build_ui()

        # Initial update
        self.update_stats()

        self.reminder_thread = None

    def _build_ui(self):
        # Top: manual entry
        top = ttk.Frame(self, padding=(10, 10))
        top.pack(fill=tk.X)

        ttk.Label(top, text="Amount:").grid(row=0, column=0, sticky=tk.W)
        self.amount_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.amount_var, width=12).grid(row=0, column=1)

        ttk.Label(top, text="Unit:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.unit_var = tk.StringVar(value="ml")
        unit_combo = ttk.Combobox(top, textvariable=self.unit_var, values=["ml", "L", "oz"], width=6)
        unit_combo.grid(row=0, column=3)

        add_btn = ttk.Button(top, text="Add", command=self.on_add)
        add_btn.grid(row=0, column=4, padx=(10, 0))

        # Allow saving current manual amount as a custom preset
        ttk.Label(top, text="Save as preset:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.preset_name_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.preset_name_var, width=20).grid(row=1, column=1, columnspan=2, sticky=tk.W)
        save_preset_btn = ttk.Button(top, text="Add Preset", command=self.save_current_as_preset)
        save_preset_btn.grid(row=1, column=3, padx=(6, 0), sticky=tk.W)

        # Preset buttons area
        preset_frame = ttk.LabelFrame(self, text="Presets (click to add)")
        preset_frame.pack(fill=tk.X, padx=10, pady=(8, 4))
        self.preset_buttons_frame = ttk.Frame(preset_frame)
        self.preset_buttons_frame.pack(fill=tk.X, padx=6, pady=6)
        self._render_presets()

        # Configure progress bar styles
        self._configure_progress_styles()

        # Middle: stats and history
        mid = ttk.Frame(self, padding=(10, 10))
        mid.pack(fill=tk.BOTH, expand=True)

        stats_frame = ttk.Frame(mid)
        stats_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Daily goal setting
        goal_frame = ttk.Frame(stats_frame)
        goal_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(goal_frame, text="Daily goal:").pack(anchor=tk.W)
        goal_input_frame = ttk.Frame(goal_frame)
        goal_input_frame.pack(fill=tk.X, pady=(2, 0))
        self.goal_var = tk.StringVar(value=str(self.settings.get("daily_goal_ml", 2000)))
        ttk.Entry(goal_input_frame, textvariable=self.goal_var, width=8).pack(side=tk.LEFT)
        ttk.Label(goal_input_frame, text="ml").pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(goal_input_frame, text="Set", command=self.set_daily_goal).pack(side=tk.LEFT, padx=(6, 0))

        # Progress bar (custom canvas-based for consistent coloring)
        progress_frame = ttk.Frame(stats_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(progress_frame, text="Progress:").pack(anchor=tk.W)
        self.progress_var = tk.DoubleVar()

        # Create a canvas-based progress bar for reliable color control across platforms
        self.progress_canvas = tk.Canvas(progress_frame, height=20, bd=0, highlightthickness=1, highlightbackground="#999")
        self.progress_canvas.pack(fill=tk.X, pady=(2, 4))
        self._progress_bar_item = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="#FF6B6B", width=0)

        self.progress_label = ttk.Label(progress_frame, text="0 / 2000 ml (0%)")
        self.progress_label.pack(anchor=tk.W)

        # Goal estimates section
        estimates_frame = ttk.LabelFrame(stats_frame, text="To reach goal:")
        estimates_frame.pack(fill=tk.BOTH, pady=(0, 10), expand=True)

        # Add scrollbar for dynamic content growth
        estimates_scrollbar = ttk.Scrollbar(estimates_frame)
        estimates_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Explicitly set colors to ensure readability across themes
        self.estimates_text = tk.Text(
            estimates_frame,
            height=4,
            width=25,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=(None, 9),
            bg="#FFFFFF",
            fg="#000000",
            insertbackground="#000000",
            yscrollcommand=estimates_scrollbar.set,
        )
        self.estimates_text.pack(fill=tk.BOTH, padx=4, pady=4, expand=True)
        estimates_scrollbar.config(command=self.estimates_text.yview)

        # Current total
        ttk.Label(stats_frame, text="Today's total:").pack(anchor=tk.W)
        self.total_var = tk.StringVar(value="0 ml")
        ttk.Label(stats_frame, textvariable=self.total_var, font=(None, 14, "bold")).pack(anchor=tk.W, pady=(4, 10))

        # Reminder controls
        ttk.Label(stats_frame, text="Reminder (minutes):").pack(anchor=tk.W)
        self.reminder_interval_var = tk.StringVar(value="60")
        ttk.Entry(stats_frame, textvariable=self.reminder_interval_var, width=6).pack(anchor=tk.W)
        self.reminder_start_btn = ttk.Button(stats_frame, text="Start reminders", command=self.start_reminders)
        self.reminder_start_btn.pack(anchor=tk.W, pady=(6, 2))
        self.reminder_stop_btn = ttk.Button(stats_frame, text="Stop reminders", command=self.stop_reminders, state=tk.DISABLED)
        self.reminder_stop_btn.pack(anchor=tk.W)

        # Graph section on the right (if matplotlib is available)
        if MATPLOTLIB_AVAILABLE:
            graph_frame = ttk.LabelFrame(mid, text="Daily Intake Trend (Past 7 Days)")
            graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
            self.graph_canvas_widget = ttk.Frame(graph_frame)
            self.graph_canvas_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            self._update_graph()
        else:
            # Placeholder if matplotlib is not available
            placeholder_frame = ttk.Frame(mid)
            placeholder_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
            ttk.Label(placeholder_frame, text="Install matplotlib to see daily intake graphs:\npip install matplotlib").pack(padx=10, pady=10)

        # Bottom controls
        bottom = ttk.Frame(self, padding=(10, 6))
        bottom.pack(fill=tk.X)
        ttk.Button(bottom, text="Clear Today", command=self.clear_today).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Export JSON", command=self.export_json).pack(side=tk.LEFT, padx=(6, 0))

    def set_daily_goal(self):
        """Update the daily water goal."""
        try:
            goal_ml = int(self.goal_var.get())
            if goal_ml <= 0:
                raise ValueError("Goal must be positive")
            self.settings["daily_goal_ml"] = goal_ml
            save_settings(self.settings)
            self.update_stats()
            messagebox.showinfo("Goal Updated", f"Daily goal set to {goal_ml} ml")
        except ValueError as e:
            messagebox.showerror("Invalid Goal", f"Please enter a valid number: {e}")

    # Render preset buttons from self.presets
    def _render_presets(self):
        # Clear existing
        for child in self.preset_buttons_frame.winfo_children():
            child.destroy()
        # Create a button for each preset
        for i, p in enumerate(self.presets):
            label = p.get("label", f"{p.get('ml')} ml")
            ml = p.get("ml", 0)
            btn = ttk.Button(self.preset_buttons_frame, text=label, command=partial(self.add_preset_ml, ml))
            btn.grid(row=0, column=i, padx=4, pady=2)

    def _configure_progress_styles(self):
        """Configure progress bar styles for different completion levels."""
        style = ttk.Style()

        # Default progress bar (red/incomplete)
        style.configure('Horizontal.TProgressbar',
                       background='#FF6B6B',  # Light red
                       troughcolor='#E0E0E0',  # Light gray trough
                       borderwidth=1,
                       lightcolor='#FF6B6B',
                       darkcolor='#FF6B6B')

        # Yellow progress bar (75%+ completion)
        style.configure('Yellow.Horizontal.TProgressbar',
                       background='#FFD93D',  # Yellow
                       troughcolor='#E0E0E0',
                       borderwidth=1,
                       lightcolor='#FFD93D',
                       darkcolor='#FFD93D')

        # Green progress bar (100% completion)
        style.configure('Green.Horizontal.TProgressbar',
                       background='#6BCF7F',  # Green
                       troughcolor='#E0E0E0',
                       borderwidth=1,
                       lightcolor='#6BCF7F',
                       darkcolor='#6BCF7F')

    # Save manual input as a preset (user-defined)
    def save_current_as_preset(self):
        name = self.preset_name_var.get().strip()
        amt = self.amount_var.get().strip()
        unit = self.unit_var.get().strip()
        if not name or not amt:
            messagebox.showinfo("Preset required", "Enter a name and amount to save a preset.")
            return
        try:
            ml = to_ml(amt, unit)
        except Exception as e:
            messagebox.showerror("Invalid input", str(e))
            return
        # Append new preset and persist
        self.presets.append({"label": name, "ml": int(ml)})
        save_presets(self.presets)
        self._render_presets()
        self._update_goal_estimates()
        self.preset_name_var.set("")
        messagebox.showinfo("Preset saved", f"Saved preset '{name}' -> {ml} ml")

    # Add preset ml to the log
    def add_preset_ml(self, ml):
        entry = {"timestamp": datetime.now().isoformat(), "amount_ml": int(ml)}
        self.log.insert(0, entry)
        save_log(self.log)
        self.update_stats()

    # Add manual entry
    def on_add(self):
        amt = self.amount_var.get().strip()
        unit = self.unit_var.get().strip()
        if not amt:
            messagebox.showinfo("Input required", "Please enter an amount to add.")
            return
        try:
            ml = to_ml(amt, unit)
        except Exception as e:
            messagebox.showerror("Invalid input", str(e))
            return
        entry = {"timestamp": datetime.now().isoformat(), "amount_ml": int(ml)}
        self.log.insert(0, entry)
        save_log(self.log)
        self.update_stats()
        self.amount_var.set("")

    # UI refresh helpers
    def refresh_history_list(self):
        self.history_list.delete(0, tk.END)
        for entry in self.log[:200]:
            ts = entry.get("timestamp")
            try:
                d = datetime.fromisoformat(ts)
                ts_str = d.strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_str = ts
            ml = entry.get("amount_ml", 0)
            oz = ml_to_oz(ml)
            self.history_list.insert(tk.END, f"{ts_str} — {ml} ml ({oz:.1f} oz)")

    def update_stats(self):
        today = date.today()
        total_ml = 0
        for e in self.log:
            try:
                ts = datetime.fromisoformat(e["timestamp"]) if isinstance(e["timestamp"], str) else None
            except Exception:
                ts = None
            if ts is None:
                total_ml += e.get("amount_ml", 0)
            else:
                if ts.date() == today:
                    total_ml += e.get("amount_ml", 0)

        # Update total display
        self.total_var.set(f"{total_ml} ml")

        # Update progress bar
        goal_ml = self.settings.get("daily_goal_ml", 2000)
        progress_percent = min(100.0, (total_ml / goal_ml) * 100.0) if goal_ml > 0 else 0
        self.progress_var.set(progress_percent)
        self.progress_label.config(text=f"{total_ml} / {goal_ml} ml ({progress_percent:.1f}%)")

        # Update the custom canvas progress bar
        self._update_progress_bar(progress_percent)

        # Update the goal estimates display
        self._update_goal_estimates()

        # Update the graph
        if MATPLOTLIB_AVAILABLE:
            self._update_graph()

    def _update_progress_bar(self, percent: float):
        """Update the canvas progress bar width and color."""
        width = self.progress_canvas.winfo_width()
        # If the canvas has not been drawn yet, schedule an update after idle
        if width <= 1:
            self.after(10, lambda: self._update_progress_bar(percent))
            return

        fill_width = int(width * (percent / 100.0))
        self.progress_canvas.coords(self._progress_bar_item, 0, 0, fill_width, 20)

        if percent >= 100:
            color = "#6BCF7F"  # green
        elif percent >= 75:
            color = "#FFD93D"  # yellow
        else:
            color = "#FF6B6B"  # red

        self.progress_canvas.itemconfigure(self._progress_bar_item, fill=color)

    def _update_goal_estimates(self):
        """Calculate and display how many of each preset are needed to reach the goal."""
        goal_ml = self.settings.get("daily_goal_ml", 2000)
        current_ml = 0

        # Calculate current total (same logic as update_stats)
        today = date.today()
        for e in self.log:
            try:
                ts = datetime.fromisoformat(e["timestamp"]) if isinstance(e["timestamp"], str) else None
            except Exception:
                ts = None
            if ts is None:
                current_ml += e.get("amount_ml", 0)
            else:
                if ts.date() == today:
                    current_ml += e.get("amount_ml", 0)

        remaining_ml = max(0, goal_ml - current_ml)

        # Enable text widget for editing
        self.estimates_text.config(state=tk.NORMAL)
        self.estimates_text.delete(1.0, tk.END)

        if remaining_ml == 0:
            self.estimates_text.insert(tk.END, "🎉 Goal reached!")
        else:
            self.estimates_text.insert(tk.END, f"Need {remaining_ml} ml more:\n\n")
            for preset in self.presets:
                preset_ml = preset.get("ml", 0)
                if preset_ml > 0:
                    count = remaining_ml / preset_ml
                    label = preset.get("label", f"{preset_ml} ml")
                    if count >= 1:
                        self.estimates_text.insert(tk.END, f"• {count:.1f} × {label}\n")
                    else:
                        self.estimates_text.insert(tk.END, f"• {count:.2f} × {label}\n")

        # Adjust height so all lines are visible (up to a maximum for practical UI)
        lines = int(self.estimates_text.index('end-1c').split('.')[0])
        self.estimates_text.config(height=min(max(5, lines), 16))

        # Disable text widget again
        self.estimates_text.config(state=tk.DISABLED)

    def _get_daily_totals(self, days=7):
        """Calculate daily water intake totals for the past N days."""
        daily_totals = {}
        today = date.today()
        
        for i in range(days):
            current_date = today - timedelta(days=i)
            daily_totals[current_date] = 0
        
        # Sum up amounts by date
        for entry in self.log:
            try:
                ts = datetime.fromisoformat(entry["timestamp"]) if isinstance(entry["timestamp"], str) else None
                if ts:
                    entry_date = ts.date()
                    if entry_date in daily_totals:
                        daily_totals[entry_date] += entry.get("amount_ml", 0)
            except Exception:
                pass
        
        # Sort by date ascending
        sorted_dates = sorted(daily_totals.keys())
        return sorted_dates, [daily_totals[d] for d in sorted_dates]

    def _update_graph(self):
        """Update the daily intake trend graph."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Clear previous graph
        for widget in self.graph_canvas_widget.winfo_children():
            widget.destroy()
        
        # Get daily totals
        dates, totals = self._get_daily_totals(days=7)
        
        if not dates:
            ttk.Label(self.graph_canvas_widget, text="No data to display").pack()
            return
        
        # Create matplotlib figure
        fig = Figure(figsize=(8, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot daily totals
        date_labels = [d.strftime("%m-%d") for d in dates]
        ax.bar(date_labels, totals, color="#4CAF50", alpha=0.7, edgecolor="#2E7D32")
        
        # Add goal line
        goal_ml = self.settings.get("daily_goal_ml", 2000)
        ax.axhline(y=goal_ml, color="red", linestyle="--", label=f"Goal: {goal_ml} ml", linewidth=2)
        
        ax.set_ylabel("Water (ml)")
        ax.set_xlabel("Date")
        ax.set_title("Daily Water Intake")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_canvas_widget)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def clear_today(self):
        today = date.today()
        new_log = []
        for e in self.log:
            try:
                ts = datetime.fromisoformat(e["timestamp"]) if isinstance(e["timestamp"], str) else None
            except Exception:
                ts = None
            if ts is None or ts.date() != today:
                new_log.append(e)
        self.log = new_log
        save_log(self.log)
        self.update_stats()

    def export_json(self):
        out_name = os.path.join(os.path.dirname(__file__), f"water_export_{int(time.time())}.json")
        with open(out_name, "w", encoding="utf-8") as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exported", f"Saved to {out_name}")

    def start_reminders(self):
        if self.reminder_thread is not None:
            messagebox.showinfo("Reminders", "Reminders already running.")
            return
        try:
            mins = int(self.reminder_interval_var.get())
        except Exception:
            messagebox.showerror("Invalid interval", "Enter an numeric minutes value.")
            return
        self.reminder_thread = ReminderThread(mins, self._show_reminder, self)
        self.reminder_thread.start()
        self.reminder_start_btn.config(state=tk.DISABLED)
        self.reminder_stop_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Reminders", f"Reminders started every {mins} minutes.")

    def stop_reminders(self):
        if self.reminder_thread is None:
            return
        self.reminder_thread.stop()
        self.reminder_thread = None
        self.reminder_start_btn.config(state=tk.NORMAL)
        self.reminder_stop_btn.config(state=tk.DISABLED)

    def _show_reminder(self):
        try:
            messagebox.showinfo("Hydration Reminder", "Time to drink water! Log what you drank.")
        except Exception:
            try:
                self.bell()
            except Exception:
                pass


def main():
    app = WaterTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
