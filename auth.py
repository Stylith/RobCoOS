import os
import sys
import json
import curses
import hashlib
import secrets
import tempfile
from pathlib import Path
from config import (COLOR_NORMAL, COLOR_SELECTED, COLOR_TITLE,
                    COLOR_DIM, COLOR_STATUS, init_colors, base_dir)
from status import draw_header, draw_separator, draw_menu_title, draw_status
from ui import run_menu, curses_message, curses_confirm, _halfdelay

USERS_FILE         = base_dir / "users.json"
SESSION_TOKEN_FILE = Path(tempfile.gettempdir()) / "robcos.session"

# ─── Session token ────────────────────────────────────────────────────────────
def write_session(username: str):
    SESSION_TOKEN_FILE.write_text(username)

def read_session() -> str | None:
    if SESSION_TOKEN_FILE.exists():
        val = SESSION_TOKEN_FILE.read_text().strip()
        return val if val else None
    return None

def clear_session():
    if SESSION_TOKEN_FILE.exists():
        try:
            SESSION_TOKEN_FILE.unlink()
        except Exception:
            pass

# ─── Storage ──────────────────────────────────────────────────────────────────
def load_users():
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=4))

# ─── Roles ────────────────────────────────────────────────────────────────────
def is_admin(username: str) -> bool:
    users = load_users()
    return users.get(username, {}).get("role", "user") == "admin"

def get_role(username: str) -> str:
    users = load_users()
    return users.get(username, {}).get("role", "user")

# ─── Hashing ──────────────────────────────────────────────────────────────────
def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations=260_000
    ).hex()

def make_user(password: str, role: str = "user") -> dict:
    salt = secrets.token_hex(32)
    return {"salt": salt, "hash": _hash(password, salt), "role": role}

def verify(password: str, record: dict) -> bool:
    try:
        return secrets.compare_digest(
            _hash(password, record["salt"]),
            record["hash"]
        )
    except Exception:
        return False

