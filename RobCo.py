import os
import sys
import time
import subprocess
import json
import shlex
import curses
import threading
import pty
import shutil
import select
import itertools
import random
import psutil
import pyte
from pathlib import Path
from datetime import date, datetime

# ─── Sound ────────────────────────────────────────────────────────────────────
try:
    from playsound import playsound as _playsound_impl
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False
    _playsound_impl = None

SETTINGS_FILE = Path("settings.json")

def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_json(path, data):
    path.write_text(json.dumps(data, indent=4))

def load_settings(): return load_json(SETTINGS_FILE)
def save_settings(d): save_json(SETTINGS_FILE, d)

_settings = load_settings()
SOUND_ON = _settings.get("sound", True)
BOOTUP_ON = _settings.get("bootup", True)
CURRENT_THEME = _settings.get("theme", "Green")

def playsound(path, block=True):
    if SOUND_ENABLED and SOUND_ON and _playsound_impl is not None:
        try:
            _playsound_impl(path, block)
        except Exception:
            pass

# ─── Base dir ─────────────────────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent
if base_dir.is_dir():
    os.chdir(base_dir)

# ─── Colors ───────────────────────────────────────────────────────────────────
COLOR_NORMAL   = 1
COLOR_SELECTED = 2
COLOR_TITLE    = 3
COLOR_STATUS   = 4
COLOR_DIM      = 5
THEMES = {
    "Green (Default)": (curses.COLOR_GREEN,   -1),
    "White":      (curses.COLOR_WHITE,   -1),
    "Amber":      (curses.COLOR_YELLOW,  -1),
    "Blue":       (curses.COLOR_BLUE,    -1),
    "Red":        (curses.COLOR_RED,     -1),
    "Purple":     (curses.COLOR_MAGENTA, -1),
    "Light Blue": (curses.COLOR_CYAN,    -1),
}

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    fg, bg = THEMES.get(CURRENT_THEME, THEMES["Green (Default)"])
    curses.init_pair(COLOR_NORMAL,   fg,              bg)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK, fg)
    curses.init_pair(COLOR_TITLE,    fg,              bg)
    curses.init_pair(COLOR_STATUS,   curses.COLOR_BLACK, fg)
    curses.init_pair(COLOR_DIM,      fg,              bg)

# ─── Drawing helpers ──────────────────────────────────────────────────────────
HEADER_LINES = [
    "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM",
    "COPYRIGHT 2075-2077 ROBCO INDUSTRIES",
    "-SERVER 1-",
]

