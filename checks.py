import shutil
import subprocess
import sys

# ─── Dependency definitions ───────────────────────────────────────────────────
REQUIRED_PYTHON_PACKAGES = {
    "pyte":       "pip install pyte",
    "psutil":     "pip install psutil",
    "playsound":  "pip install playsound  (optional, needed for sound)",
}

REQUIRED_CLI_TOOLS = {
    "tmux": "Install via your package manager: brew install tmux / apt install tmux",
    "epy":  "pip install epy-reader  (optional, needed for ebook reading)",
    "vim":  "Install via your package manager  (optional, needed for editing)",
}

OPTIONAL = {"playsound", "epy", "vim"}

# ─── Checkers ─────────────────────────────────────────────────────────────────
def check_python_packages():
    missing = []
    for pkg, hint in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(pkg)
        except ImportError:
            missing.append((pkg, hint))
    return missing

def check_cli_tools():
    missing = []
    for tool, hint in REQUIRED_CLI_TOOLS.items():
        if not shutil.which(tool):
            missing.append((tool, hint))
    return missing

def has_tmux():
    return shutil.which("tmux") is not None

def in_tmux():
    return "TMUX" in __import__("os").environ

# ─── Pre-flight report ────────────────────────────────────────────────────────
def run_preflight(skip_optional=True):
    """
    Check all dependencies. Returns (ok, warnings, errors).
    ok = True if all required deps are present.
    warnings = list of missing optional dep messages.
    errors   = list of missing required dep messages.
    """
    errors   = []
    warnings = []

    for pkg, hint in check_python_packages():
        if pkg in OPTIONAL:
            warnings.append(f"[optional] Python package '{pkg}' not found.\n  -> {hint}")
        else:
            errors.append(f"[required] Python package '{pkg}' not found.\n  -> {hint}")

    for tool, hint in check_cli_tools():
        if tool in OPTIONAL:
            warnings.append(f"[optional] CLI tool '{tool}' not found.\n  -> {hint}")
        else:
            errors.append(f"[required] CLI tool '{tool}' not found.\n  -> {hint}")

    ok = len(errors) == 0
    return ok, warnings, errors

def print_preflight_report():
    ok, warnings, errors = run_preflight()
    if errors:
        print("\n=== RobcOS: Missing required dependencies ===")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print("\n=== RobcOS: Missing optional dependencies ===")
        for w in warnings:
            print(f"  ! {w}")
    if ok and not warnings:
        print("All dependencies satisfied.")
    return ok
