import curses
import time
from config import (COLOR_NORMAL, COLOR_SELECTED, COLOR_TITLE,
                    COLOR_DIM, playsound)
from status import (draw_header, draw_status, draw_separator,
                    draw_menu_title, set_status_paused)

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
    set_status_paused(True)
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
    set_status_paused(False)
    return inp.strip()

def curses_confirm(stdscr, message):
    set_status_paused(True)
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
    set_status_paused(False)
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
        try:
            stdscr.addstr(h - 2, 2, "up/down scroll  q/tab/enter=back",
                          curses.color_pair(COLOR_DIM))
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
                    stdscr.addch(y + row, x + col, '=',
                                 curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                elif col == 0 or col == box_w - 1:
                    stdscr.addch(y + row, x + col, '|',
                                 curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                else:
                    stdscr.addch(y + row, x + col, ' ',
                                 curses.color_pair(COLOR_SELECTED))
            except curses.error:
                pass
    try:
        stdscr.addstr(y + 2, x + 3, message,
                      curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
    except curses.error:
        pass
    stdscr.refresh()
    time.sleep(delay)
