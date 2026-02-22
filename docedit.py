from pathlib import Path
from config import load_categories, save_categories
from ui import run_menu, curses_input, curses_confirm, curses_message

def add_category(stdscr, categories):
    name = curses_input(stdscr, "Enter category name:")
    if not name:
        curses_message(stdscr, "Error: Invalid Input.")
        return
    path_input = curses_input(stdscr, "Enter folder path:")
    path = Path(path_input).expanduser()
    if not path.exists() or not path.is_dir():
        curses_message(stdscr, "Error: Invalid Directory.")
        return
    categories[name] = str(path)
    save_categories(categories)
    curses_message(stdscr, "Category Added.")

def delete_category(stdscr, categories):
    if not categories:
        curses_message(stdscr, "Error: No categories to delete.")
        return
    options = list(categories.keys()) + ["Back"]
    result = run_menu(stdscr, "Delete Category", options)
    if result == "Back" or result not in categories:
        return
    if curses_confirm(stdscr, f"Delete '{result}'?"):
        del categories[result]
        save_categories(categories)
        curses_message(stdscr, "Deleted.")
    else:
        curses_message(stdscr, "Cancelled.", 0.8)

def edit_documents_menu(stdscr):
    while True:
        result = run_menu(stdscr, "Edit Documents",
                          ["Add Category", "Delete Category", "---", "Back"])
        if result == "Back":
            return result
        elif result == "Add Category":
            add_category(stdscr, load_categories())
        elif result == "Delete Category":
            delete_category(stdscr, load_categories())
