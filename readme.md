# Montage Maker

A desktop GUI and CLI tool for batch-creating image grid montages using ImageMagick. Point it at a folder of images, dial in your settings, and generate one or more tiled output pages.

![Montage Maker](resources/MontageMakerIcon.png)

---

## Prerequisites

Montage Maker requires **ImageMagick** to be installed and the `montage` command to be on your PATH.

### Windows 10 / 11
1. Download the latest installer from [imagemagick.org/script/download.php](https://imagemagick.org/script/download.php#windows) (choose the **DLL** build, 64-bit).
2. Run the installer. Check **"Add application directory to your system path"**.

### macOS
```bash
brew install imagemagick
```

### Linux (Ubuntu / Debian)
```bash
sudo apt update && sudo apt install imagemagick
```

### Verify
```bash
montage -version
```
You should see a version line like `Version: ImageMagick 7.x.x ...`. If not, restart your terminal and check your PATH.

---

## Setup

Run the bootstrap script once with your **system Python** (not inside a venv). It installs ImageMagick if missing, creates a virtual environment, and installs Python dependencies.

```bash
# Windows
python setup.py

# macOS / Linux
python3 setup.py
```

The script creates `venv_win/` (Windows) or `venv_mac/` (macOS/Linux) and installs `nicegui` and `pywebview`.

---

## Running the App

### GUI (primary)
```bash
# Windows
venv_win\Scripts\python app.py

# macOS / Linux
venv_mac/bin/python app.py
```

A native desktop window opens — no browser required.

### CLI (original engine, still functional)
```bash
python montage_maker.py 2x2
python montage_maker.py --preset "Instagram Post"
python montage_maker.py 2x2 --size "500x500+5+5" --label --fontsize 24
```

---

## GUI Overview

The app uses a three-column layout:

| Column | Contents |
|---|---|
| Left (40%) | Image folder, Output folder, Generate button, output previews |
| Middle (30%) | Preset selector · Grid · Tile size & spacing · Background · Output (crop/format) |
| Right (30%) | Output filename prefix · Text · Effects |

### Header
Two controls sit in the top-right corner:
- **Theme** dropdown — switch between four themes: **Light**, **Warm** (light modes) or **Dark**, **Midnight** (dark modes). Saved to `session.ini` and restored on next launch.
- **Port: 8000** button — opens a dialog to change the server port. Takes effect after restarting the app. Persisted in `session.ini`.

---

## Settings Reference

### Grid
| Field | Description |
|---|---|
| Columns | Number of tiles per row |
| Rows | Number of rows per page. Pages are created automatically when images exceed one grid. |

### Tile size & spacing
| Field | Format | Description |
|---|---|---|
| Width / Height | pixels | Size of each individual tile |
| H spacing / V spacing | pixels | Gap between tiles (ImageMagick `-geometry` border) |

### Background
| Field | Description |
|---|---|
| Color | Background fill color behind tiles (hex or named color) |
| Transparent | Passes `-background none`. Output format is automatically forced to PNG. |

### Output
| Field | Description |
|---|---|
| Crop | Center-crops source images to `WxH` before tiling (e.g. `1080x1080`) |
| Format | Output file extension: `png`, `jpg`, `bmp`, `tiff` |

### Output filename prefix
Base name for generated files. Pages are numbered automatically: `prefix_01.png`, `prefix_02.png`, etc.

### Text
| Field | Description |
|---|---|
| Title | Text banner printed above the entire montage (`-title`) |
| Font name | ImageMagick font name for labels and title (e.g. `Arial`, `Helvetica`) |
| Show filename labels | Adds the source filename below each tile |
| Label font size | Point size for filename labels |

### Effects

| Control | Description |
|---|---|
| **Mode** | `Frame` — ornamental 3D border around tiles. `Concatenate` — zero spacing, tiles touch. |
| **Quality (JPG)** | JPEG compression quality 0–100 (default 85). Has no effect on PNG. |
| **Drop shadow** | Adds a drop shadow behind each tile. Automatically disabled while Polaroid is active (they conflict; `+polaroid` bakes in its own shadow). |
| **Polaroid** | Applies a Polaroid-style effect. Set a fixed angle or enable **Random (±15°)** for variety. |
| **Frame** | Draws a beveled ornamental frame around each tile. Controls: Width, Height, Outer bevel, Inner bevel. Set **Matte color** for the frame color. Pairs naturally with Mode = Frame. |
| **Border** | Adds a flat solid border around each tile. Controls: Width, Height. Set **Border color**. |

---

## Preset Manager

Click **Manage…** next to the Preset selector to open the preset manager. You can:
- **Load** an existing preset to edit it
- **Save** under any name (spaces and proper case allowed; `]` and newlines are not)
- **Delete** a preset
- **Clear** the form to start fresh

Presets are stored in `config.ini` in the same directory as the script, sorted alphabetically.

### Bundled presets

| Preset | Grid | Notes |
|---|---|---|
| Contact Sheet | 4×4 | 300px tiles, labeled, cropped square |
| Filmstrip | 4×1 | 480px tiles, Concatenate mode, black background |
| Gallery Wall | 2×2 | 500px tiles, beveled frame, drop shadow, warm background |
| Instagram Post | 2×2 | Cropped to 1080×1080, JPG |
| Instagram Story | 1×1 | Cropped to 1080×1920, JPG |
| Link Preview | 2×2 | Cropped to 1200×630, JPG — universal OG image format |
| Pinterest Pin | 2×3 | Cropped to 1000×1500, JPG |
| Polaroid | 3×2 | Polaroid effect, random angle, dark background, drop shadow |
| Square 3×3 | 3×3 | 720px tiles, PNG |
| X Post | 2×2 | Cropped to 1200×675, JPG |
| YouTube Thumb | 2×2 | Cropped to 1280×720 |

---

## File Conflict Dialog

When output files already exist, a dialog appears with three options:

| Option | Behavior |
|---|---|
| **Cancel** | Abort — nothing is written |
| **Auto-increment** | Appends `_v2`, `_v3`, etc. to the prefix to create a new set alongside the existing ones |
| **Overwrite** | Replaces the **most recent version** of the output files only (e.g. `montage_v3_*.png`), leaving earlier versions untouched |

The dialog shows the total file count and the exact prefix that Overwrite will target.

---

## config.ini Key Reference

| Key | Format | Example | Notes |
|---|---|---|---|
| `grid` | `CxR` | `2x3` | Columns × rows |
| `size` | `WxH+HB+VB` | `500x500+10+10` | Tile size + spacing |
| `background` | color | `#ffffff` | Hex or ImageMagick color name |
| `transparent` | `on`/`off` | `on` | Forces background to `none`; output must be PNG |
| `crop` | `WxH` | `1080x1080` | Center-crop applied before tiling |
| `ext` | extension | `png` | Output format |
| `prefix` | string | `montage` | Output filename prefix |
| `fontsize` | integer | `12` | Label point size |
| `labels` | `on`/`off` | `on` | Show filename labels |
| `title` | string | `My Trip` | Title banner above montage |
| `font` | string | `Arial` | Font name for labels/title |
| `quality` | `0`–`100` | `85` | JPEG quality |
| `mode` | type | `Frame` | `Frame` or `Concatenate` |
| `shadow` | `on`/`off` | `on` | Drop shadow behind tiles |
| `frame` | `WxH+outer+inner` | `6x6+3+3` | Frame geometry (bevel sizes) |
| `mattecolor` | color | `#808080` | Frame color |
| `border` | `WxH` | `5x5` | Flat border width/height |
| `bordercolor` | color | `#000000` | Border color |
| `polaroid` | `random` or angle | `random` | Polaroid effect; `random` = ±15°, or a fixed angle |

---

## session.ini

Auto-created in the project directory (gitignored). Persists three things across sessions:

```ini
[paths]
input = /path/to/last/used/image/folder
output = /path/to/last/used/output/folder

[server]
port = 8000

[ui]
theme = Dark
```

---

## CLI Reference

```bash
python montage_maker.py [GRID] [OPTIONS]
```

| Argument | Default | Description |
|---|---|---|
| `GRID` | `2x2` | Grid layout (e.g. `3x4`). Optional if `--preset` is used. |
| `--preset NAME` | — | Load settings from a `config.ini` section |
| `--ext EXT` | `png` | Output format |
| `--size WxH+HB+VB` | `500x500+10+10` | Tile geometry |
| `--label` | off | Force filename labels on |
| `--fontsize N` | `12` | Label font size |
| `--prefix NAME` | `montage` | Output filename prefix |
| `--crop WxH` | — | Center-crop before tiling |

The CLI scans the **current working directory** for images. Images are sorted alphabetically and paged automatically. Output goes to the current directory. A `process.log` is written to the same location.

---

## Building a Standalone Executable

```bash
venv_win\Scripts\pip install "nicegui[pyinstaller]"
nicegui-pack --onefile --name Montage_Maker app.py
```

The resulting `Montage_Maker.exe` (Windows) requires no Python installation but still needs ImageMagick on PATH.

---

## Troubleshooting

**`montage: command not found`**
ImageMagick is not on your PATH. Reinstall with "Add to PATH" checked, then open a new terminal.

**Window fails to open (Windows)**
The native window requires the Microsoft Edge WebView2 runtime. It is pre-installed on Windows 10/11; if missing, download it from [developer.microsoft.com/microsoft-edge/webview2](https://developer.microsoft.com/microsoft-edge/webview2/).

**"Connection lost" toast during generation**
This should not occur in the current version (generation runs in a background thread). If it reappears, it indicates a very long ImageMagick operation blocking the event loop.

**Port conflict on startup**
Click **PORT: 8000** in the app header, enter a free port, save, and restart the app.
