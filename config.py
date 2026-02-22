import os
import json
import curses
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
base_dir  = Path(__file__).resolve().parent
USERS_DIR = base_dir / "users"          # users/{username}/*.json
USERS_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = base_dir / "settings.json"   # global fallback
APPS_FILE     = base_dir / "apps.json"
GAMES_FILE    = base_dir / "games.json"
DOCS_FILE     = base_dir / "documents.json"
NETWORKS_FILE = base_dir / "networks.json"
ABOUT_FILE    = base_dir / "about.json"

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".txt", ".mobi", ".azw3"}

# ─── Current user (set after login) ──────────────────────────────────────────
_current_user: str | None = None

def set_current_user(username: str):
    global _current_user
    _current_user = username
    # Load this user's settings into globals immediately
    _load_user_settings()

def get_current_user() -> str | None:
    return _current_user

def _user_dir(username: str | None = None) -> Path | None:
    u = username or _current_user
    if not u:
        return None
    d = USERS_DIR / u
    d.mkdir(exist_ok=True)
    return d

# ─── JSON helpers ─────────────────────────────────────────────────────────────
def load_json(path):
    if Path(path).exists():
        return json.loads(Path(path).read_text())
    return {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=4))

# ─── User-aware loaders ───────────────────────────────────────────────────────
# Each returns the user's personal file if it exists, else the global file.
# Each saver always writes to the user's personal file.

def _user_file(filename: str) -> Path:
    d = _user_dir()
    if d:
        return d / filename
    return base_dir / filename   # fallback for no-user mode

def load_apps():        return load_json(_user_file("apps.json"))
def save_apps(d):       save_json(_user_file("apps.json"), d)

def load_games():       return load_json(_user_file("games.json"))
def save_games(d):      save_json(_user_file("games.json"), d)

def load_networks():    return load_json(_user_file("networks.json"))
def save_networks(d):   save_json(_user_file("networks.json"), d)

# Documents/categories: per-user, falls back to global
def load_categories():  return load_json(_user_file("documents.json"))
def save_categories(d): save_json(_user_file("documents.json"), d)

def load_about():       return load_json(ABOUT_FILE)
def save_about(d):      save_json(ABOUT_FILE, d)

# Settings: per-user, falls back to global defaults
def load_settings():
    d = _user_dir()
    if d:
        f = d / "settings.json"
        if f.exists():
            return load_json(f)
    return load_json(SETTINGS_FILE)   # global fallback

def save_settings(data):
    d = _user_dir()
    if d:
        save_json(d / "settings.json", data)
    else:
        save_json(SETTINGS_FILE, data)

# ─── Settings state ───────────────────────────────────────────────────────────
_settings     = load_json(SETTINGS_FILE)   # global defaults on startup
SOUND_ON      = _settings.get("sound",  True)
BOOTUP_ON     = _settings.get("bootup", True)
CURRENT_THEME = _settings.get("theme",  "Green (Default)")

def _load_user_settings():
    """Reload globals from the logged-in user's settings file."""
    global SOUND_ON, BOOTUP_ON, CURRENT_THEME
    s = load_settings()
    SOUND_ON      = s.get("sound",  True)
    BOOTUP_ON     = s.get("bootup", True)
    CURRENT_THEME = s.get("theme",  "Green (Default)")
    init_colors()   # re-apply theme immediately

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
    try:
        curses.start_color()
        curses.use_default_colors()
        fg, bg = THEMES.get(CURRENT_THEME, THEMES["Green (Default)"])
        curses.init_pair(COLOR_NORMAL,   fg,                  bg)
        curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK,  fg)
        curses.init_pair(COLOR_TITLE,    fg,                  bg)
        curses.init_pair(COLOR_STATUS,   curses.COLOR_BLACK,  fg)
        curses.init_pair(COLOR_DIM,      fg,                  bg)
    except Exception:
        pass   # curses not yet initialised (e.g. during import)

# ─── Header ───────────────────────────────────────────────────────────────────
HEADER_LINES = [
    "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM",
    "COPYRIGHT 2075-2077 ROBCO INDUSTRIES",
    "-SERVER 1-",
]

# ─── Tmux / desktop ───────────────────────────────────────────────────────────
SESSION_NAME = "robcos"
NUM_WINDOWS  = 4

# ─── Input timeout ────────────────────────────────────────────────────────────
INPUT_TIMEOUT = 2