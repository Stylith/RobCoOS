import curses
import os
import time
import platform
import psutil
from config import (COLOR_NORMAL, COLOR_DIM, THEMES,
                    SOUND_ON, BOOTUP_ON, CURRENT_THEME,
                    set_sound, set_bootup, set_theme,
                    save_all_settings, init_colors,
                    load_about, save_about)
from status import draw_header, draw_separator, draw_status
from ui import run_menu, curses_input, curses_message

ALL_FIELDS = ["OS", "Hostname", "CPU", "RAM", "Uptime", "Battery", "Theme", "Shell", "Python"]

def get_system_info(fields):
    import config
    info = {}
    if "OS" in fields:
        info["OS"] = platform.system() + " " + platform.release()
    if "Hostname" in fields:
        info["Hostname"] = platform.node()
    if "CPU" in fields:
        info["CPU"] = platform.processor() or "Unknown"
    if "Uptime" in fields:
        uptime_seconds = time.time() - psutil.boot_time()
        h = int(uptime_seconds // 3600)
        m = int((uptime_seconds % 3600) // 60)
        info["Uptime"] = f"{h}h {m}m"
    if "RAM" in fields:
        ram = psutil.virtual_memory()
        used = ram.used // (1024 ** 2)
        total = ram.total // (1024 ** 2)
        info["RAM"] = f"{used}MB / {total}MB"
    if "Battery" in fields:
        battery = psutil.sensors_battery()
        if battery:
            info["Battery"] = f"{int(battery.percent)}%"
    if "Theme" in fields:
        info["Theme"] = config.CURRENT_THEME
    if "Shell" in fields:
        info["Shell"] = os.environ.get("SHELL", "Unknown")
    if "Python" in fields:
        info["Python"] = platform.python_version()
    return info

def about_edit_menu(stdscr, config_data):
    while True:
        result = run_menu(stdscr, "Edit About",
                          ["Edit ASCII Art", "Toggle Fields", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Edit ASCII Art":
            line = curses_input(stdscr, "Enter ASCII art line (blank to finish):")
            if line:
                art = config_data.get("ascii", [])
                art.append(line)
                config_data["ascii"] = art
                save_about(config_data)
                curses_message(stdscr, "Line added. Re-enter to add more.")
        elif result == "Toggle Fields":
            fields = config_data.get("fields", ALL_FIELDS[:])
            while True:
                choices = ([f"{'[x]' if f in fields else '[ ]'} {f}" for f in ALL_FIELDS]
                           + ["---", "Back"])
                toggle = run_menu(stdscr, "Toggle Fields", choices,
                                  subtitle="Select to toggle on/off")
                if toggle in ("Back"):
                    break
                field = toggle.split(" ", 1)[1]
                if field in fields:
                    fields.remove(field)
                else:
                    fields.append(field)
                config_data["fields"] = fields
                save_about(config_data)

def about_screen(stdscr):
    config_data = load_about()
    ascii_art = config_data.get("ascii", [
        "██████╗  ██████╗ ██████╗  ██████╗ ██████╗ ",
        "██╔══██╗██╔═══██╗██╔══██╗██╔════╝██╔═══██╗",
        "██████╔╝██║   ██║██████╔╝██║     ██║   ██║",
        "██╔══██╗██║   ██║██╔══██╗██║     ██║   ██║",
        "██║  ██║╚██████╔╝██████╔╝╚██████╗╚██████╔╝",
        "╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝ ",
    ])
    fields = config_data.get("fields", ["OS", "Hostname", "CPU", "RAM",
                                         "Uptime", "Battery", "Theme", "Shell"])
    info = get_system_info(fields)
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr)
        draw_separator(stdscr, 4, w)
        art_start = 5
        for i, line in enumerate(ascii_art):
            x = max(0, (w - len(line)) // 2)
            try:
                stdscr.addstr(art_start + i, x, line,
                              curses.color_pair(COLOR_NORMAL) | curses.A_BOLD)
            except curses.error:
                pass
        info_start = art_start + len(ascii_art) + 1
        for i, (key, val) in enumerate(info.items()):
            line = f"{key}: {val}"
            x = max(0, (w - len(line)) // 2)
            try:
                stdscr.addstr(info_start + i, x, line, curses.color_pair(COLOR_NORMAL))
            except curses.error:
                pass
        try:
            stdscr.addstr(h - 2, 2, "e=edit  q/tab=back", curses.color_pair(COLOR_DIM))
        except curses.error:
            pass
        draw_status(stdscr)
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27, 9):
            break
        elif key == ord('e'):
            about_edit_menu(stdscr, config_data)
            config_data = load_about()
            info = get_system_info(config_data.get("fields", fields))

def theme_menu(stdscr):
    result = run_menu(stdscr, "Select Theme", list(THEMES.keys()) + ["---", "Back"])
    if result != "Back" and result in THEMES:
        set_theme(result)
        save_all_settings()
        init_colors()

def settings_menu(stdscr):
    from apps import edit_menus_menu
    while True:
        import config
        sound_label  = "Sound: ON  [toggle]" if config.SOUND_ON  else "Sound: OFF [toggle]"
        bootup_label = "Bootup: ON [toggle]" if config.BOOTUP_ON else "Bootup: OFF [toggle]"
        result = run_menu(stdscr, "Settings Menu",
                          ["About", "Theme", "Edit Menus",
                           bootup_label, sound_label, "---", "Back"])
        if result == "Back":
            break
        elif result == "About":
            about_screen(stdscr)
        elif result == "Theme":
            r = theme_menu(stdscr)
        elif result == "Edit Menus":
            r = edit_menus_menu(stdscr)
        elif result == sound_label:
            set_sound(not config.SOUND_ON)
            save_all_settings()
        elif result == bootup_label:
            set_bootup(not config.BOOTUP_ON)
            save_all_settings()