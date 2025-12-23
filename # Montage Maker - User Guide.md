# Montage Maker - User Guide

A Python utility to batch-process folders of images into grid layouts using ImageMagick. It supports robust configuration via presets (for social media sizing), manual overrides, cropping, and labeling.

## 1. Prerequisites & Installation

This script relies on **ImageMagick** being installed and accessible via your system's command line.

### Windows 10/11
1.  **Download:** Go to the [ImageMagick Download Page](https://imagemagick.org/script/download.php#windows) and download the latest **DLL** version (e.g., `ImageMagick-x.x.x-Q16-x64-dll.exe`).
2.  **Install:** Run the installer.
3.  **CRITICAL STEP:** During installation, check the box that says:
    * [x] **Add application directory to your system path**
    * [x] **Install Legacy Utilities (e.g. convert)** (Optional but recommended)
4.  **Ghostscript:** If the installer asks to install Ghostscript, say **Yes**. If not, download it separately from [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html).

### Mac (macOS - Apple Silicon/Intel)
The easiest way is using **Homebrew**.
1.  Open your Terminal.
2.  Run:
    ```bash
    brew install imagemagick
    brew install ghostscript
    ```

### Linux (Ubuntu/Debian)
1.  Open your Terminal.
2.  Run:
    ```bash
    sudo apt update
    sudo apt install imagemagick ghostscript
    ```

### How to Verify Installation
Open a new terminal (Command Prompt, PowerShell, or Bash) and type:
```bash
montage -version
```
**Success:** You see version details (e.g., `Version: ImageMagick 7.1.1...`).
**Failure:** You see `command not found`. *Solution: Restart your terminal or reinstall/check PATH settings.*

---

## 2. Command Line Arguments

**Basic Syntax:**
```bash
# Windows
python montage_maker.py [GRID] [OPTIONS]

# Mac / Linux (if 'python' command is not found, use 'python3')
python3 montage_maker.py [GRID] [OPTIONS]
```

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GRID` | Optional* | `2x2` | The layout columns and rows (e.g., `2x2`). Required unless using a preset that defines it. |
| `--preset` | Optional | None | Loads settings from `config.ini`. |
| `--ext` | Optional | `jpg` | The file extension to look for (e.g., `png`, `jpeg`). |
| `--size` | Optional | `500x500+10+10` | The geometry of each tile: `WxH+BorderX+BorderY`. **Use quotes.** |
| `--label` | Flag | `False` | If present, prints the filename underneath the image. |
| `--prefix`| Optional | `montage` | The prefix for output files (e.g., `my_vacation` becomes `my_vacation_01.jpg`). |
| `--crop` | Optional | None | Crops the source image to `WxH` from the center *before* fitting it to the tile. |

*\*Grid is optional if a preset is provided.*

---

## 3. Configuration File (config.ini)

You can save frequently used settings in a `config.ini` file located in the same folder as the script.

**Example config.ini:**
```ini
[instagram_post]
grid = 2x2
size = 1080x1080+0+0
crop = 1080x1080
ext = jpg
prefix = ig_post

[youtube_thumb]
grid = 2x2
size = 640x360+0+0
crop = 1280x720
ext = jpg
prefix = yt_thumb
```

---

## 4. Usage Examples

### Scenario A: Using a Preset
You want to create Instagram posts using the settings defined in your config file.
```bash
python montage_maker.py --preset instagram_post
```

### Scenario B: Preset with Override
You want to use the "Instagram" settings (cropping, size, etc.) but you only have enough images for a 1x1 grid.
```bash
python montage_maker.py 1x1 --preset instagram_post
```

### Scenario C: Manual Mode (No Preset)
You just want a quick 2x2 grid of 500px squares.
```bash
python montage_maker.py 2x2 --size "500x500+5+5"
```

### Scenario D: Complex Crop
Cropping HD video frames (1920x1080) into a 3x3 contact sheet.
```bash
python montage_maker.py 3x3 --crop "1920x1080" --prefix "dailies"
```

---

## 5. Troubleshooting

**Error: `montage: command not found`**
* **Cause:** ImageMagick is not installed or not in your system PATH.
* **Fix:** Reinstall ImageMagick and ensure "Add to PATH" is checked (Windows).

**Error: `montage_maker.py: error: the following arguments are required: grid`**
* **Cause:** You didn't provide a grid size AND you didn't provide a preset.
* **Fix:** Provide one or the other (e.g., `python montage_maker.py 2x2`).

**Images looking squashed?**
* Check your `--size` vs `--crop`. If you crop a 16:9 image (wide) but force it into a 1:1 (square) tile size, it will distort. Match your aspect ratios!

---

## 6. Bonus Tip: Creating Shortcuts (Mac/Linux)

If you find yourself using the same complex command often, you can create a permanent shortcut (alias).

1.  Open your shell configuration file (usually `~/.bashrc` or `~/.zshrc`).
2.  Add a line like this at the bottom:
    ```bash
    alias make_sheets='python3 /Users/ed/Scripts/montage_maker.py --preset instagram_post'
    ```
3.  Save and restart your terminal. Now just type `make_sheets`!