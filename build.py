#!/usr/bin/env python3
"""Cross-platform build script — produces a standalone Montage_Maker executable via PyInstaller."""

import platform
import subprocess
import sys
from pathlib import Path

APP_NAME = "Montage_Maker"
MAIN_SCRIPT = "app.py"


def main():
    system = platform.system()

    if system == "Windows":
        venv = Path("venv_win")
        python = venv / "Scripts" / "python.exe"
        pip = venv / "Scripts" / "pip.exe"
        pyinstaller = venv / "Scripts" / "pyinstaller.exe"
        sep = ";"
    else:
        venv = Path("venv_mac")
        python = venv / "bin" / "python"
        pip = venv / "bin" / "pip"
        pyinstaller = venv / "bin" / "pyinstaller"
        sep = ":"

    if not venv.exists():
        print(f"Error: virtual environment '{venv}' not found — run setup.py first.")
        sys.exit(1)

    # Install PyInstaller into the venv if missing
    check = subprocess.run([str(pip), "show", "pyinstaller"], capture_output=True)
    if check.returncode != 0:
        print("PyInstaller not found — installing...")
        subprocess.check_call([str(pip), "install", "pyinstaller"])

    # Locate the nicegui package directory inside the venv
    loc = subprocess.run(
        [str(python), "-c", "import nicegui, pathlib; print(pathlib.Path(nicegui.__file__).parent)"],
        capture_output=True, text=True,
    )
    if loc.returncode != 0:
        print("Error: could not locate nicegui in the venv.")
        sys.exit(1)
    nicegui_dir = loc.stdout.strip()

    cmd = [
        str(pyinstaller),
        "--name", APP_NAME,
        "--onefile",
        "--add-data", f"{nicegui_dir}{sep}nicegui",
        MAIN_SCRIPT,
    ]

    print("PyInstaller command:")
    print(" ", " ".join(cmd))
    print()

    rc = subprocess.call(cmd)

    if rc == 0:
        exe = Path("dist") / (APP_NAME + (".exe" if system == "Windows" else ""))
        print(f"\nBuild complete: {exe}")
    else:
        print("\nBuild failed.")
        sys.exit(rc)


if __name__ == "__main__":
    main()
