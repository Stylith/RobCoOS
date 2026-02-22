import os
import json
import curses
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent
SETTINGS_FILE = base_dir / "settings.json"
APPS_FILE     = base_dir / "apps.json"
GAMES_FILE    = base_dir / "games.json"
DOCS_FILE     = base_dir / "documents.json"
NETWORKS_FILE = base_dir / "networks.json"
ABOUT_FILE    = base_dir / "about.json"

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".txt", ".mobi", ".azw3"}

# ─── JSON helpers ─────────────────────────────────────────────────────────────
def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_json(path, data):
    path.write_text(json.dumps(data, indent=4))

def load_settings(): return load_json(SETTINGS_FILE)
def save_settings(d): save_json(SETTINGS_FILE, d)

def load_apps():        return load_json(APPS_FILE)
def save_apps(d):       save_json(APPS_FILE, d)
def load_games():       return load_json(GAMES_FILE)
def save_games(d):      save_json(GAMES_FILE, d)
def load_networks():    return load_json(NETWORKS_FILE)
def save_networks(d):   save_json(NETWORKS_FILE, d)
def load_categories():  return load_json(DOCS_FILE)
def save_categories(d): save_json(DOCS_FILE, d)
def load_about():       return load_json(ABOUT_FILE)
def save_about(d):      save_json(ABOUT_FILE, d)

# ─── Settings state ───────────────────────────────────────────────────────────
_settings = load_settings()
SOUND_ON      = _settings.get("sound", True)
BOOTUP_ON     = _settings.get("bootup", True)
CURRENT_THEME = _settings.get("theme", "Green (Default)")

def set_sound(val):
    global SOUND_ON
    SOUND_ON = val

def set_bootup(val):
    global BOOTUP_ON
    BOOTUP_ON = val

def set_theme(val):
    global CURRENT_THEME
    CURRENT_THEME = val

def save_all_settings():
    save_settings({"sound": SOUND_ON, "bootup": BOOTUP_ON, "theme": CURRENT_THEME})

# ─── Sound ────────────────────────────────────────────────────────────────────
try:
    from playsound import playsound as _playsound_impl
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False
    _playsound_impl = None

def playsound(path, block=True):
    if SOUND_ENABLED and SOUND_ON and _playsound_impl is not None:
        try:
            _playsound_impl(path, block)
        except Exception:
            pass

# ─── Colors ───────────────────────────────────────────────────────────────────
COLOR_NORMAL   = 1
COLOR_SELECTED = 2
COLOR_TITLE    = 3
COLOR_STATUS   = 4
COLOR_DIM      = 5

THEMES = {
    "Green (Default)": (curses.COLOR_GREEN,   -1),
    "White":           (curses.COLOR_WHITE,   -1),
    "Amber":           (curses.COLOR_YELLOW,  -1),
    "Blue":            (curses.COLOR_BLUE,    -1),
    "Red":             (curses.COLOR_RED,     -1),
    "Purple":          (curses.COLOR_MAGENTA, -1),
    "Light Blue":      (curses.COLOR_CYAN,    -1),
}

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    fg, bg = THEMES.get(CURRENT_THEME, THEMES["Green (Default)"])
    curses.init_pair(COLOR_NORMAL,   fg,                  bg)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK,  fg)
    curses.init_pair(COLOR_TITLE,    fg,                  bg)
    curses.init_pair(COLOR_STATUS,   curses.COLOR_BLACK,  fg)
    curses.init_pair(COLOR_DIM,      fg,                  bg)

# ─── Header ───────────────────────────────────────────────────────────────────
HEADER_LINES = [
    "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM",
    "COPYRIGHT 2075-2077 ROBCO INDUSTRIES",
    "-SERVER 1-",
]

# ─── Tmux / desktop ───────────────────────────────────────────────────────────
SESSION_NAME  = "robcos"
NUM_WINDOWS   = 4

# ─── Input timeout (halfdelay units = tenths of a second) ─────────────────────
# 2 = 200ms: getch returns -1 if no key pressed, used to drive status redraws
INPUT_TIMEOUT = 2
