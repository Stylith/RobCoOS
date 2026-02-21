import os 
import sys
import time
import subprocess
import json
import shlex
from pathlib import Path 
from datetime import date
from bullet import Bullet, Check, YesNo, Input
from playsound import playsound

os.system('clear')

base_dir = Path(__file__).resolve().parent
if not base_dir.is_dir():
    print("Error," + {base_dir} + "does not exist")
else:
    os.chdir(base_dir)

#center all text
def Middle(text):
    return text.center(os.get_terminal_size().columns)

class Format:
    end = '\033[0m'
    underline = '\033[4m'

# Journal menu
def journal_new():
        clear()
        current_date = date.today()
        x = Path("journal_entries")
        if not os.path.exists(x):
            os.makedirs("journal_entries")
        else:
            cli = Input(
                prompt = Format.underline + str(current_date) + Format.end + "\n",
            )
            result = cli.launch()
            file_name = "journal_entries/" + str(current_date) +".txt"
            with open(file_name, "a") as f:
                f.write(result)
    
def journal_view():
    clear()
    directory_path = Path("journal_entries")
    logs = [f for f in directory_path.iterdir() if f.is_file()]
    if not logs:
        print("Error, log folder empty")
        time.sleep(2)
        logsmenu()
    else:
        file_map = {f.stem: f for f in logs}
    options = list(file_map.keys()) + ["Back"]
    while True:
        cli = Bullet(
            prompt = "\nSelect Log",
            choices = options,
            bullet = "> "
        )
        result = cli.launch()
        if result == "Back":
            break
        newpath = file_map[result]
        clear()
        subprocess.run(['vim', str(newpath)])

def journal_delete():
    clear()
    directory_path = Path("journal_entries")
    logs = [f for f in directory_path.iterdir() if f.is_file()]
    if not logs:
        print("Error, log folder empty")
        time.sleep(2)
        logsmenu()
    else:
        file_map = {f.stem: f for f in logs}
    options = list(file_map.keys()) + ["Back"]
    cli = Bullet(
        prompt = "\nSelect Log",
        choices = options,
        bullet = "> "
    )
    result = cli.launch()
    if result == "Back":
        logsmenu()
    newpath = file_map[result]
    clear()
    subprocess.run(['rm', str(newpath)])

#Apps menu script
APPS_FILE = Path("apps.json")
def load_apps():
    if APPS_FILE.exists():
        return json.loads(APPS_FILE.read_text())
    return {}

def save_apps(apps):
    APPS_FILE.write_text(json.dumps(apps, indent=4))

def add_app(apps):
    name = input("Enter app display name: ").strip()
    command = input("Enter launch command: ").strip()

    if not name or not command:
        print("Error: Invalid Input")
        time.sleep(1)
        return

    apps[name] = shlex.split(command)
    save_apps(apps)
    print(f"{name} added.")

def delete_app(apps):
    if not apps:
        print("Error: App List Empty")
        time.sleep(2)
        return

    cli = Bullet(
        prompt = "\nSelect App to Delete",
        choices = list(apps.keys())
    )

    result = cli.launch()
    confirm = input(f"Delete '{result}'? (y/n): ").lower()
    if confirm == "y":
        del apps[result]
        save_apps(apps)
        print(f"{result} deleted.")
        time.sleep(1)
    else:
        print("Cancelled.")
        time.sleep(1)

#Games menu script
GAMES_FILE = Path("games.json")
def load_games():
    if GAMES_FILE.exists():
        return json.loads(GAMES_FILE.read_text())
    return {}

def save_games(games):
    GAMES_FILE.write_text(json.dumps(games, indent=4))

def add_game(games):
    name = input("Enter game display name: ").strip()
    command = input("Enter launch command: ").strip()

    if not name or not command:
        print("Error: Invalid Input")
        time.sleep(1)
        return

    games[name] = shlex.split(command)
    save_games(games)
    print(f"{name} added.")

def delete_game(games):
    if not games:
        print("Error: Games List Empty")
        time.sleep(2)
        return

    cli = Bullet(
        prompt = "\nSelect Game to Delete",
        choices = list(games.keys())
    )

    result = cli.launch()
    confirm = input(f"Delete '{result}'? (y/n): ").lower()
    if confirm == "y":
        del games[result]
        save_games(games)
        print(f"{result} deleted.")
        time.sleep(1)
    else:
        print("Cancelled.")
        time.sleep(1)