# ─── Input helpers ────────────────────────────────────────────────────────────
def _read_password(stdscr, row, col, max_len=64):
    curses.flushinp()
    curses.nocbreak()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(1)
    buf = []
    while True:
        key = stdscr.getch()
        if key in (10, 13):
            break
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
                try:
                    stdscr.addstr(row, col + len(buf), " ",
                                  curses.color_pair(COLOR_NORMAL))
                    stdscr.move(row, col + len(buf))
                except curses.error:
                    pass
        elif key == 27:
            curses.curs_set(0)
            _halfdelay()
            return None
        elif 32 <= key <= 126 and len(buf) < max_len:
            buf.append(chr(key))
            try:
                stdscr.addstr(row, col + len(buf) - 1, "*",
                              curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass
        stdscr.noutrefresh()
        curses.doupdate()
    curses.curs_set(0)
    _halfdelay()
    return "".join(buf)

def _prompt_field(stdscr, title, label, row):
    _draw_login(stdscr, title)
    col = 6 + len(label) + 1
    try:
        stdscr.addstr(row, 6, label,
                      curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
    except curses.error:
        pass
    curses.flushinp()
    curses.nocbreak()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(1)
    stdscr.noutrefresh()
    curses.doupdate()
    buf = []
    while True:
        key = stdscr.getch()
        if key in (10, 13):
            break
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if buf:
                buf.pop()
                try:
                    stdscr.addstr(row, col + len(buf), " ",
                                  curses.color_pair(COLOR_NORMAL))
                    stdscr.move(row, col + len(buf))
                except curses.error:
                    pass
        elif key == 27:
            curses.curs_set(0)
            _halfdelay()
            return None
        elif 32 <= key <= 126 and len(buf) < 32:
            buf.append(chr(key))
            try:
                stdscr.addstr(row, col + len(buf) - 1, chr(key),
                              curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass
        stdscr.noutrefresh()
        curses.doupdate()
    curses.curs_set(0)
    _halfdelay()
    val = "".join(buf).strip()
    return val if val else None

# ─── UI helpers ───────────────────────────────────────────────────────────────
def _draw_login(stdscr, title, username=None):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    draw_header(stdscr)
    draw_separator(stdscr, 4, w)
    draw_menu_title(stdscr, title, 5)
    draw_separator(stdscr, 6, w)
    if username:
        try:
            stdscr.addstr(8, 6, f"User: {username}",
                          curses.color_pair(COLOR_DIM))
        except curses.error:
            pass
    draw_status(stdscr)

def _terminal_locked(stdscr, delay=3):
    import time
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = ["TERMINAL LOCKED", "", "PLEASE CONTACT AN ADMINISTRATOR"]
    start = (h - len(lines)) // 2
    for i, line in enumerate(lines):
        x = max(0, (w - len(line)) // 2)
        try:
            stdscr.addstr(start + i, x, line,
                          curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.noutrefresh()
    curses.doupdate()
    time.sleep(delay)

def _show_error(stdscr, msg, delay=1.5):
    import time
    h, w = stdscr.getmaxyx()
    try:
        stdscr.addstr(h - 3, 6, msg,
                      curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()
    time.sleep(delay)

def _show_success(stdscr, msg, delay=0.8):
    import time
    h, w = stdscr.getmaxyx()
    _draw_login(stdscr, "")
    try:
        stdscr.addstr(7, 6, msg,
                      curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()
    time.sleep(delay)

def _first_time_setup(stdscr):
    import time
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    draw_header(stdscr)
    draw_separator(stdscr, 4, w)
    draw_menu_title(stdscr, "FIRST TIME SETUP", 5)
    draw_separator(stdscr, 6, w)
    try:
        stdscr.addstr(8, 6, "No users found. Create an admin account.",
                      curses.color_pair(COLOR_DIM))
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()
    time.sleep(1.5)

    username = _prompt_field(stdscr, "FIRST TIME SETUP", "Admin username:", row=10)
    if not username:
        return

    _draw_login(stdscr, "FIRST TIME SETUP")
    try:
        stdscr.addstr(10, 6, "Password: ",
                      curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()
    password = _read_password(stdscr, 10, 16)
    if not password:
        return

    _draw_login(stdscr, "FIRST TIME SETUP")
    try:
        stdscr.addstr(10, 6, "Confirm password: ",
                      curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()
    confirm = _read_password(stdscr, 10, 24)
    if confirm != password:
        _show_error(stdscr, "Passwords do not match.")
        return

    # First user is always admin
    users = {username: make_user(password, role="admin")}
    save_users(users)
    _show_success(stdscr, f"Admin account '{username}' created.")

# ─── Login screen ─────────────────────────────────────────────────────────────
def login_screen(stdscr):
    import time
    is_first_window = "--first" in sys.argv
    # Non-first windows always do a short poll before showing their own login screen.
    # Covers both startup and post-logout scenarios.
    if "TMUX" in os.environ and not is_first_window:
        for _ in range(20):          # 10s max then show own login
            existing = read_session()
            if existing:
                return existing
            time.sleep(0.5)

    users = load_users()
    if not users:
        _first_time_setup(stdscr)
        users = load_users()
        if not users:
            return None

    MAX_ATTEMPTS = 3

    while True:
        attempts = 0
        username = run_menu(stdscr, "LOGIN", list(users.keys()) + ["---", "Exit"])
        if username == "__SESSION_READY__":
            existing = read_session()
            if existing:
                return existing
            continue
        if username in (None, "Back"):
            continue
        if username == "Exit":
            return "__EXIT__"

        users = load_users()
        if username not in users:
            continue

        while attempts < MAX_ATTEMPTS:
            _draw_login(stdscr, "LOGIN", username=username)
            role_label = f"[{get_role(username)}]"
            try:
                stdscr.addstr(10, 6, "Password: ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
                # Role tag inline after "User: {username}" on the header row
                user_str = f"User: {username}  {role_label}"
                stdscr.addstr(8, 6, user_str, curses.color_pair(COLOR_DIM))
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()

            password = _read_password(stdscr, 10, 16)
            if password is None:
                break

            if verify(password, users[username]):
                write_session(username)
                _show_success(stdscr, f"Welcome, {username}.")
                return username

            attempts += 1
            remaining = MAX_ATTEMPTS - attempts
            if remaining > 0:
                _show_error(stdscr, f"Wrong password. {remaining} attempt(s) left.")
            else:
                _terminal_locked(stdscr)

# ─── User management menu ─────────────────────────────────────────────────────
def user_management_menu(stdscr, current_user):
    while True:
        result = run_menu(stdscr, "User Management",
                          ["Add User", "Change Password", "Change Role",
                           "Delete User", "---", "Back"])
        if result == "Back":
            return

        elif result == "Add User":
            username = _prompt_field(stdscr, "ADD USER", "New username:", row=7)
            if not username:
                continue
            users = load_users()
            if username in users:
                curses_message(stdscr, f"User '{username}' already exists.")
                continue
            # Pick role
            role_choice = run_menu(stdscr, "Select Role", ["user", "admin"])
            if role_choice in (None, "Back"):
                continue
            _draw_login(stdscr, "ADD USER")
            try:
                stdscr.addstr(7, 6, "Password: ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            password = _read_password(stdscr, 7, 16)
            if not password:
                continue
            _draw_login(stdscr, "ADD USER")
            try:
                stdscr.addstr(7, 6, "Confirm:  ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            confirm = _read_password(stdscr, 7, 16)
            if confirm != password:
                curses_message(stdscr, "Passwords do not match.")
                continue
            users[username] = make_user(password, role=role_choice)
            save_users(users)
            curses_message(stdscr, f"User '{username}' ({role_choice}) added.")

        elif result == "Change Password":
            users = load_users()
            target = run_menu(stdscr, "Change Password",
                              list(users.keys()) + ["---", "Back"])
            if target in ("Back", None):
                continue
            _draw_login(stdscr, "CHANGE PASSWORD", username=target)
            try:
                stdscr.addstr(10, 6, "Current password: ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            old_pw = _read_password(stdscr, 10, 24)
            if not old_pw or not verify(old_pw, users[target]):
                curses_message(stdscr, "Incorrect current password.")
                continue
            _draw_login(stdscr, "CHANGE PASSWORD", username=target)
            try:
                stdscr.addstr(10, 6, "New password:     ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            new_pw = _read_password(stdscr, 10, 24)
            if not new_pw:
                continue
            _draw_login(stdscr, "CHANGE PASSWORD", username=target)
            try:
                stdscr.addstr(10, 6, "Confirm:          ",
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            confirm = _read_password(stdscr, 10, 24)
            if confirm != new_pw:
                curses_message(stdscr, "Passwords do not match.")
                continue
            users[target]["hash"] = _hash(new_pw, users[target]["salt"])
            save_users(users)
            curses_message(stdscr, f"Password changed for '{target}'.")

        elif result == "Change Role":
            users = load_users()
            # Can't demote yourself
            others = [u for u in users if u != current_user]
            if not others:
                curses_message(stdscr, "No other users to change role for.")
                continue
            target = run_menu(stdscr, "Change Role", others + ["---", "Back"])
            if target in ("Back", None):
                continue
            current_role = get_role(target)
            new_role = "user" if current_role == "admin" else "admin"
            if curses_confirm(stdscr, f"Change '{target}' from {current_role} to {new_role}?"):
                users[target]["role"] = new_role
                save_users(users)
                curses_message(stdscr, f"'{target}' is now {new_role}.")

        elif result == "Delete User":
            users = load_users()
            if len(users) <= 1:
                curses_message(stdscr, "Cannot delete the last user.")
                continue
            deletable = [u for u in users if u != current_user]
            target = run_menu(stdscr, "Delete User", deletable + ["---", "Back"])
            if target in ("Back", None):
                continue
            if curses_confirm(stdscr, f"Delete user '{target}'?"):
                del users[target]
                save_users(users)
                # Remove user's personal data folder
                import shutil
                from config import USERS_DIR
                user_dir = USERS_DIR / target
                if user_dir.exists():
                    shutil.rmtree(user_dir)
                curses_message(stdscr, f"User '{target}' deleted.")