def draw_header(win):
    h, w = win.getmaxyx()
    for i, line in enumerate(HEADER_LINES):
        x = max(0, (w - len(line)) // 2)
        try:
            win.addstr(i, x, line, curses.color_pair(COLOR_TITLE) | curses.A_BOLD)
        except curses.error:
            pass

def draw_status(win):
    h, w = win.getmaxyx()
    now = datetime.today().strftime("%A, %d. %B - %I:%M%p")
    status = f"{now}"
    status = status.ljust(w)[:w - 1]
    battery = psutil.sensors_battery()
    batt_percent = battery.percent
    batt_status = f"{batt_percent} %"
    try:
        win.addstr(h - 1, 0, status, curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
    except curses.error:
        pass
    try:
        if battery is None:
            batt_status = ""
        win.addstr(h-1, w - 2 - len(batt_status), batt_status, curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
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

# ─── Generic curses menu ──────────────────────────────────────────────────────
def run_menu(stdscr, title, choices, subtitle=""):
    selectable = [c for c in choices if c != "---"]
    idx = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr)
        draw_separator(stdscr, 4, w)
        draw_menu_title(stdscr, title, 5)
        draw_separator(stdscr, 6, w)
        if subtitle:
            try:
                stdscr.addstr(8, 6, subtitle, curses.color_pair(COLOR_DIM) | curses.A_UNDERLINE)
            except curses.error:
                pass

        start_row = 10 if subtitle else 9
        for di, choice in enumerate(choices):
            row = start_row + di
            if row >= h - 2:
                break
            is_sep = choice == "---"
            is_selected = (not is_sep) and (choice == selectable[idx])
            prefix = "  > " if is_selected else "    "
            text = prefix + choice
            attr = (curses.color_pair(COLOR_DIM) if is_sep else
                    curses.color_pair(COLOR_SELECTED) | curses.A_BOLD if is_selected else
                    curses.color_pair(COLOR_NORMAL))
            try:
                stdscr.addstr(row, 2, text[:w - 4], attr)
            except curses.error:
                pass

        draw_status(stdscr)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            idx = (idx - 1) % len(selectable) if selectable else 0
        elif key in (curses.KEY_DOWN, ord('j')):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            idx = (idx + 1) % len(selectable) if selectable else 0
        elif key in (curses.KEY_ENTER, 10, 13, 32):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            return selectable[idx] if selectable else None
        elif key in (ord('q'), ord('Q'), 27, 9):
            playsound('Sounds/ui_hacking_charenter_01.wav', False)
            return "Back"

# ─── Input helpers ────────────────────────────────────────────────────────────
def curses_input(stdscr, prompt):
    global status_paused
    status_paused = True
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    draw_header(stdscr)
    try:
        stdscr.addstr(5, 2, prompt, curses.color_pair(COLOR_TITLE) | curses.A_UNDERLINE)
        stdscr.addstr(7, 2, "> ", curses.color_pair(COLOR_NORMAL))
    except curses.error:
        pass
    curses.echo()
    curses.curs_set(1)
    stdscr.refresh()
    try:
        inp = stdscr.getstr(7, 4, w - 6).decode("utf-8")
    except Exception:
        inp = ""
    curses.noecho()
    curses.curs_set(0)
    status_paused = False
    return inp.strip()

def curses_confirm(stdscr, message):
    global status_paused
    status_paused = True
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    draw_header(stdscr)
    full = message + " (y/n): "
    try:
        stdscr.addstr(5, 2, full, curses.color_pair(COLOR_NORMAL))
    except curses.error:
        pass
    curses.echo()
    curses.curs_set(1)
    stdscr.refresh()
    try:
        ans = stdscr.getstr(5, 2 + len(full), 3).decode("utf-8").strip().lower()
    except Exception:
        ans = ""
    curses.noecho()
    curses.curs_set(0)
    status_paused = False
    return ans == "y"

def curses_message(stdscr, message, delay=1.5):
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    draw_header(stdscr)
    try:
        stdscr.addstr(6, 2, message, curses.color_pair(COLOR_NORMAL))
    except curses.error:
        pass
    draw_status(stdscr)
    stdscr.refresh()
    time.sleep(delay)

def curses_pager(stdscr, text, title=""):
    lines = text.split("\n")
    offset = 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr)
        if title:
            draw_menu_title(stdscr, title, 4)
        max_lines = h - 8
        for i, line in enumerate(lines[offset:offset + max_lines]):
            try:
                stdscr.addstr(5 + i, 2, line[:w - 4], curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass
        nav = "up/down scroll  q/tab=back  Press enter to continue"
        try:
            stdscr.addstr(h - 2, 2, nav, curses.color_pair(COLOR_DIM))
        except curses.error:
            pass
        draw_status(stdscr)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')) and offset > 0:
            offset -= 1
        elif key in (curses.KEY_DOWN, ord('j')) and offset < max(0, len(lines) - max_lines):
            offset += 1
        elif key in (ord('q'), ord('Q'), 27, 9, curses.KEY_ENTER, 10, 13):
            break

def curses_box_message(stdscr, message, delay=2):
    h, w = stdscr.getmaxyx()
    box_w = len(message) + 6
    box_h = 5
    x = (w - box_w) // 2
    y = (h - box_h) // 2
    for row in range(box_h):
        for col in range(box_w):
            try:
                if row == 0 or row == box_h - 1:
                    stdscr.addch(y + row, x + col, '=', curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                elif col == 0 or col == box_w - 1:
                    stdscr.addch(y + row, x + col, '|', curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                else:
                    stdscr.addch(y + row, x + col, ' ', curses.color_pair(COLOR_SELECTED))
            except curses.error:
                pass
    try:
        stdscr.addstr(y + 2, x + 3, message, curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.refresh()
    time.sleep(delay)

# ─── Data helpers ─────────────────────────────────────────────────────────────
APPS_FILE     = Path("apps.json")
GAMES_FILE    = Path("games.json")
DOCS_FILE     = Path("documents.json")
NETWORKS_FILE = Path("networks.json")
ALLOWED_EXTENSIONS = {".pdf", ".epub", ".txt", ".mobi", ".azw3"}

def load_apps():        return load_json(APPS_FILE)
def save_apps(d):       save_json(APPS_FILE, d)
def load_games():       return load_json(GAMES_FILE)
def save_games(d):      save_json(GAMES_FILE, d)
def load_networks():    return load_json(NETWORKS_FILE)
def save_networks(d):   save_json(NETWORKS_FILE, d)
def load_categories():  return load_json(DOCS_FILE)
def save_categories(d): save_json(DOCS_FILE, d)

def scan_documents(folder: Path):
    return [f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS]

# ─── Subprocess launcher ──────────────────────────────────────────────────────
def _suspend(stdscr):
    global status_paused
    status_paused = True
    time.sleep(1.1)
    curses.endwin()
    os.system('tput reset')

def _resume(stdscr):
    global status_paused
    os.system('clear')
    curses.reset_prog_mode()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()
    stdscr.clearok(True)
    stdscr.clear()
    stdscr.refresh()
    status_paused = False

def launch_subprocess(stdscr, cmd):
    _suspend(stdscr)
    subprocess.run(cmd)
    _resume(stdscr)

def launch_vim(stdscr, path):
    _suspend(stdscr)
    subprocess.run(['vim', str(path)])
    _resume(stdscr)

def launch_epy(stdscr, path):
    _suspend(stdscr)
    subprocess.run(['epy', str(path)])
    _resume(stdscr)

# ─── Journal ──────────────────────────────────────────────────────────────────
def journal_new(stdscr):
    global status_paused
    current_date = date.today()
    x = Path("journal_entries")
    x.mkdir(exist_ok=True)
    status_paused = True
    text = curses_input(stdscr, f"New Entry - {current_date}")
    status_paused = False
    if text:
        file_name = x / f"{current_date}.txt"
        with open(file_name, "a") as f:
            f.write(text + "\n")
        curses_message(stdscr, "Entry saved.")

def journal_view(stdscr):
    directory_path = Path("journal_entries")
    if not directory_path.exists():
        curses_message(stdscr, "Error: journal_entries folder not found.")
        return
    logs = [f for f in directory_path.iterdir() if f.is_file()]
    if not logs:
        curses_message(stdscr, "Error: Log folder empty.")
        return
    file_map = {f.stem: f for f in logs}
    options = sorted(file_map.keys()) + ["Back"]
    while True:
        result = run_menu(stdscr, "View Logs", options)
        if result == "Back":
            break
        if result in file_map:
            text = file_map[result].read_text()
            curses_pager(stdscr, text, title=result)

def journal_delete(stdscr):
    directory_path = Path("journal_entries")
    if not directory_path.exists():
        curses_message(stdscr, "Error: journal_entries folder not found.")
        return
    logs = [f for f in directory_path.iterdir() if f.is_file()]
    if not logs:
        curses_message(stdscr, "Error: Log folder empty.")
        return
    file_map = {f.stem: f for f in logs}
    options = sorted(file_map.keys()) + ["Back"]
    result = run_menu(stdscr, "Delete Log", options)
    if result == "Back" or result not in file_map:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        file_map[result].unlink()
        curses_message(stdscr, f"Deleted {result}.")

# ─── Generic add/delete ───────────────────────────────────────────────────────
def add_entry(stdscr, data, save_fn, kind="App"):
    name = curses_input(stdscr, f"Enter {kind} display name:")
    if not name:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    command = curses_input(stdscr, f"Enter launch command for '{name}':")
    if not command:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    data[name] = shlex.split(command)
    save_fn(data)
    curses_message(stdscr, f"{name} added.")

def delete_entry(stdscr, data, save_fn, kind="App"):
    if not data:
        curses_message(stdscr, f"Error: {kind} list is empty.")
        return
    options = list(data.keys()) + ["Back"]
    result = run_menu(stdscr, f"Delete {kind}", options)
    if result == "Back" or result not in data:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        del data[result]
        save_fn(data)
        curses_message(stdscr, f"{result} deleted.")
    else:
        curses_message(stdscr, "Cancelled.", 0.8)

def add_category(stdscr, categories):
    name = curses_input(stdscr, "Enter category name:")
    if not name:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    path_input = curses_input(stdscr, "Enter folder path:")
    path = Path(path_input).expanduser()
    if not path.exists() or not path.is_dir():
        curses_message(stdscr, "Error: Invalid Directory.")
        return
    categories[name] = str(path)
    save_categories(categories)
    curses_message(stdscr, "Category Added.")

def delete_category(stdscr, categories):
    if not categories:
        curses_message(stdscr, "Error: No categories to delete.")
        return
    options = list(categories.keys()) + ["Back"]
    result = run_menu(stdscr, "Delete Category", options)
    if result == "Back" or result not in categories:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        del categories[result]
        save_categories(categories)
        curses_message(stdscr, "Deleted.")
    else:
        curses_message(stdscr, "Cancelled.", 0.8)

#--------------------------App Store--------------------------------------------


PACKAGE_MANAGERS = {
    'brew':    [],
    'apt':     ['-y'],
    'apt-get': ['-y'],
    'dnf':     ['-y'],
    'pacman':  ['--noconfirm'],
    'zypper':  ['-n'],
}

def has_internet():
    try:
        import urllib.request
        urllib.request.urlopen("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False

def detect_package_manager():
    for pm in PACKAGE_MANAGERS:
        if shutil.which(pm):
            return pm
    return None

def is_installed(cmd):
    return shutil.which(cmd) is not None

def search_packages(pm, query):
    try:
        result = subprocess.run([pm, "search", query],
                                capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split("\n")
        return [l for l in lines if l.strip() and not l.startswith("=")]
    except Exception:
        return []

def get_package_info(pm, pkg):
    try:
        if pm == "brew":
            result = subprocess.run(["brew", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            # First line is usually "name: description"
            lines = result.stdout.strip().split("\n")
            return lines[1].strip() if len(lines) > 1 else "No description available."

        elif pm in ("apt", "apt-get"):
            result = subprocess.run(["apt", "show", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Description:"):
                    return line.replace("Description:", "").strip()

        elif pm == "dnf":
            result = subprocess.run(["dnf", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Summary"):
                    return line.split(":", 1)[-1].strip()

        elif pm == "pacman":
            result = subprocess.run(["pacman", "-Si", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Description"):
                    return line.split(":", 1)[-1].strip()

        elif pm == "zypper":
            result = subprocess.run(["zypper", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Summary"):
                    return line.split(":", 1)[-1].strip()

        return "No description available."
    except Exception:
        return "Could not fetch description."

def get_installed_packages(pm):
    try:
        if pm == "brew":
            result = subprocess.run(["brew", "list"], capture_output=True, text=True, timeout=10)
        elif pm in ("apt", "apt-get"):
            result = subprocess.run(["apt", "list", "--installed"], capture_output=True, text=True, timeout=10)
        elif pm == "dnf":
            result = subprocess.run(["dnf", "list", "installed"], capture_output=True, text=True, timeout=10)
        elif pm == "pacman":
            result = subprocess.run(["pacman", "-Q"], capture_output=True, text=True, timeout=10)
        elif pm == "zypper":
            result = subprocess.run(["zypper", "se", "--installed-only"], capture_output=True, text=True, timeout=10)
        else:
            return []
        return [l.split()[0] for l in result.stdout.strip().split("\n") if l.strip() and not l.startswith("WARNING")]
    except Exception:
        return []

def appstore_menu(stdscr):
    pm = detect_package_manager()
    MAX_PER_PAGE = 20

    while True:
        result = run_menu(stdscr, "Program Installer", ["Search", "Installed Apps", "---", "Back"],
                          subtitle=f"Package Manager: {pm or 'Not Found'}")
        if result == "Back":
            break
        elif result == "Search":
            query = curses_input(stdscr, "Search packages:")
            if not query:
                continue
            if not has_internet():
                curses_message(stdscr, "Error: No internet connection")
                continue
            curses_message(stdscr, "Searching...", 0.5)
            results = search_packages(pm, query)

            if not results:
                curses_message(stdscr, "No results found.")
                continue

            page = 0
            while True:
                start = page * MAX_PER_PAGE
                end = start + MAX_PER_PAGE
                page_results = results[start:end]
                total_pages = (len(results) - 1) // MAX_PER_PAGE + 1

                choices = []
                for r in page_results:
                    cmd = r.split()[0]
                    status = "[installed]" if is_installed(cmd) else "[get]      "
                    choices.append(f"{status} {r}")

                if page > 0:
                    choices.append("< Prev Page")
                if end < len(results):
                    choices.append("> Next Page")
                choices += ["---", "Back"]

                pkg_result = run_menu(stdscr, "Program Installer", choices,
                                      subtitle=f"Results: {query}  |  Page {page + 1}/{total_pages}")
                if pkg_result == "Back":
                    break
                elif pkg_result == "> Next Page":
                    page += 1
                elif pkg_result == "< Prev Page":
                    page -= 1
                else:
                    pkg = pkg_result.split()[1]
                    if is_installed(pkg):
                        curses_message(stdscr, f"{pkg} is already installed.")
                    elif pm is None:
                        curses_message(stdscr, "Error: No supported package manager found.")
                    else:
                        info = get_package_info(pm, pkg) if has_internet() else "No internet - description unavailable."
                        curses_pager(stdscr, f"{pkg}\n\n{info}", title="Package Info")
                        if curses_confirm(stdscr, f"Install {pkg}?"):
                            flags = PACKAGE_MANAGERS.get(pm, [])
                            if pm == "brew":
                                launch_cmd = [pm, "install"] + flags + [pkg]
                            else:
                                launch_cmd = ["sudo", pm, "install"] + flags + [pkg]
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} installed successfully!")
                            else:
                                curses_box_message(stdscr, f"Failed to install {pkg}.")

        elif result == "Installed Apps":
            curses_message(stdscr, "Loading...", 0.5)
            installed = get_installed_packages(pm)
            if not installed:
                curses_message(stdscr, "No installed packages found.")
                continue
            filter_query = ""
            page = 0
            while True:
                h, w = stdscr.getmaxyx()
                max_items = max(3, h - 18)
                filtered = [p for p in installed if filter_query.lower() in p.lower()] if filter_query else installed
                start = page * max_items
                end = start + max_items
                page_results = filtered[start:end]
                total_pages = max(1, (len(filtered) - 1) // max_items + 1)

                search_label = f"Search: {filter_query}" if filter_query else "Search..."
                choices = [search_label, "---"] + [f"  {p}" for p in page_results]
                if page > 0:
                    choices.append("< Prev Page")
                if end < len(filtered):
                    choices.append("> Next Page")
                choices += ["---", "Back"]

                pkg_result = run_menu(stdscr, "Installed Apps", choices,
                                      subtitle=f"{len(filtered)} packages  |  Page {page + 1}/{total_pages}")
                if pkg_result == "Back":
                    break
                elif pkg_result == "> Next Page":
                    page += 1
                elif pkg_result == "< Prev Page":
                    page -= 1
                elif pkg_result == search_label:
                    filter_query = curses_input(stdscr, "Filter packages:")
                    page = 0
                else:
                    pkg = pkg_result.strip()
                    info = get_package_info(pm, pkg) if has_internet() else "No internet - description unavailable."
                    action = run_menu(stdscr, pkg, ["Update", "Uninstall", "---", "Back"],
                                      subtitle=info)
                    if action == "Uninstall":
                        if curses_confirm(stdscr, f"Uninstall {pkg}?"):
                            flags = PACKAGE_MANAGERS.get(pm, [])
                            if pm == "brew":
                                launch_cmd = [pm, "uninstall"] + flags + [pkg]
                            else:
                                launch_cmd = ["sudo", pm, "remove"] + flags + [pkg]
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} uninstalled.")
                                installed = get_installed_packages(pm)
                            else:
                                curses_box_message(stdscr, f"Failed to uninstall {pkg}.")
                    elif action == "Update":
                        if not has_internet():
                            curses_message(stdscr, "Error: No internet connection.")
                        else:
                            if pm == "brew":
                                launch_cmd = [pm, "upgrade", pkg]
                            else:
                                launch_cmd = ["sudo", pm, "upgrade"] + [pkg]
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} updated.")
                            else:
                                curses_box_message(stdscr, f"Failed to update {pkg}.")

        
# ─── Menus ────────────────────────────────────────────────────────────────────
def logs_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Logs Menu",
                          ["Create New Log", "View Logs", "Delete Logs", "Back"])
        if result == "Back":
            break
        elif result == "Create New Log":
            journal_new(stdscr)
        elif result == "View Logs":
            journal_view(stdscr)
        elif result == "Delete Logs":
            journal_delete(stdscr)

def apps_menu(stdscr):
    while True:
        apps = load_apps()
        choices = list(apps.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Applications Menu", choices, subtitle="Select App")
        if result == "Back":
            break
        elif result in apps:
            launch_subprocess(stdscr, apps[result])

def games_menu(stdscr):
    while True:
        games = load_games()
        choices = list(games.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Games Menu", choices, subtitle="Select Game")
        if result == "Back":
            break
        elif result in games:
            launch_subprocess(stdscr, games[result])

def network_menu(stdscr):
    while True:
        networks = load_networks()
        choices = list(networks.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Network Menu", choices, subtitle="Select Network Program")
        if result == "Back":
            break
        elif result in networks:
            launch_subprocess(stdscr, networks[result])

def documents_menu(stdscr):
    while True:
        categories = load_categories()
        choices = ["Logs"] + list(categories.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Documents Menu", choices, subtitle="Select Document Type")
        if result == "Back":
            break
        elif result == "Logs":
            logs_menu(stdscr)
        elif result in categories:
            folder = Path(categories[result]).expanduser()
            while True:
                files = scan_documents(folder)
                if not files:
                    curses_message(stdscr, "No supported documents found.")
                    break
                files.sort(key=lambda f: f.stem.lower())
                file_map = {f.stem.replace("_", " "): f for f in files}
                file_result = run_menu(stdscr, result, list(file_map.keys()) + ["Back"], subtitle=f"Select {result}")
                if file_result == "Back":
                    break
                if file_result in file_map:
                    launch_epy(stdscr, file_map[file_result])

def edit_apps_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Applications",
                          ["Add App", "Delete App", "---", "Back"])
        if result == "Back":
            break
        elif result == "Add App":
            add_entry(stdscr, load_apps(), save_apps, "App")
        elif result == "Delete App":
            delete_entry(stdscr, load_apps(), save_apps, "App")

def edit_games_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Games",
                          ["Add Game", "Delete Game", "---", "Back"])
        if result == "Back":
            break
        elif result == "Add Game":
            add_entry(stdscr, load_games(), save_games, "Game")
        elif result == "Delete Game":
            delete_entry(stdscr, load_games(), save_games, "Game")

def edit_network_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Network",
                          ["Add Network", "Delete Network", "---", "Back"])
        if result == "Back":
            break
        elif result == "Add Network":
            add_entry(stdscr, load_networks(), save_networks, "Network Program")
        elif result == "Delete Network":
            delete_entry(stdscr, load_networks(), save_networks, "Network Program")

def edit_documents_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Documents",
                          ["Add Category", "Delete Category", "---", "Back"])
        if result == "Back":
            break
        elif result == "Add Category":
            add_category(stdscr, load_categories())
        elif result == "Delete Category":
            delete_category(stdscr, load_categories())

def edit_menus_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Menus",
                          ["Edit Applications", "Edit Documents",
                           "Edit Network", "Edit Games", "---", "Back"])
        if result == "Back":
            break
        elif result == "Edit Applications":
            edit_apps_menu(stdscr)
        elif result == "Edit Documents":
            edit_documents_menu(stdscr)
        elif result == "Edit Network":
            edit_network_menu(stdscr)
        elif result == "Edit Games":
            edit_games_menu(stdscr)

def theme_menu(stdscr):
    global CURRENT_THEME
    result = run_menu(stdscr, "Select Theme", list(THEMES.keys()) + ["---", "Back"])
    if result != "Back" and result in THEMES:
        CURRENT_THEME = result
        save_settings({"sound": SOUND_ON, "bootup": BOOTUP_ON, "theme": CURRENT_THEME})
        init_colors()

# ─── Embedded terminal ────────────────────────────────────────────────────────
def embedded_terminal(stdscr):
    global status_paused
    status_paused = True

    shell = os.environ.get("SHELL", "/bin/bash")
    h, w = stdscr.getmaxyx()

    env = os.environ.copy()
    env["PS1"] = "> "
    env["ZDOTDIR"] = "/dev/null"

    screen = pyte.Screen(w, h - 2)
    stream = pyte.ByteStream(screen)

    pid, fd = pty.fork()

    if pid == 0:
        os.execvpe(shell, [shell, "--no-rcs", "-f"], env)
    else:
        stdscr.keypad(False)
        stdscr.nodelay(True)

        while True:
            h, w = stdscr.getmaxyx()
            screen.resize(h - 2, w)

            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try:
                    data = os.read(fd, 1024)
                    stream.feed(data)
                except OSError:
                    break

            stdscr.erase()

            # Header
            try:
                stdscr.addstr(0, 0, " ROBCO MAINTENANCE TERMLINK ".center(w - 1),
                              curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
            except curses.error:
                pass

            # Terminal output offset by 1 for header
            for row_idx, row in enumerate(screen.display):
                try:
                    stdscr.addstr(row_idx + 1, 0, row[:w - 1])
                except curses.error:
                    pass

            # Footer
            try:
                stdscr.addstr(h - 1, 0, " CTRL+X TO EXIT ".ljust(w - 1),
                              curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
            except curses.error:
                pass

            # Cursor position
            try:
                stdscr.move(screen.cursor.y + 1, screen.cursor.x)
            except curses.error:
                pass

            stdscr.refresh()

            key = stdscr.getch()
            if key == 24:  # Ctrl+X
                os.kill(pid, 9)
                break
            elif key != -1:
                if key < 256:
                    os.write(fd, bytes([key]))
                else:
                    os.write(fd, curses.keyname(key))

        os.waitpid(pid, 0)
        stdscr.keypad(True)
        stdscr.nodelay(False)
        status_paused = False

# ─── Settings ─────────────────────────────────────────────────────────────────
def settings_menu(stdscr):
    global SOUND_ON, BOOTUP_ON
    while True:
        sound_label = "Sound: ON  [toggle]" if SOUND_ON else "Sound: OFF [toggle]"
        bootup_label = "Bootup: ON [toggle]" if BOOTUP_ON else "Bootup: OFF [toggle]"
        result = run_menu(stdscr, "Settings Menu",
                          ["Theme", "Edit Menus", bootup_label, sound_label, "---", "Back"])
        if result == "Back":
            break
        elif result == "Edit Menus":
            edit_menus_menu(stdscr)
        elif result == "Theme":
            theme_menu(stdscr)
        elif result == sound_label:
            SOUND_ON = not SOUND_ON
            save_settings({"sound": SOUND_ON, "bootup": BOOTUP_ON, "theme": CURRENT_THEME})
        elif result == bootup_label:
            BOOTUP_ON = not BOOTUP_ON
            save_settings({"sound": SOUND_ON, "bootup": BOOTUP_ON, "theme": CURRENT_THEME})



# ─── Status bar thread ────────────────────────────────────────────────────────
status_running = True
status_paused = False
_stdscr_ref = None

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

# ─── Boot animation ───────────────────────────────────────────────────────────
def bootup_curses(stdscr):
    stdscr.nodelay(True)

    def skipped():
        return stdscr.getch() == ord(' ')
    sounds= [
        'Sounds/ui_hacking_charsingle_01.wav',
        'Sounds/ui_hacking_charsingle_02.wav',
        'Sounds/ui_hacking_charsingle_03.wav',
        'Sounds/ui_hacking_charsingle_04.wav',
        'Sounds/ui_hacking_charsingle_05.wav',
    ]
    random.shuffle(sounds)

    # (text, char_delay, end_pause, centered)
    sequences = [
        ("WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK\nSET TERMINAL/INQUIRE", 0.02, 2, False),
        ("RIT-V300\n>SET FILE/PROTECTION-OWNER/RFWD ACCOUNTS.F\n>SET HALT RESTART/MAINT", 0.05, 2, False),
        ("ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL\nRETROS BIOS\nRBIOS-4.02.08.00 52EE5.E7.E8\nCopyright 2201-2203 Robco Ind.\nUppermem: 64KB\nRoot (5A8)\nMaintenance Mode", 0.02, 2, False),
        ("LOGON ADMIN", 0.1, 3, False),
        ("ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM\nCOPYRIGHT 2075-2077 ROBCO INDUSTRIES\n-SERVER 1-", 0.05, 2, True),
    ]

    for (text, delay, pause, centered), sound in itertools.zip_longest(sequences, sounds):
        if skipped():
            break
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        text_lines = text.split("\n")
        done = False

        if centered:
            start_row = 0
            for li, line_text in enumerate(text_lines):
                row = start_row + li
                col = max(0, (w - len(line_text)) // 2)
                for ch in line_text:
                    if skipped():
                        done = True
                        break
                    try:
                        stdscr.addch(row, col, ch, curses.color_pair(COLOR_NORMAL))
                        playsound('Sounds/ui_hacking_charscroll.wav', False)
                        col += 1
                    except curses.error:
                        pass
                    stdscr.refresh()
                    time.sleep(delay)
                if done:
                    break
        else:
            row, col = 0, 0
            for ch in text:
                if skipped():
                    done = True
                    break
                if ch == "\n":
                    row += 1
                    col = 0
                else:
                    try:
                        stdscr.addch(row, col, ch, curses.color_pair(COLOR_NORMAL))
                        playsound(random.choice(sounds), False)
                        col += 1
                    except curses.error:
                        pass
                stdscr.refresh()
                time.sleep(delay)

        if done:
            break
        elapsed = 0
        while elapsed < pause:
            if skipped():
                done = True
                break
            time.sleep(0.05)
            elapsed += 0.05
        if done:
            break
        stdscr.erase()

    playsound('Sounds/ui_hacking_passgood.wav')

    stdscr.nodelay(False)
    stdscr.erase()

# ─── Main ─────────────────────────────────────────────────────────────────────
def main(stdscr):
    global _stdscr_ref, status_running
    _stdscr_ref = stdscr

    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    if BOOTUP_ON:
        bootup_curses(stdscr)

    t = threading.Thread(target=status_bar_thread, daemon=True)
    t.start()

    while True:
        result = run_menu(stdscr, "Main Menu",
                          ["Applications", "Documents", "Network", "Games", "Program Installer", "Terminal",
                           "---", "Settings", "Logout"])
        if result == "Logout":
            playsound('Sounds/ui_hacking_passbad.wav', False)
            curses_message(stdscr, "Logging out...", 1)
            break
        elif result == "Applications":
            apps_menu(stdscr)
        elif result == "Documents":
            documents_menu(stdscr)
        elif result == "Games":
            games_menu(stdscr)
        elif result == "Network":
            network_menu(stdscr)
        elif result == "Program Installer":
            appstore_menu(stdscr)
        elif result == "Terminal":
            embedded_terminal(stdscr)
        elif result == "Settings":
            settings_menu(stdscr)

    status_running = False
    _stdscr_ref = None
    t.join(timeout=2)

if __name__ == "__main__":
    stdscr = curses.initscr()
    try:
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        main(stdscr)
    finally:
        stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        os.system('clear')
        sys.exit(0)