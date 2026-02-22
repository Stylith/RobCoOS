import os
import sys
import curses
import subprocess

# ─── Base dir ─────────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
sys.path.insert(0, base_dir)

from checks import has_tmux, in_tmux, run_preflight

# ─── Dependency preflight ─────────────────────────────────────────────────────
def preflight_gate():
    ok, warnings, errors = run_preflight()
    if not ok:
        print("\n╔══════════════════════════════════════════════════╗")
        print("║         RobcOS - Dependency Error                ║")
        print("╚══════════════════════════════════════════════════╝")
        for e in errors:
            print(f"  ✗ {e}")
        if warnings:
            print()
            for w in warnings:
                print(f"  ! {w}")
        print("\nPlease install the missing required dependencies and try again.")
        sys.exit(1)
    if warnings:
        print("\n╔══════════════════════════════════════════════════╗")
        print("║     RobcOS - Optional Dependencies Missing       ║")
        print("╚══════════════════════════════════════════════════╝")
        for w in warnings:
            print(f"  ! {w}")
        print("\nSome features will be unavailable. Press Enter to continue...")
        input()

# ─── Tmux helpers ─────────────────────────────────────────────────────────────
# SESSION_NAME and NUM_WINDOWS live in config.py

def tmux_session_exists():
    from config import SESSION_NAME
    r = subprocess.run(["tmux", "has-session", "-t", SESSION_NAME], capture_output=True)
    return r.returncode == 0

def kill_all_sessions():
    from config import SESSION_NAME
    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME], capture_output=True)

def launch_in_tmux():
    from config import SESSION_NAME, NUM_WINDOWS
    script = os.path.abspath(__file__)

    if not has_tmux():
        print("Warning: tmux not found. Running without desktop switching.")
        print("Install tmux for multi-window support:")
        print("  brew install tmux  /  apt install tmux  /  pacman -S tmux")
        print("\nPress Enter to continue in single-window mode...")
        input()
        return False

    if in_tmux():
        return False  # already inside tmux, run normally

    if tmux_session_exists():
        os.execvp("tmux", ["tmux", "attach-session", "-t", SESSION_NAME])
        return True

    # ── Create session ──────────────────────────────────────────────────────
    # First window gets --first flag so only it plays the bootup animation.
    # Windows start at index 0 by default; we renumber to 1 after creation
    # so Ctrl+B 1-4 works as expected.
    subprocess.run([
        "tmux", "new-session", "-d",
        "-s", SESSION_NAME,
        "-n", "Desktop 1",
        sys.executable, script, "--no-tmux", "--first"   # ← bootup flag
    ])

    # Hide tmux status bar so it doesn't bleed into the RobcOS UI
    subprocess.run(["tmux", "set-option", "-t", SESSION_NAME, "status", "off"])

    # Spawn remaining windows (no --first, so no bootup)
    for i in range(2, NUM_WINDOWS + 1):
        subprocess.run([
            "tmux", "new-window",
            "-t", f"{SESSION_NAME}:",
            "-n", f"Desktop {i}",
            sys.executable, script, "--no-tmux"          # ← no bootup flag
        ])

    # Renumber all windows starting from 1 so Ctrl+B 1, 2, 3, 4 all work
    subprocess.run(["tmux", "set-option", "-t", SESSION_NAME, "base-index", "1"])
    subprocess.run(["tmux", "move-window", "-r", "-t", SESSION_NAME])

    # Land on Desktop 1
    subprocess.run(["tmux", "select-window", "-t", f"{SESSION_NAME}:1"])
    os.execvp("tmux", ["tmux", "attach-session", "-t", SESSION_NAME])
    return True

# ─── Main curses loop ─────────────────────────────────────────────────────────
def main(stdscr, show_bootup=True):
    # All local imports deferred so preflight runs first
    import config
    from config import init_colors, playsound, SESSION_NAME, NUM_WINDOWS
    from status import draw_status
    from ui import run_menu, curses_message, _halfdelay
    from apps import apps_menu, games_menu, network_menu
    from documents import documents_menu
    from installer import appstore_menu
    from terminal import embedded_terminal
    from settings import settings_menu
    from boot import bootup_curses

    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    if config.BOOTUP_ON and show_bootup:
        bootup_curses(stdscr)

    # halfdelay drives status bar refreshes — no thread needed
    _halfdelay()

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

    # Logout from any desktop kills the whole session — all desktops close
    if in_tmux() and has_tmux():
        kill_all_sessions()

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    no_tmux  = "--no-tmux" in sys.argv
    is_first = "--first"   in sys.argv

    if not no_tmux:
        # Preflight runs before any local imports — missing deps shown cleanly
        preflight_gate()
        launched = launch_in_tmux()
        if launched:
            sys.exit(0)

    # show_bootup is True only when --first is passed, or not in tmux at all
    show_bootup = is_first or not in_tmux()

    stdscr = curses.initscr()
    try:
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        main(stdscr, show_bootup=show_bootup)
    finally:
        stdscr.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        os.system('clear')
        sys.exit(0)
