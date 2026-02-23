import shutil
import subprocess
from config import (load_apps, save_apps, load_games, save_games,
                    load_networks, save_networks)
from ui import run_menu, curses_input, curses_confirm, curses_message, curses_pager, curses_box_message
from launcher import _suspend, _resume

PACKAGE_MANAGERS = {
    'brew':    [],
    'apt':     ['-y'],
    'apt-get': ['-y'],
    'dnf':     ['-y'],
    'pacman':  ['--noconfirm'],
    'zypper':  ['-n'],
}

def has_internet():
    try:
        import urllib.request
        urllib.request.urlopen("https://www.google.com", timeout=3)
        return True
    except Exception:
        return False

def detect_package_manager():
    for pm in PACKAGE_MANAGERS:
        if shutil.which(pm):
            return pm
    return None

def is_installed(cmd):
    return shutil.which(cmd) is not None

def search_packages(pm, query):
    try:
        result = subprocess.run([pm, "search", query],
                                capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split("\n")
        return [l for l in lines if l.strip() and not l.startswith("=")]
    except Exception:
        return []

def get_package_info(pm, pkg):
    try:
        if pm == "brew":
            result = subprocess.run(["brew", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split("\n")
            return lines[1].strip() if len(lines) > 1 else "No description available."
        elif pm in ("apt", "apt-get"):
            result = subprocess.run(["apt", "show", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Description:"):
                    return line.replace("Description:", "").strip()
        elif pm == "dnf":
            result = subprocess.run(["dnf", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Summary"):
                    return line.split(":", 1)[-1].strip()
        elif pm == "pacman":
            result = subprocess.run(["pacman", "-Si", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Description"):
                    return line.split(":", 1)[-1].strip()
        elif pm == "zypper":
            result = subprocess.run(["zypper", "info", pkg],
                                    capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.startswith("Summary"):
                    return line.split(":", 1)[-1].strip()
        return "No description available."
    except Exception:
        return "Could not fetch description."

def get_installed_packages(pm):
    try:
        if pm == "brew":
            result = subprocess.run(["brew", "list"],
                                    capture_output=True, text=True, timeout=10)
        elif pm in ("apt", "apt-get"):
            result = subprocess.run(["apt", "list", "--installed"],
                                    capture_output=True, text=True, timeout=10)
        elif pm == "dnf":
            result = subprocess.run(["dnf", "list", "installed"],
                                    capture_output=True, text=True, timeout=10)
        elif pm == "pacman":
            result = subprocess.run(["pacman", "-Q"],
                                    capture_output=True, text=True, timeout=10)
        elif pm == "zypper":
            result = subprocess.run(["zypper", "se", "--installed-only"],
                                    capture_output=True, text=True, timeout=10)
        else:
            return []
        pkgs = []
        for l in result.stdout.strip().split("\n"):
            if not l.strip() or l.startswith("WARNING") or l.startswith("Listing"):
                continue
            name = l.split()[0].split("/")[0]   # strip /source,now for apt
            if name:
                pkgs.append(name)
        return pkgs
    except Exception:
        return []

def appstore_menu(stdscr):
    from auth import is_admin
    from config import get_current_user
    if not is_admin(get_current_user()):
        curses_message(stdscr, "Access denied. Admin only.")
        return
    pm = detect_package_manager()

    while True:
        result = run_menu(stdscr, "Program Installer",
                          ["Search", "Installed Apps", "---", "Back"],
                          subtitle=f"Package Manager: {pm or 'Not Found'}")
        if result == "Back":
            break

        elif result == "Search":
            query = curses_input(stdscr, "Search packages:")
            if not query:
                continue
            if not has_internet():
                curses_message(stdscr, "Error: No internet connection")
                continue
            curses_message(stdscr, "Searching...", 0.5)
            results = search_packages(pm, query)
            if not results:
                curses_message(stdscr, "No results found.")
                continue
            page = 0
            while True:
                h, w = stdscr.getmaxyx()
                max_per_page = max(5, h - 18)
                start = page * max_per_page
                end = start + max_per_page
                page_results = results[start:end]
                total_pages = max(1, (len(results) - 1) // max_per_page + 1)
                choices = []
                for r in page_results:
                    cmd = r.split()[0]
                    status = "[installed]" if is_installed(cmd) else "[get]      "
                    choices.append(f"{status} {r}")
                if page > 0:
                    choices.append("< Prev Page")
                if end < len(results):
                    choices.append("> Next Page")
                choices += ["---", "Back"]
                pkg_result = run_menu(stdscr, "Program Installer", choices,
                                      subtitle=f"Results: {query}  |  Page {page + 1}/{total_pages}")
                if pkg_result == "Back":
                    break
                elif pkg_result == "> Next Page":
                    page += 1
                elif pkg_result == "< Prev Page":
                    page -= 1
                else:
                    pkg = pkg_result.split()[1]
                    if is_installed(pkg):
                        curses_message(stdscr, f"{pkg} is already installed.")
                    elif pm is None:
                        curses_message(stdscr, "Error: No supported package manager found.")
                    else:
                        info = get_package_info(pm, pkg) if has_internet() else "No internet - description unavailable."
                        curses_pager(stdscr, f"{pkg}\n\n{info}", title="Package Info")
                        if curses_confirm(stdscr, f"Install {pkg}?"):
                            flags = PACKAGE_MANAGERS.get(pm, [])
                            launch_cmd = ([pm, "install"] + flags + [pkg] if pm == "brew"
                                          else ["sudo", pm, "install"] + flags + [pkg])
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} installed successfully!")
                            else:
                                curses_box_message(stdscr, f"Failed to install {pkg}.")

        elif result == "Installed Apps":
            curses_message(stdscr, "Loading...", 0.5)
            installed = get_installed_packages(pm)
            if not installed:
                curses_message(stdscr, "No installed packages found.")
                continue
            filter_query = ""
            page = 0
            while True:
                h, w = stdscr.getmaxyx()
                max_items = max(3, h - 18)
                filtered = ([p for p in installed if filter_query.lower() in p.lower()]
                            if filter_query else installed)
                start = page * max_items
                end = start + max_items
                page_results = filtered[start:end]
                total_pages = max(1, (len(filtered) - 1) // max_items + 1)
                search_label = f"Search: {filter_query}" if filter_query else "Search..."
                choices = [search_label, "---"] + [f"  {p}" for p in page_results]
                if page > 0:
                    choices.append("< Prev Page")
                if end < len(filtered):
                    choices.append("> Next Page")
                choices += ["---", "Back"]
                pkg_result = run_menu(stdscr, "Installed Apps", choices,
                                      subtitle=f"{len(filtered)} packages  |  Page {page + 1}/{total_pages}")
                if pkg_result == "Back":
                    break
                elif pkg_result == "> Next Page":
                    page += 1
                elif pkg_result == "< Prev Page":
                    page -= 1
                elif pkg_result == search_label:
                    filter_query = curses_input(stdscr, "Filter packages:")
                    page = 0
                else:
                    pkg = pkg_result.strip()
                    info = (get_package_info(pm, pkg) if has_internet()
                            else "No internet - description unavailable.")
                    action = run_menu(stdscr, pkg,
                                      ["Update", "Reinstall", "Uninstall", "Add to Menu", "---", "Back"],
                                      subtitle=info)
                    if action == "Reinstall":
                        if not has_internet():
                            curses_message(stdscr, "Error: No internet connection.")
                        elif curses_confirm(stdscr, f"Reinstall {pkg}?"):
                            flags = PACKAGE_MANAGERS.get(pm, [])
                            # Each PM has its own reinstall syntax
                            if pm == "brew":
                                launch_cmd = ["brew", "reinstall"] + flags + [pkg]
                            elif pm in ("apt", "apt-get"):
                                launch_cmd = ["sudo", pm, "install", "--reinstall"] + flags + [pkg]
                            elif pm == "dnf":
                                launch_cmd = ["sudo", "dnf", "reinstall"] + flags + [pkg]
                            elif pm == "pacman":
                                launch_cmd = ["sudo", "pacman", "-S"] + flags + [pkg]
                            elif pm == "zypper":
                                launch_cmd = ["sudo", "zypper", "install", "--force"] + flags + [pkg]
                            else:
                                curses_message(stdscr, f"Reinstall not supported for {pm}.")
                                continue
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} reinstalled.")
                            else:
                                curses_box_message(stdscr, f"Failed to reinstall {pkg}.")
                    elif action == "Uninstall":
                        if curses_confirm(stdscr, f"Uninstall {pkg}?"):
                            flags = PACKAGE_MANAGERS.get(pm, [])
                            launch_cmd = ([pm, "uninstall"] + flags + [pkg] if pm == "brew"
                                          else ["sudo", pm, "remove"] + flags + [pkg])
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} uninstalled.")
                                installed = get_installed_packages(pm)
                            else:
                                curses_box_message(stdscr, f"Failed to uninstall {pkg}.")
                    elif action == "Update":
                        if not has_internet():
                            curses_message(stdscr, "Error: No internet connection.")
                        else:
                            launch_cmd = ([pm, "upgrade", pkg] if pm == "brew"
                                          else ["sudo", pm, "upgrade", pkg])
                            _suspend(stdscr)
                            proc = subprocess.run(launch_cmd)
                            _resume(stdscr)
                            if proc.returncode == 0:
                                curses_box_message(stdscr, f"{pkg} updated.")
                            else:
                                curses_box_message(stdscr, f"Failed to update {pkg}.")
                    elif action == "Add to Menu":
                        menu_choice = run_menu(stdscr, "Add to Menu",
                                               ["Applications", "Games", "Network", "---", "Back"])
                        if menu_choice != "Back":
                            display_name = curses_input(stdscr, f"Enter display name for '{pkg}':")
                            if not display_name:
                                display_name = pkg
                            if menu_choice == "Applications":
                                data = load_apps()
                                data[display_name] = [pkg]
                                save_apps(data)
                            elif menu_choice == "Games":
                                data = load_games()
                                data[display_name] = [pkg]
                                save_games(data)
                            elif menu_choice == "Network":
                                data = load_networks()
                                data[display_name] = [pkg]
                                save_networks(data)
                            curses_box_message(stdscr, f"{display_name} added to {menu_choice}.")