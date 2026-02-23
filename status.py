import os
import curses
import time
import subprocess
import psutil
from datetime import datetime
from config import (COLOR_TITLE, COLOR_STATUS, COLOR_DIM, HEADER_LINES, INPUT_TIMEOUT, SHOW_STATUS)

# ─── Drawing helpers ──────────────────────────────────────────────────────────
def draw_header(win):
    h, w = win.getmaxyx()
    for i, line in enumerate(HEADER_LINES):
        x = max(0, (w - len(line)) // 2)
        try:
            win.addstr(i, x, line, curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
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

# ─── Tmux tab cache ───────────────────────────────────────────────────────────
# Only shell out every 2 seconds instead of every getch timeout
_tab_cache_value = ""
_tab_cache_time  = 0.0
_TAB_TTL         = 2.0

def _get_tmux_tabs():
    global _tab_cache_value, _tab_cache_time
    now = time.monotonic()
    if now - _tab_cache_time < _TAB_TTL:
        return _tab_cache_value
    try:
        if "TMUX" not in os.environ:
            _tab_cache_value = ""
            _tab_cache_time  = now
            return ""
        cur = subprocess.run(
            ["tmux", "display-message", "-p", "#I"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip()
        wins = subprocess.run(
            ["tmux", "list-windows", "-F", "#I"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip().split()
        if wins and cur:
            result = "  ".join(f"[{w}*]" if w == cur else f"[{w}]" for w in wins)
        else:
            result = ""
    except Exception:
        result = _tab_cache_value  # keep last good value on failure
    _tab_cache_value = result
    _tab_cache_time  = now
    return result

# ─── Status bar ───────────────────────────────────────────────────────────────
def draw_status(win):
    import config as _cfg
    if not _cfg.SHOW_STATUS:
        return
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
        batt = f"{battery.percent:.0f} %"
        try:
            win.addstr(h - 1, w - 2 - len(batt), batt,
                       curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
        except curses.error:
            pass

    # Center: tmux tabs
    if "TMUX" in os.environ:
        tabs = _get_tmux_tabs()
        if tabs:
            x = max(0, (w - len(tabs)) // 2)
            try:
                win.addstr(h - 1, x, tabs,
                           curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
            except curses.error:
                pass