#Documents menu script
DOCS_FILE = Path("documents.json")
ALLOWED_EXTENSIONS = {".pdf", ".epub", ".txt", ".mobi", ".azw3"}
def load_categories():
    if DOCS_FILE.exists():
        return json.loads(DOCS_FILE.read_text())
    return {}

def save_categories(categories):
    DOCS_FILE.write_text(json.dumps(categories, indent=4))

def add_category(categories):
    name = input("Enter category name: ").strip()
    path_input = input("Enter folder path: ").strip()
    path = Path(path_input).expanduser()
    if not path.exists() or not path.is_dir():
        print("Error: Invalid Directory")
        input("Press Enter to Continue")
        return
    categories [name] = str(path)
    save_categories(categories)
    print("Category Added")
    time.sleep(1)

def delete_category(categories):
    if not categories:
        print("Error: No Categories to Delete")
        input("Press Enter to Continue")
        return
    cli = Bullet(
        prompt = "\nSelect Category to Delete",
        choices = list(categories.keys())
    )
    result = cli.launch()
    confirm = input(f"Delete '{result}'? (y/n): ").lower()
    if confirm == "y":
        del categories[result]
        save_categories(categories)
        print ("Deleted.")
    input("Press Enter to Continue")

def scan_documents(folder: Path):
    return [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]

def open_file(file_path: Path):
    subprocess.run(["epy", str(file_path)])

#Network menu script
NETWORKS_FILE = Path("networks.json")
def load_networks():
    if NETWORKS_FILE.exists():
        return json.loads(NETWORKS_FILE.read_text())
    return {}

def save_networks(networks):
    NETWORKS_FILE.write_text(json.dumps(networks, indent=4))

def add_network(networks):
    name = input("Enter Network Program display name: ").strip()
    command = input("Enter launch command: ").strip()

    if not name or not command:
        print("Error: Invalid Input")
        time.sleep(1)
        return

    networks[name] = shlex.split(command)
    save_networks(networks)
    print(f"{name} added.")

def delete_network(networks):
    if not networks:
        print("Error: Network Program List Empty")
        time.sleep(2)
        return

    cli = Bullet(
        prompt = "\nSelect Network Program to Delete",
        choices = list(networks.keys())
    )

    result = cli.launch()
    confirm = input(f"Delete '{result}'? (y/n): ").lower()
    if confirm == "y":
        del networks[result]
        save_networks(networks)
        print(f"{result} deleted.")
        time.sleep(1)
    else:
        print("Cancelled.")

#Robco text on top
startup1 = "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM"
startup2 = "COPYRIGHT 2075-2077 ROBCO INDUSTRIES"
startup3 = "-SERVER 1-"

def maintitle():
    for i in Middle(startup1):
        print(i, end="", flush=True)
        time.sleep(0.01)
    for i in Middle(startup2):
        print(i, end="", flush=True)
        time.sleep(0.01)
    for i in Middle(startup3):
        print(i, end="", flush=True)
        time.sleep(0.01)
    print("")
    playsound('Sounds/ui_hacking_passgood.wav')
    time.sleep(1)

def title():
    print(Middle(startup1))
    print(Middle(startup2))
    print(Middle(startup3))
    
#Bootup Animation
def bootup():
    intro = "WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK\nSET TERMINAL/INQUIRE"
    intro3 = "RIT-V300\n>SET FILE/PROTECTION-OWNER/RFWD ACCOUNTS.F\n>SET HALT RESTART/MAINT"
    intro4 = "ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL\nRETROS BIOS\nRBIOS-4.02.08.00 52EE5.E7.E8\nCopyright 2201-2203 Robco Ind.\nUppermem: 64KB\nRoot (5A8)\nMaintenance Mode"
    for i in intro:
        playsound('Sounds/ui_hacking_charscroll.wav', False)
        print(i, end="", flush=True)
        time.sleep(0.02)
    time.sleep(2)
    clear()
    for i in intro3:
        playsound('Sounds/ui_hacking_charscroll.wav', False)
        print(i, end="", flush=True)
        time.sleep(0.05)
    time.sleep(2)
    clear()
    for i in intro4:
        playsound('Sounds/ui_hacking_charscroll.wav', False)
        print(i, end="", flush=True)
        time.sleep(0.02)
    time.sleep(2)
    clear()
    for i in "LOGON ADMIN":
        playsound('Sounds/ui_hacking_charenter_01.wav')
        print(i, end="", flush=True)
        time.sleep(0.1)
    time.sleep(3)
    clear()
    maintitle() 
    
