import shlex
from config import (load_apps, save_apps, load_games, save_games,
                    load_networks, save_networks)
from ui import run_menu, curses_input, curses_confirm, curses_message
from launcher import launch_subprocess

# ─── Generic add/delete ───────────────────────────────────────────────────────
def add_entry(stdscr, data, save_fn, kind="App"):
    name = curses_input(stdscr, f"Enter {kind} display name:")
    if not name:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    command = curses_input(stdscr, f"Enter launch command for '{name}':")
    if not command:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    data[name] = shlex.split(command)
    save_fn(data)
    curses_message(stdscr, f"{name} added.")

def delete_entry(stdscr, data, save_fn, kind="App"):
    if not data:
        curses_message(stdscr, f"Error: {kind} list is empty.")
        return
    options = list(data.keys()) + ["Back"]
    result = run_menu(stdscr, f"Delete {kind}", options)
    if result == "Back" or result not in data:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        del data[result]
        save_fn(data)
        curses_message(stdscr, f"{result} deleted.")
    else:
        curses_message(stdscr, "Cancelled.", 0.8)

# ─── Apps menu ────────────────────────────────────────────────────────────────
def apps_menu(stdscr):
    while True:
        apps = load_apps()
        choices = list(apps.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Applications Menu", choices, subtitle="Select App")
        if result == "Back":
            break
        elif result in apps:
            launch_subprocess(stdscr, apps[result])

def games_menu(stdscr):
    while True:
        games = load_games()
        choices = list(games.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Games Menu", choices, subtitle="Select Game")
        if result == "Back":
            break
        elif result in games:
            launch_subprocess(stdscr, games[result])

def network_menu(stdscr):
    while True:
        networks = load_networks()
        choices = list(networks.keys()) + ["---", "Back"]
        result = run_menu(stdscr, "Network Menu", choices, subtitle="Select Network Program")
        if result == "Back":
            break
        elif result in networks:
            launch_subprocess(stdscr, networks[result])

# ─── Edit menus ───────────────────────────────────────────────────────────────
def edit_apps_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Applications",
                          ["Add App", "Delete App", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Add App":
            add_entry(stdscr, load_apps(), save_apps, "App")
        elif result == "Delete App":
            delete_entry(stdscr, load_apps(), save_apps, "App")

def edit_games_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Games",
                          ["Add Game", "Delete Game", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Add Game":
            add_entry(stdscr, load_games(), save_games, "Game")
        elif result == "Delete Game":
            delete_entry(stdscr, load_games(), save_games, "Game")

def edit_network_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Network",
                          ["Add Network", "Delete Network", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Add Network":
            add_entry(stdscr, load_networks(), save_networks, "Network Program")
        elif result == "Delete Network":
            delete_entry(stdscr, load_networks(), save_networks, "Network Program")

def edit_menus_menu(stdscr):
    from documents import edit_documents_menu
    while True:
        result = run_menu(stdscr, "Edit Menus",
                          ["Edit Applications", "Edit Documents",
                           "Edit Network", "Edit Games", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Edit Applications":
            r = edit_apps_menu(stdscr)
        elif result == "Edit Documents":
            r = edit_documents_menu(stdscr)
        elif result == "Edit Network":
            r = edit_network_menu(stdscr)
        elif result == "Edit Games":
            r = edit_games_menu(stdscr)
