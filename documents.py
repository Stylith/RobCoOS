import curses
from datetime import date
from pathlib import Path
from config import (COLOR_NORMAL, COLOR_DIM, ALLOWED_EXTENSIONS,
                    load_categories, init_colors)
from status import draw_header, draw_separator, draw_menu_title, draw_status
from ui import run_menu, curses_input, curses_confirm, curses_message, curses_pager, _halfdelay
from launcher import launch_epy

# ─── Document scanning ────────────────────────────────────────────────────────
def scan_documents(folder: Path):
    return [f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS]

def sort_key(f):
    name = f.stem.replace("_", " ").lower()
    if name.startswith("the "):
        name = name[4:]
    return name

# ─── Journal editor ───────────────────────────────────────────────────────────
def journal_new(stdscr):
    current_date = date.today()
    journal_dir  = Path("journal_entries")
    journal_dir.mkdir(exist_ok=True)
    lines      = [""]
    cursor_row = 0
    cursor_col = 0
    curses.curs_set(1)
    curses.cbreak()   # blocking getch for responsive typing (no halfdelay)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr)
        draw_separator(stdscr, 4, w)
        draw_menu_title(stdscr, f"New Entry - {current_date}", 5)
        draw_separator(stdscr, 6, w)
        for i, line in enumerate(lines):
            try:
                stdscr.addstr(8 + i, 2, line[:w - 4], curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass
        try:
            stdscr.addstr(h - 2, 2, "CTRL+W = save  |  CTRL+X = cancel",
                          curses.color_pair(COLOR_DIM))
        except curses.error:
            pass
        draw_status(stdscr)
        try:
            stdscr.move(8 + cursor_row, 2 + cursor_col)
        except curses.error:
            pass
        stdscr.noutrefresh()
        curses.doupdate()

        key = stdscr.getch()

        if key == curses.KEY_RESIZE:
            init_colors()
            stdscr.clear()
            continue
        elif key == 23:  # Ctrl+W save
            text = "\n".join(lines).strip()
            if text:
                file_name = journal_dir / f"{current_date}.txt"
                with open(file_name, "a") as f:
                    f.write(text + "\n")
                curses.curs_set(0)
                _halfdelay()
                curses_message(stdscr, "Entry saved.")
            else:
                curses.curs_set(0)
                _halfdelay()
            return
        elif key == 24:  # Ctrl+X cancel
            curses.curs_set(0)
            _halfdelay()
            return
        elif key in (curses.KEY_ENTER, 10, 13):
            current = lines[cursor_row]
            lines[cursor_row] = current[:cursor_col]
            lines.insert(cursor_row + 1, current[cursor_col:])
            cursor_row += 1
            cursor_col = 0
        elif key in (curses.KEY_BACKSPACE, 127):
            if cursor_col > 0:
                lines[cursor_row] = (lines[cursor_row][:cursor_col - 1]
                                     + lines[cursor_row][cursor_col:])
                cursor_col -= 1
            elif cursor_row > 0:
                prev_len = len(lines[cursor_row - 1])
                lines[cursor_row - 1] += lines[cursor_row]
                lines.pop(cursor_row)
                cursor_row -= 1
                cursor_col = prev_len
        elif key == curses.KEY_UP and cursor_row > 0:
            cursor_row -= 1
            cursor_col = min(cursor_col, len(lines[cursor_row]))
        elif key == curses.KEY_DOWN and cursor_row < len(lines) - 1:
            cursor_row += 1
            cursor_col = min(cursor_col, len(lines[cursor_row]))
        elif key == curses.KEY_LEFT and cursor_col > 0:
            cursor_col -= 1
        elif key == curses.KEY_RIGHT and cursor_col < len(lines[cursor_row]):
            cursor_col += 1
        elif 32 <= key <= 126:
            lines[cursor_row] = (lines[cursor_row][:cursor_col]
                                 + chr(key)
                                 + lines[cursor_row][cursor_col:])
            cursor_col += 1

# ─── Journal view / delete ────────────────────────────────────────────────────
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
    options  = sorted(file_map.keys(), reverse=True) + ["Back"]
    while True:
        result = run_menu(stdscr, "View Logs", options)
        if result == "Back":
            return
        if result in file_map:
            curses_pager(stdscr, file_map[result].read_text(), title=result)

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
    options  = sorted(file_map.keys(), reverse=True) + ["Back"]
    result   = run_menu(stdscr, "Delete Log", options)
    if result == "Back" or result not in file_map:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        file_map[result].unlink()
        curses_message(stdscr, f"Deleted {result}.")

# ─── Logs menu ────────────────────────────────────────────────────────────────
def logs_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Logs Menu",
                          ["Create New Log", "View Logs", "Delete Logs", "---", "Back"])
        if result == "Back":
            return
        elif result == "Create New Log":
            journal_new(stdscr)
        elif result == "View Logs":
            journal_view(stdscr)
        elif result == "Delete Logs":
            journal_delete(stdscr)

# ─── Documents menu ───────────────────────────────────────────────────────────
def documents_menu(stdscr):
    while True:
        categories = load_categories()
        choices    = ["Logs"] + list(categories.keys()) + ["---", "Back"]
        result     = run_menu(stdscr, "Documents Menu", choices,
                              subtitle="Select Document Type")
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
                files.sort(key=sort_key)
                file_map    = {f.stem.replace("_", " "): f for f in files}
                file_result = run_menu(stdscr, result,
                                       list(file_map.keys()) + ["Back"],
                                       subtitle=f"Select {result}")
                if file_result == "Back":
                    break
                elif file_result in file_map:
                    launch_epy(stdscr, file_map[file_result])