#Main menu
def clear():
    os.system('clear')

def mainmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Main Menu"))
        print(Middle("=================================================="))
        print("")
        cli = Bullet(
            prompt = Format.underline + "Select Program" + Format.end + "\n",
            choices = ["Applications", "Documents", "Network", "Games", "---", "Settings", "Logout"], 
            bullet = "> "
        )
        result = cli.launch()
        if result == "Logout":
            print("Logging out...")
            playsound('Sounds/ui_hacking_passbad.wav', False)
            time.sleep(1)
            os.system('clear')
            break
        elif result in ("---", ""):
            continue
        elif result == "Applications":
            appsmenu()
        elif result == "Documents":
            documentsmenu()
        elif result == "Games":
            gamesmenu()
        elif result == "Network":
            networkmenu()
        elif result == "Settings":
            settingsmenu()


def appsmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Applications Menu"))
        print(Middle("=================================================="))
        print("")
        apps = load_apps()
        choices = list(apps.keys()) + ["---", "Back"]
        cli = Bullet(
            prompt = Format.underline + "Select Application" + Format.end + "\n",
            choices = choices,
            bullet = "> "
        )
        result = cli.launch()
        if result in ("---", ""):
            continue
        elif result == "Back":
            break
        else:
            playsound('Sounds/ui_hacking_charenter_01.wav')
            clear()
            subprocess.run(apps[result])
            
   
def documentsmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Documents Menu"))
        print(Middle("=================================================="))
        print("")
        categories = load_categories()
        choices = ["Logs"] + list(categories.keys()) + ["---", "Back"]
        cli = Bullet(
            prompt = Format.underline + "Select Doc Type" + Format.end + "\n",
            choices = choices, 
            bullet = "> "
        )
        result = cli.launch()
        if result == "---":
            continue
        elif result == "Logs":
            logsmenu()
        elif result == "Back":
            break
        else:
            while True:
                playsound('Sounds/ui_hacking_charenter_01.wav')
                clear()
                title()
                print("")
                print(Middle("Games Menu"))
                print(Middle("=================================================="))
                print("")
                folder = Path(categories[result]).expanduser()
                files = scan_documents(folder)
                if not files:
                    print("No Supported Documents Found")
                    input("Press Enter to Continue")
                    break
                files.sort(key=lambda f: f.stem.lower())
                file_map = {}
                for f in files:
                    display = f.stem.replace("_", " ")
                    file_map[display] = f
                file_cli = Bullet(
                    prompt = Format.underline + f"\n{result}" + Format.end + "\n",
                    choices = list(file_map.keys()) + ["---", "Back"],
                    bullet = "> "
                )
                file_result = file_cli.launch()
                if file_result == "Back":
                    break
                if file_result in ("---", ""):
                    continue
                else:
                    playsound('Sounds/ui_hacking_charenter_01.wav')
                    open_file(file_map[file_result])

def gamesmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Games Menu"))
        print(Middle("=================================================="))
        print("")
        games = load_games()
        choices = list(games.keys()) + ["---", "Back"]
        cli = Bullet(
            prompt = Format.underline + "Select Game" + Format.end + "\n",
            choices = choices,
            bullet = "> "
        )
        result = cli.launch()
        if result in ("---", ""):
            continue
        elif result == "Back":
            break
        else:
            playsound('Sounds/ui_hacking_charenter_01.wav')
            clear()
            subprocess.run(games[result])

def networkmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Network Menu"))
        print(Middle("=================================================="))
        print("")
        networks = load_networks()
        choices = list(networks.keys()) + ["---", "Back"]
        cli = Bullet(
            prompt = Format.underline + "Select Network Program" + Format.end + "\n",
            choices = choices,
            bullet = "> "
        )
        result = cli.launch()
        if result in ("---", ""):
            continue
        elif result == "Back":
            break
        else:
            playsound('Sounds/ui_hacking_charenter_01.wav')
            clear()
            subprocess.run(networks[result])

def logsmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Logs Menu"))
        print(Middle("=================================================="))
        print("")
        cli = Bullet(
            prompt = Format.underline + "Choose Action" + Format.end + "\n",
            choices = ["Create New Log", "View Logs", "Delete Logs", "Back"], 
            bullet = "> "
        )
        result = cli.launch()
        if result == "Create New Log":
            journal_new()
        if result == "View Logs":
            journal_view()
        if result == "Delete Logs":
            journal_delete()
        if result == "Back":
            break

