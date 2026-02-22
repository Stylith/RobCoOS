import os
import curses
import subprocess
import time
from config import init_colors, INPUT_TIMEOUT
from ui import _halfdelay

def _suspend(stdscr):
    time.sleep(1.1)
    curses.endwin()
    os.system('tput reset')

def _resume(stdscr):
    os.system('clear')
    curses.reset_prog_mode()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()
    stdscr.clearok(True)
    stdscr.clear()
    stdscr.noutrefresh()
    curses.doupdate()
    _halfdelay()  # restore halfdelay after returning from external app

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
