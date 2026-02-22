import curses
import time
import itertools
import random
from config import COLOR_NORMAL, INPUT_TIMEOUT, playsound
from ui import _halfdelay

def bootup_curses(stdscr):
    stdscr.nodelay(True)

    def skipped():
        return stdscr.getch() == ord(' ')

    sounds = [
        'Sounds/ui_hacking_charsingle_01.wav',
        'Sounds/ui_hacking_charsingle_02.wav',
        'Sounds/ui_hacking_charsingle_03.wav',
        'Sounds/ui_hacking_charsingle_04.wav',
        'Sounds/ui_hacking_charsingle_05.wav',
    ]
    random.shuffle(sounds)

    sequences = [
        ("WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK\nSET TERMINAL/INQUIRE", 0.02, 2, False),
        ("RIT-V300\n>SET FILE/PROTECTION-OWNER/RFWD ACCOUNTS.F\n>SET HALT RESTART/MAINT", 0.05, 2, False),
        ("ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL\nRETROS BIOS\nRBIOS-4.02.08.00 52EE5.E7.E8\n"
         "Copyright 2201-2203 Robco Ind.\nUppermem: 64KB\nRoot (5A8)\nMaintenance Mode", 0.02, 2, False),
        ("LOGON ADMIN", 0.1, 3, False),
        ("ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM\nCOPYRIGHT 2075-2077 ROBCO INDUSTRIES\n-SERVER 1-",
         0.05, 2, True),
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
                    stdscr.noutrefresh()
                    curses.doupdate()
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
                stdscr.noutrefresh()
                curses.doupdate()
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
    stdscr.erase()
    stdscr.noutrefresh()
    curses.doupdate()
    _halfdelay()  # restore halfdelay after boot animation
