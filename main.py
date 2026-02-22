import os
import sys
import curses
import threading

import config
from config import init_colors, BOOTUP_ON
from status import (status_bar_thread, set_stdscr_ref, stop_status)
from ui import run_menu, curses_message
from config import playsound
from apps import apps_menu, games_menu, network_menu
from documents import documents_menu
from installer import appstore_menu
from terminal import embedded_terminal
from settings import settings_menu
from boot import bootup_curses

# ─── Base dir ─────────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)

# ─── Main ─────────────────────────────────────────────────────────────────────
def main(stdscr):
    set_stdscr_ref(stdscr)

    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    if config.BOOTUP_ON:
        bootup_curses(stdscr)

    t = threading.Thread(target=status_bar_thread, daemon=True)
    t.start()

    while True:
        result = run_menu(stdscr, "Main Menu",
                          ["Applications", "Documents", "Network", "Games",
                           "Program Installer", "Terminal",
                           "---", "Settings", "Logout"],
                          subtitle="RobcOS v.85")
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

    stop_status()
    set_stdscr_ref(None)
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
