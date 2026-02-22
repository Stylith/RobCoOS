import os
import curses
import pty
import select
import pyte
from config import COLOR_SELECTED, COLOR_STATUS, INPUT_TIMEOUT
from status import draw_status
from ui import _halfdelay

def embedded_terminal(stdscr):
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
        stdscr.nodelay(True)   # non-blocking for the terminal render loop
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
            try:
                stdscr.addstr(0, 0, " ROBCO MAINTENANCE TERMLINK ".center(w - 1),
                              curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
            except curses.error:
                pass
            for row_idx, row in enumerate(screen.display):
                try:
                    stdscr.addstr(row_idx + 1, 0, row[:w - 1])
                except curses.error:
                    pass
            try:
                stdscr.addstr(h - 1, 0, " CTRL+X TO EXIT ".ljust(w - 1),
                              curses.color_pair(COLOR_STATUS) | curses.A_BOLD)
            except curses.error:
                pass
            try:
                stdscr.move(screen.cursor.y + 1, screen.cursor.x)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            key = stdscr.getch()
            if key == 24:  # Ctrl+X
                os.kill(pid, 9)
                break
            elif key == curses.KEY_RESIZE:
                pass  # screen.resize handles it next iteration
            elif key != -1:
                if key < 256:
                    os.write(fd, bytes([key]))
                else:
                    os.write(fd, curses.keyname(key))
        os.waitpid(pid, 0)
        stdscr.keypad(True)
        stdscr.nodelay(False)
        _halfdelay()  # restore halfdelay after terminal exits
