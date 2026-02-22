import curses
import time
import psutil
from datetime import datetime
from config import (COLOR_TITLE, COLOR_STATUS, COLOR_DIM,
                    HEADER_LINES)

# ─── Status bar thread state ──────────────────────────────────────────────────
status_running = True
status_paused  = False
_stdscr_ref    = None

def set_status_paused(val):
    global status_paused
    status_paused = val

def set_stdscr_ref(scr):
    global _stdscr_ref
    _stdscr_ref = scr

def stop_status():
    global status_running
    status_running = False

# ─── Drawing helpers ──────────────────────────────────────────────────────────
def draw_header(win):
    h, w = win.getmaxyx()
    for i, line in enumerate(HEADER_LINES):
        x = max(0, (w - len(line)) // 2)
        try:
            win.addstr(i, x, line, curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        except curses.error:
            pass

def _get_tmux_tabs():
    """Return e.g. '[1*] [2] [3] [4]' with * marking the active window."""
    try:
        import os, subprocess
        if "TMUX" not in os.environ:
            return ""
        # Current window index
        cur = subprocess.run(
            ["tmux", "display-message", "-p", "#I"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip()
        # All window indices in the current session (no -t needed when inside tmux)
        wins = subprocess.run(
            ["tmux", "list-windows", "-F", "#I"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip().split()
        if not wins or not cur:
            return ""
        return "  ".join(f"[{w}*]" if w == cur else f"[{w}]" for w in wins)
    except Exception:
        return ""

def draw_status(win):
    import os as _os
    h, w = win.getmaxyx()
    now = datetime.today().strftime("%A, %d. %B - %I:%M%p")

    # Fill bar
    try:
        win.addstr(h - 1, 0, " " * (w - 1), curses.color_pair(COLOR_STATUS))
    except curses.error:
        pass

    # Left: date
    try:
        win.addstr(h - 1, 1, now, curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
    except curses.error:
        pass

    # Right: battery
    battery = psutil.sensors_battery()
    if battery:
        batt_status = f"{battery.percent:.0f} %"
        try:
            win.addstr(h - 1, w - 2 - len(batt_status), batt_status,
                       curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
        except curses.error:
            pass

    # Center: tmux tabs
    if "TMUX" in _os.environ:
        tabs = _get_tmux_tabs()
        if tabs:
            x = max(0, (w - len(tabs)) // 2)
            try:
                win.addstr(h - 1, x, tabs, curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
            except curses.error:
                pass


def draw_separator(win, row, w):
    sep = "=" * min(50, w - 4)
    x = max(0, (w - len(sep)) // 2)
    try:
        win.addstr(row, x, sep, curses.color_pair(COLOR_DIM))
    except curses.error:
        pass

def draw_menu_title(win, title, row):
    h, w = win.getmaxyx()
    x = max(0, (w - len(title)) // 2)
    try:
        win.addstr(row, x, title, curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
    except curses.error:
        pass

# ─── Status bar thread ────────────────────────────────────────────────────────
def status_bar_thread():
    while status_running:
        time.sleep(1)
        if not status_running or status_paused:
            continue
        scr = _stdscr_ref
        if scr is not None:
            try:
                draw_status(scr)
                scr.refresh()
            except Exception:
                pass