def settingsmenu():
    while True:
        playsound('Sounds/ui_hacking_charenter_01.wav')
        clear()
        title()
        print("")
        print(Middle("Settings Menu"))
        print(Middle("=================================================="))
        print("")
        cli = Bullet(
            prompt = Format.underline + "Configurations" + Format.end + "\n",
            choices = ["Edit Menus", "---", "Back"], 
            bullet = "> "
        )
        result = cli.launch()
        if result in ("---", ""):
            continue
        elif result == "Back":
            break
        elif result == "Edit Menus":
            while True:
                playsound('Sounds/ui_hacking_charenter_01.wav')
                clear()
                title()
                print("")
                print(Middle("Edit Menus"))
                print(Middle("=================================================="))
                print("")
                menu_cli = Bullet(
                    prompt = Format.underline + "Edit Menu" + Format.end + "\n",
                    choices = ["Edit Applications", "Edit Documents", "Edit Network", "Edit Games", "---", "Back"],
                    bullet = "> "
                )
                menu_result = menu_cli.launch()
                if menu_result in ("---", ""):
                    continue
                elif menu_result == "Back":
                    break
                elif menu_result == "Edit Applications":
                    while True:
                        playsound('Sounds/ui_hacking_charenter_01.wav')
                        clear()
                        title()
                        print("")
                        print(Middle("Edit Applications Menu"))
                        print(Middle("=================================================="))
                        print("")
                        apps = load_apps()
                        app_cli = Bullet(
                        prompt = Format.underline + "Edit Applications" + Format.end + "\n",
                        choices = ["Add App", "Delete App", "---", "Back"],
                        bullet = "> "
                        )
                        app_result = app_cli.launch()
                        if app_result in ("---", ""):
                            continue
                        elif app_result == "Back":
                            break
                        elif app_result == "Add App":
                            add_app(apps)
                        elif app_result == "Delete App":
                            delete_app(apps)
                elif menu_result == "Edit Games":
                    while True:
                        playsound('Sounds/ui_hacking_charenter_01.wav')
                        clear()
                        title()
                        print("")
                        print(Middle("Edit Games Menu"))
                        print(Middle("=================================================="))
                        print("")
                        games = load_games()
                        game_cli = Bullet(
                        prompt = Format.underline + "Edit Games" + Format.end + "\n",
                        choices = ["Add Game", "Delete Game", "---", "Back"],
                        bullet = "> "
                        )
                        game_result = game_cli.launch()
                        if game_result in ("---", ""):
                            continue
                        elif game_result == "Back":
                            break
                        elif game_result == "Add Game":
                            add_game(games)
                        elif game_result == "Delete Game":
                            delete_game(games)
                elif menu_result == "Edit Network":
                    while True:
                        playsound('Sounds/ui_hacking_charenter_01.wav')
                        clear()
                        title()
                        print("")
                        print(Middle("Edit Network Menu"))
                        print(Middle("=================================================="))
                        print("")
                        networks = load_networks()
                        network_cli = Bullet(
                        prompt = Format.underline + "Edit Network" + Format.end + "\n",
                        choices = ["Add Network", "Delete Network", "---", "Back"],
                        bullet = "> "
                        )
                        network_result = network_cli.launch()
                        if network_result in ("---", ""):
                            continue
                        elif network_result == "Back":
                            break
                        elif network_result == "Add Network":
                            add_network(networks)
                        elif network_result == "Delete Network":
                            delete_network(networks)
                elif menu_result == "Edit Documents":
                    while True:
                        playsound('Sounds/ui_hacking_charenter_01.wav')
                        clear()
                        title()
                        print("")
                        print(Middle("Edit Documents Menu"))
                        print(Middle("=================================================="))
                        print("")
                        categories = load_categories()
                        category_cli = Bullet(
                        prompt = Format.underline + "Edit Document Categories" + Format.end + "\n",
                        choices = ["Add Category", "Delete Category", "---", "Back"],
                        bullet = "> "
                        )
                        category_result = category_cli.launch()
                        if category_result in ("---", ""):
                            continue
                        elif category_result == "Back":
                            break
                        elif category_result == "Add Category":
                            add_category(categories)
                        elif category_result == "Delete Category":
                            delete_category(categories)
                elif menu_result == "Back":
                    break

#bootup()
if __name__ == "__main__":
    mainmenu()