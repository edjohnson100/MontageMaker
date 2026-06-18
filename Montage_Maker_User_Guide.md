# Montage Maker — User Guide

> **A friendly guide for the Artistly community**

---

## Table of Contents

- [What Is Montage Maker?](#what-is-montage-maker)
- [Quick Start (TL;DR)](#quick-start-tldr)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [The Interface at a Glance](#the-interface-at-a-glance)
- [Settings Walkthrough](#settings-walkthrough)
  - [Grid](#grid)
  - [Tile Size & Spacing](#tile-size--spacing)
  - [Background](#background)
  - [Output](#output)
  - [Output Filename Prefix](#output-filename-prefix)
  - [Text (Titles & Labels)](#text-titles--labels)
  - [Effects](#effects)
- [Presets — Your Best Friends](#presets--your-best-friends)
- [The Preset Manager](#the-preset-manager)
- [File Conflict Dialog](#file-conflict-dialog)
- [Using the CLI](#using-the-cli)
- [Troubleshooting](#troubleshooting)

---

## What Is Montage Maker?

Montage Maker takes a folder full of images and arranges them into a tidy grid — a **montage** — and saves the result as a single image file. You pick the grid size, tile dimensions, spacing, and a handful of effects; it does the heavy lifting using ImageMagick under the hood.

It's great for:

- Creating contact sheets of your Artistly image sets
- Building social-ready posts (Instagram, Pinterest, Twitter/X, and more)
- Generating documentation images for 3D printing projects
- Making quick overview sheets of any image collection

> **[SCREENSHOT: The Montage Maker main window — use 2026-06-17_16-07-41.png]**

---

## Quick Start (TL;DR)

If you want to just jump in, here's the five-second version:

1. Launch the app (`venv_win\Scripts\python app.py` on Windows).
2. In the **Left column**, click the folder icon next to **Image Folder** and pick your image folder.
3. Set your **Output Folder** the same way.
4. In the **Middle column**, pick a **Preset** from the dropdown (try *Square 3×3* to start).
5. Hit **Generate Montage**.
6. Your montage(s) appear in the output folder, and a preview with a "X montage(s) created" count shows up right below the button.

That's it. Everything else in this guide is about fine-tuning.

---

## Installation

### What you need first: ImageMagick

Montage Maker uses **ImageMagick** to do its thing. You'll need it installed before the app will work.

**Windows 10 / 11**
1. Download the installer from [imagemagick.org](https://imagemagick.org/script/download.php#windows) — grab the 64-bit DLL build.
2. Run the installer. **Check "Add application directory to your system path"** — this step matters!
3. Open a new terminal and type `montage -version`. You should see a version number.

**macOS**
```bash
brew install imagemagick
```

**Linux (Ubuntu / Debian)**
```bash
sudo apt update && sudo apt install imagemagick
```

### Setting up Montage Maker

Run the bootstrap script once with your system Python — this creates a virtual environment and installs all Python dependencies automatically.

```bash
# Windows
python setup.py

# macOS / Linux
python3 setup.py
```

You only need to do this once.

---

## Running the App

### GUI (the friendly way)

```bash
# Windows
venv_win\Scripts\python app.py

# macOS / Linux
venv_mac/bin/python app.py
```

A native desktop window opens — no browser required.

### CLI (for the command-line fans)

The original command-line engine is still fully functional if you prefer that workflow. See [Using the CLI](#using-the-cli) at the end of this guide.

---

## The Interface at a Glance

The app uses a three-column layout:

| Column | What's in it |
|---|---|
| **Left (40%)** | Image folder, Output folder, **Generate Montage** button, and output previews with a count of montages created |
| **Middle (30%)** | Preset selector, Grid, Tile size & spacing, Background, Output format |
| **Right (30%)** | Output filename prefix, Text (title, font, labels), Effects |

> **[SCREENSHOT: Annotated version of 2026-06-17_16-07-41.png with callouts for each column]**

**The header** has two controls in the top-right corner:

| Control | What it does |
|---|---|
| **Theme** dropdown | Switch between four themes: **Light** and **Warm** (light modes) or **Dark** and **Midnight** (dark modes). Your choice is saved automatically and restored on next launch. |
| **Port: 8000** button | Change the server port if another app is using 8000. Takes effect after restarting the app. |

---

## Settings Walkthrough

### Grid

Controls how many tiles appear on each page.

| Field | What it does |
|---|---|
| **Columns** | Number of tiles per row |
| **Rows** | Number of rows per page |

If your image folder has more images than fit on one page, Montage Maker automatically creates additional pages — `prefix_01.png`, `prefix_02.png`, and so on.

> **Example:** A 3×3 grid with 12 images produces two pages — the first with 9 images, the second with 3.

> **[EXAMPLE OUTPUT: 3×3 grid of puppy images — 9 per page]**

---

### Tile Size & Spacing

Controls how big each individual tile is and how much breathing room sits between them.

| Field | Format | What it does |
|---|---|---|
| **Width / Height** | pixels | The dimensions of each tile |
| **H spacing / V spacing** | pixels | The gap between tiles (horizontal and vertical) |

> **Tip:** Larger spacing gives your montage an airy, editorial feel. Setting both H and V spacing to `0` (as shown in the Square 3×3 preset) makes tiles sit flush against each other — clean and compact. The **Concatenate** mode under Effects does the same thing automatically.

> **[EXAMPLE OUTPUT: Same 3×3 grid — left with 10px spacing, right with 0px spacing / Concatenate]**

---

### Background

| Field | What it does |
|---|---|
| **Color** | The fill color that shows between and behind tiles. Accepts hex values (`#ffffff`) or named colors (`black`, `white`, `gray`, etc.) |
| **Transparent** | Removes the background entirely. Output format is automatically forced to PNG when this is on, since JPG doesn't support transparency. |

> **[EXAMPLE OUTPUT: White background vs. black background vs. transparent (checkerboard)]**

---

### Output

| Field | What it does |
|---|---|
| **Crop** | Center-crops each source image to the specified size before tiling (e.g. `1080x1080`). Great for making sure all tiles are the same proportions. |
| **Format** | The file format for output files: `png`, `jpg`, `bmp`, or `tiff`. |

> **Tip:** Use **Crop** when your source images have mixed aspect ratios and you want a clean, uniform grid. Without it, ImageMagick will try to fit each image into the tile space as-is, which can result in letterboxing.

---

### Output Filename Prefix

The base name for your generated files. Pages are numbered automatically.

> **Example:** A prefix of `puppies` with a 3×3 grid across two pages produces `puppies_01.png` and `puppies_02.png`.

---

### Text (Titles & Labels)

| Field | What it does |
|---|---|
| **Title** | A text banner printed above the entire montage |
| **Font name** | The ImageMagick font name used for all text (e.g. `Arial`, `Helvetica`) |
| **Show filename labels** | Adds the source filename below each tile — great for contact sheets and documentation. Note that labels show the full filename, so long AI-generated filenames will appear in full. |
| **Label font size** | Point size for the filename labels |

> **[EXAMPLE OUTPUT: Contact sheet with filename labels under each tile]**

> **Tip:** The **Contact Sheet** preset has labels on by default — it's a handy reference for what labeled output looks like.

---

### Effects

This is where things get fun.

| Control | What it does |
|---|---|
| **Mode** | `Frame` — adds a decorative 3D border around tiles. `Concatenate` — zero spacing, tiles touch edge-to-edge. |
| **Quality (JPG)** | JPEG compression quality, 0–100. Default is 85. Has no effect on PNG output. |
| **Drop shadow** | Adds a subtle shadow behind each tile. Automatically disabled while Polaroid is active — Polaroid already bakes in its own shadow. |
| **Polaroid** | Applies a Polaroid-style effect. Set a fixed angle, or enable **Random (±15°)** for a casually tossed look. |
| **Frame** | A beveled ornamental border around each tile. Controls: Width, Height, Outer bevel, Inner bevel, and **Matte color** for the frame color. Pairs naturally with Mode = Frame. |
| **Border** | A flat solid border around each tile. Controls: Width, Height, and **Border color**. |

> **[EXAMPLE OUTPUT: Drop shadow effect on a 2×2 grid]**

> **[EXAMPLE OUTPUT: Polaroid effect with Random angle enabled]**

> **[EXAMPLE OUTPUT: Frame effect with gray matte color]**

> **Tip:** Drop shadow and Polaroid look especially nice together for a "scattered photos" aesthetic.

---

## Presets — Your Best Friends

Presets are saved collections of all your settings. Instead of dialing in 15 different fields, you just pick a preset from the dropdown and you're ready to go. Montage Maker ships with eleven presets built in:

| Preset | Grid | Description |
|---|---|---|
| **Contact Sheet** | 4×4 | 300px tiles with filename labels, cropped square — classic proof sheet |
| **Filmstrip** | 4×1 | 480px tiles, Concatenate mode, black background — a seamless horizontal banner |
| **Gallery Wall** | 2×2 | 500px tiles, beveled frame, drop shadow, warm linen background — framed prints on a wall |
| **Instagram Post** | 2×2 | Cropped to 1080×1080, JPG — ready to upload |
| **Instagram Story** | 1×1 | Cropped to 1080×1920, JPG — full-screen story / TikTok format |
| **Link Preview** | 2×2 | Cropped to 1200×630, JPG — the universal OG image format for Discord, Slack, and social link shares |
| **Pinterest Pin** | 2×3 | Cropped to 1000×1500, JPG — tall Pinterest format |
| **Polaroid** | 3×2 | 450px tiles, Polaroid effect with random angles, dark background and drop shadow |
| **Square 3×3** | 3×3 | 720px tiles, PNG — a versatile general-purpose layout |
| **X Post** | 2×2 | Cropped to 1200×675, JPG — X / Bluesky ready |
| **YouTube Thumb** | 2×2 | Cropped to 1280×720 — YouTube thumbnail dimensions |

> **[EXAMPLE OUTPUT: Instagram Post 2×2 — cropped square tiles]**

> **[EXAMPLE OUTPUT: Contact Sheet 4×4 with filename labels]**

> **[EXAMPLE OUTPUT: Pinterest Pin 2×3 — tall format]**

> **[EXAMPLE OUTPUT: Square 3×3 — the puppy sample image you already have!]**

> **Tip:** The social media presets (Instagram, Pinterest, X Post, Link Preview, YouTube Thumb) all have crop values set to their platform's ideal dimensions. This means your output is genuinely ready to upload — no resizing needed.

---

## The Preset Manager

Click **Manage…** next to the Preset dropdown to open the Preset Manager.

From here you can:

- **Load** an existing preset into the form to review or edit it
- **Save** under any name you like (spaces and proper case are fine; the only characters that aren't allowed are `]` and newlines)
- **Delete** a preset you no longer need
- **Clear** the form to start fresh from scratch

Presets are stored in `config.ini` in the same folder as the script, and are sorted alphabetically in the dropdown.

> **[SCREENSHOT: Preset Manager dialog]**

> **Tip:** After dialing in a custom setup you like — say, your preferred tile size, a specific background color, and drop shadow on — save it as a preset with a memorable name. Future-you will be grateful.

---

## File Conflict Dialog

If files with your chosen prefix already exist in the output folder, a dialog pops up before anything is written. You have three choices:

| Option | What happens |
|---|---|
| **Cancel** | Nothing is written. You're back where you started. |
| **Auto-increment** | Appends `_v2`, `_v3`, etc. to create a new set alongside the existing files. |
| **Overwrite** | Replaces the **most recent version** only (e.g. if `_v3` files exist, only those are replaced — earlier versions are left alone). |

The dialog tells you exactly how many files are affected and which prefix Overwrite will target, so there are no surprises.

> **Tip:** Auto-increment is the safe default if you're experimenting. Overwrite is handy when you're iterating on a final result and don't want to accumulate numbered versions.

---

## Using the CLI

Prefer the command line? The original CLI engine is still fully functional and lives in `montage_maker.py`.

```bash
python montage_maker.py [GRID] [OPTIONS]
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `GRID` | `2x2` | Grid layout, e.g. `3x4`. Optional if `--preset` is used. |
| `--preset NAME` | — | Load all settings from a named `config.ini` section |
| `--ext EXT` | `png` | Output file format |
| `--size WxH+HB+VB` | `500x500+10+10` | Tile size + horizontal/vertical spacing |
| `--label` | off | Turn filename labels on |
| `--fontsize N` | `12` | Label font size in points |
| `--prefix NAME` | `montage` | Output filename prefix |
| `--crop WxH` | — | Center-crop each image before tiling |

### Examples

```bash
# Simple 2×2 grid with default settings
python montage_maker.py 2x2

# Use a saved preset
python montage_maker.py --preset "Instagram Post"

# Custom 2×2 with specific tile size, labels on, and larger font
python montage_maker.py 2x2 --size "500x500+5+5" --label --fontsize 24
```

> **Note:** The CLI scans the **current working directory** for images, so `cd` into your image folder (or the folder containing them) before running. Output goes to the current directory as well. A `process.log` is written alongside the output files.

---

## Troubleshooting

**`montage: command not found`**
ImageMagick isn't on your PATH. Reinstall it with "Add to PATH" checked during setup, then open a brand new terminal window.

**The app window fails to open (Windows)**
The native window needs the Microsoft Edge WebView2 runtime. It comes pre-installed on Windows 10 and 11, but if it's missing, grab it from [developer.microsoft.com/microsoft-edge/webview2](https://developer.microsoft.com/microsoft-edge/webview2/).

**"Connection lost" toast appears during generation**
This shouldn't happen in the current version (generation runs in a background thread). If it does appear, it means ImageMagick is taking an unusually long time with a large batch. Give it a moment — it should finish.

**Port conflict on startup**
Click **Port: 8000** in the app header, enter a different port number that's not in use, save, and restart the app.

---

*Montage Maker is built with [NiceGUI](https://nicegui.io/) and [ImageMagick](https://imagemagick.org/).*
