"""
===============================================================================
Project:     Montage Maker
Script:      setup.py
Author:      Ed Johnson
Description: Montage Maker bootstrap script.
                Run with the system Python (not inside a venv) to:
                1. Check and install ImageMagick and Ghostscript
                2. Create a virtual environment (venv_win or venv_mac)
                3. Install Python dependencies from requirements.txt

                Usage:
                    Windows:  python setup.py
                    macOS:    python3 setup.py

Last Update: 2026-06-18
Version:     1.0.0
License:     MIT License for source code.
             Project artwork, branding, documentation, and promotional assets
             are licensed separately. See LICENSE,
             ASSET_AND_BRANDING_LICENSE.md, and THIRD_PARTY_NOTICES.md.
===============================================================================
"""

import shutil
import subprocess
import sys
import venv
from pathlib import Path

MIN_PYTHON = (3, 8)
VENV_WIN = "venv_win"
VENV_MAC = "venv_mac"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd):
    subprocess.run(cmd, check=True)


def _available(name):
    return shutil.which(name) is not None


def _probe(*cmds):
    """Return True if any of the given commands exit successfully."""
    for cmd in cmds:
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return False


def _imagemagick_present():
    return _probe(
        ["montage", "--version"],
        ["magick", "montage", "--version"],
    )


# ---------------------------------------------------------------------------
# System dependency installation
# ---------------------------------------------------------------------------

def _install_win(winget_id, choco_id, label):
    print(f"  Installing {label}...")
    if _available("winget"):
        try:
            _run([
                "winget", "install", "--id", winget_id, "-e",
                "--accept-package-agreements", "--accept-source-agreements",
            ])
            print(f"  {label} installed via winget.")
            return
        except subprocess.CalledProcessError:
            pass
    if _available("choco"):
        try:
            _run(["choco", "install", choco_id, "-y"])
            print(f"  {label} installed via Chocolatey.")
            return
        except subprocess.CalledProcessError:
            pass
    print(f"\n  WARNING: Could not install {label} automatically.")
    print(f"  winget and Chocolatey were both unavailable or failed.")


def _install_mac(brew_pkg, label):
    print(f"  Installing {label}...")
    if not _available("brew"):
        sys.exit(
            "\nHomebrew is required to install system dependencies on macOS.\n"
            "Install it from https://brew.sh then re-run this script."
        )
    _run(["brew", "install", brew_pkg])
    print(f"  {label} installed via Homebrew.")


def _check_system_deps(is_windows):
    print("\n[1/3] Checking system dependencies...")

    if _imagemagick_present():
        print("  ImageMagick .. OK")
    else:
        if is_windows:
            _install_win("ImageMagick.ImageMagick", "imagemagick", "ImageMagick")
        else:
            _install_mac("imagemagick", "ImageMagick")
        if not _imagemagick_present():
            print(
                "\n  WARNING: 'montage' command still not found after installation.\n"
                "  You may need to open a new terminal so PATH updates take effect,\n"
                "  then re-run this script."
            )


# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------

def _create_venv(venv_path):
    print(f"\n[2/3] Setting up virtual environment '{venv_path}' ...")
    if venv_path.exists():
        print("  Already exists — skipping creation.")
    else:
        venv.create(str(venv_path), with_pip=True)
        print("  Created.")


def _install_deps(venv_path, is_windows):
    print("\n[3/3] Installing Python dependencies...")
    scripts = "Scripts" if is_windows else "bin"
    # Use `python -m pip` so Windows doesn't lock the pip.exe binary
    py = venv_path / scripts / ("python.exe" if is_windows else "python")
    _run([str(py), "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    _run([str(py), "-m", "pip", "install", "-r", "requirements.txt"])
    print("  Done.")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_next_steps(venv_path, is_windows):
    scripts = "Scripts" if is_windows else "bin"
    sep = "\\" if is_windows else "/"
    activate = (
        f"{venv_path}\\Scripts\\activate"
        if is_windows
        else f"source {venv_path}/bin/activate"
    )
    run_direct = f"{venv_path}{sep}{scripts}{sep}python app.py"

    print("\n" + "=" * 54)
    print("  Setup complete!")
    print()
    print("  Run the app:")
    print(f"    {run_direct}")
    print()
    print("  Or activate the environment first:")
    print(f"    {activate}")
    print("    python app.py")
    print()
    print("  To build a standalone executable:")
    print(f"    {venv_path}{sep}{scripts}{sep}pip install \"nicegui[pyinstaller]\"")
    print("    nicegui-pack --onefile --name Montage_Maker app.py")
    if is_windows:
        print()
        print("  NOTE: The native window requires the Microsoft Edge")
        print("  WebView2 runtime (pre-installed on Windows 10/11).")
        print("  If the window fails to open, download WebView2 from:")
        print("  https://developer.microsoft.com/microsoft-edge/webview2/")
    print("=" * 54)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if sys.version_info < MIN_PYTHON:
        sys.exit(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required "
            f"(found {sys.version.split()[0]})"
        )

    is_windows = sys.platform == "win32"
    venv_path = Path(VENV_WIN if is_windows else VENV_MAC)

    print("Montage Maker Setup")
    print(f"  Platform : {'Windows' if is_windows else 'macOS'}")
    print(f"  Python   : {sys.version.split()[0]}")

    _check_system_deps(is_windows)
    _create_venv(venv_path)
    _install_deps(venv_path, is_windows)
    _print_next_steps(venv_path, is_windows)


if __name__ == "__main__":
    main()
