# Montage Maker

**Turn Image Sets Into Showpieces**

Montage Maker is a desktop GUI and CLI tool for turning folders of images into polished grids, contact sheets, social-ready posts, documentation images, reference sheets, and artful montages. Point it at a folder of images, choose a preset or customize the layout, and generate one or more finished image files.

It is useful for AI image batches, design variations, project photos, product mockups, 3D printing documentation, tutorial assets, and any visual collection that deserves to look organized instead of scattered.

![Montage Maker](resources/MontageMakerIcon.png)

---

## Quick Start

For most users, the standalone app is the easiest way to run Montage Maker. You do **not** need to install Python when using the standalone executable.

1. Install **ImageMagick** and make sure the `montage` command is available on your PATH.
2. Launch Montage Maker:
   - **Windows:** double-click `Montage_Maker.exe`
   - **macOS:** double-click `Montage_Maker`
   - **Python/source version:** run `app.py` from the virtual environment
3. Choose an **Image folder**.
4. Choose an **Output folder**, or leave it blank and Montage Maker will create/use a `Montages` folder inside your image folder.
5. Pick a preset, such as **Square 3×3**, or adjust the settings manually.
6. Click **Generate Montage**.

Your montage file(s) appear in the output folder, with a preview shown inside the app.

---

## Full User Guide

For the friendly walkthrough with screenshots, examples, presets, and troubleshooting, see:

[Montage Maker User Guide](Montage_Maker_User_Guide.pdf)

---

## Requirements

Montage Maker uses **ImageMagick** under the hood to build the final montage images. Whether you use the standalone app or run from Python source, ImageMagick must be installed separately and available on your system PATH.

### Windows 10 / 11

1. Download the latest installer from [imagemagick.org/script/download.php](https://imagemagick.org/script/download.php#windows).
2. Choose the **64-bit DLL** build.
3. Run the installer.
4. Check **Add application directory to your system path**.
5. Open a new terminal and verify the install:

```bash
montage -version
```

### macOS

```bash
brew install imagemagick
montage -version
```

### Linux (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install imagemagick
montage -version
```

If `montage -version` does not return a version number, restart your terminal and check your PATH.

---

## Recommended: Use the Standalone App

Download the latest release from the **Releases** section in the GitHub sidebar (right side of the repository page).

### Windows

1. Install ImageMagick using the instructions above.
2. Put `Montage_Maker.exe` somewhere convenient, such as a project folder or local tools folder.
3. Double-click `Montage_Maker.exe`.
4. If Windows asks for permission to run the app, approve it if you trust the source.

### macOS

1. Install ImageMagick using the instructions above.
2. Put `Montage_Maker` somewhere convenient, such as your Applications folder or a project folder.
3. Double-click `Montage_Maker`.
4. If macOS blocks the app because it came from outside the App Store, use the normal macOS security workflow to allow it.

> The standalone app includes the Python application code, but it does not include ImageMagick. ImageMagick still has to be installed separately.

---

## Optional: Run from Python Source

Use this route if you want to run the source code directly, customize the app, or contribute changes.

Run the bootstrap script once with your **system Python**. Do not run it from inside an existing virtual environment.

```bash
# Windows
python setup.py

# macOS / Linux
python3 setup.py
```

The script creates a platform-specific virtual environment:

- Windows: `venv_win/`
- macOS/Linux: `venv_mac/`

It then installs the Python dependencies needed by the GUI.

Launch the app with:

```bash
# Windows
venv_win\Scripts\python app.py

# macOS / Linux
venv_mac/bin/python app.py
```

A native desktop window opens. No browser is required.

---

## Optional: Build Your Own Standalone Executable

Most users do not need this. Use this only if you want to package your own standalone copy of Montage Maker.

Run `setup.py` first so the virtual environment exists, then run:

```bash
# Windows
venv_win\Scripts\python build.py

# macOS
venv_mac/bin/python build.py
```

`build.py` installs PyInstaller into the virtual environment if needed, locates the NiceGUI package, and runs PyInstaller with the correct flags.

The finished executable will be created in `dist/`:

- Windows: `dist/Montage_Maker.exe`
- macOS: `dist/Montage_Maker`

The executable does not require a separate Python installation, but it still requires ImageMagick on PATH.

> Note: Use `build.py` for packaging. Do not use `nicegui-pack` on Windows; it may fail because its subprocess cannot find `pyinstaller` in the virtual environment.

---

## GUI Overview

The app uses a three-column layout that scales with the window width:

| Column | Contents |
|---|---|
| Left (~40%) | Image folder, output folder, **Input Image Files** selection panel, Generate button, and output previews |
| Middle (~25%) | Preset selector, grid controls, tile size and spacing, background, output crop/format |
| Right (~35%) | Output filename prefix, text/title options, labels, and effects |

### Input Image Files Panel

The collapsible **Input Image Files** panel lists every supported image in the selected folder with a checkbox and thumbnail preview.

Use it to:

- include or exclude individual images
- select all images
- deselect all images
- confirm how many images are selected before generating

This is faster than moving files in and out of the folder when you want to test different image sets.

### Header Controls

The top-right header controls include:

| Control | What it does |
|---|---|
| **Theme** | Switches between Light, Warm, Dark, and Midnight themes. Your choice is saved automatically. |
| **Port: 8000** | Changes the local app port if another app is already using 8000. Takes effect after restarting Montage Maker. |

---

## Common Uses

Montage Maker works well for:

- AI image batch reviews
- design variation comparisons
- contact sheets
- 3D printing project documentation
- laser/CAD/tutorial images
- product mockup sheets
- social media posts
- Pinterest pins
- YouTube thumbnails
- link preview images
- gallery-style presentation pages

---

## Bundled Presets

Montage Maker includes these built-in presets:

| Preset | Grid | Notes |
|---|---|---|
| Contact Sheet | 4×4 | 300px tiles, labels on, cropped square |
| Filmstrip | 4×1 | Concatenated tiles, black background, filmstrip-style borders |
| Gallery Wall | 2×2 | Framed tiles, drop shadow, warm background |
| Instagram Post | 2×2 | Cropped to 1080×1080, JPG |
| Instagram Story | 1×1 | Cropped to 1080×1920, JPG |
| Link Preview | 2×2 | Cropped to 1200×630, JPG |
| Pinterest Pin | 2×3 | Cropped to 1000×1500, JPG |
| Polaroid | 3×2 | Polaroid effect, random angle, dark background |
| Square 3×3 | 3×3 | 720px tiles, PNG |
| X Post | 2×2 | Cropped to 1200×675, JPG |
| YouTube Thumb | 2×2 | Cropped to 1280×720, PNG |

You can also save your own presets from the **Preset Manager**.

---

## Key Settings

| Setting | What it controls |
|---|---|
| Grid | Columns and rows per output page |
| Tile size & spacing | Pixel size of each tile and the gap between tiles |
| Background | Solid background color or transparent PNG output |
| Crop | Center-crops source images before tiling |
| Format | Output file type: PNG, JPG, BMP, or TIFF |
| Prefix | Base filename for generated output files |
| Title | Text banner above the montage |
| Labels | Optional source filename labels under each tile |
| Effects | Drop shadow, Polaroid, frame, border, and concatenate modes |

If the selected images exceed the grid capacity, Montage Maker automatically creates additional pages, such as `montage_01.png`, `montage_02.png`, and so on.

---

## File Conflict Handling

If output files with the selected prefix already exist, Montage Maker shows a dialog before writing anything.

| Option | Behavior |
|---|---|
| Cancel | Stops the run without writing files |
| Auto-increment | Creates a new version using `_v2`, `_v3`, etc. |
| Overwrite | Replaces the most recent matching version only |

Auto-increment is the safest option while experimenting.

---

## CLI Reference

The original command-line engine is still available in `montage_maker.py`.

```bash
python montage_maker.py [GRID] [OPTIONS]
```

| Argument | Default | Description |
|---|---|---|
| `GRID` | `2x2` | Grid layout, such as `3x4`. Optional if `--preset` is used. |
| `--preset NAME` | — | Load settings from a named `config.ini` section |
| `--ext EXT` | `png` | Output file format |
| `--size WxH+HB+VB` | `500x500+10+10` | Tile size plus horizontal/vertical spacing |
| `--label` | off | Show filename labels |
| `--fontsize N` | `12` | Label font size |
| `--prefix NAME` | `montage` | Output filename prefix |
| `--crop WxH` | — | Center-crop each source image before tiling |

Examples:

```bash
# Simple 2×2 grid with default settings
python montage_maker.py 2x2

# Use a saved preset
python montage_maker.py --preset "Instagram Post"

# Custom 2×2 with specific tile size, labels on, and larger font
python montage_maker.py 2x2 --size "500x500+5+5" --label --fontsize 24
```

The CLI scans the **current working directory** for images. Output goes to the current directory, and a `process.log` file is written alongside the output files.

---

## Troubleshooting

### `montage: command not found`

ImageMagick is not installed, or the `montage` command is not on your PATH. Reinstall ImageMagick with **Add application directory to your system path** checked, then open a new terminal and try again.

### The app window fails to open on Windows

The native window requires the Microsoft Edge WebView2 runtime. It is pre-installed on most Windows 10/11 systems. If it is missing, install it from Microsoft and try again.

### A port conflict appears on startup

Click **Port: 8000** in the app header, enter a free port number, save, and restart Montage Maker.

### “Connection lost” appears during generation

Generation runs in a background thread, so this should not normally appear. If it does, ImageMagick may be taking a long time with a large batch. Give it a moment and check the output folder when it finishes.

---

## Project Notes

Montage Maker is built with:

- [NiceGUI](https://nicegui.io/)
- [ImageMagick](https://imagemagick.org/)
- Python

ImageMagick does the heavy lifting. Montage Maker provides the friendly desktop interface, presets, image selection, output preview, conflict handling, and workflow glue.

---

## License

Montage Maker source code is licensed under the [MIT License](LICENSE) unless otherwise noted.

Documentation, original project artwork, logos, screenshots, promotional graphics, the Montage Maker name, and Lucy-related branding are not included in the MIT source code license. See [Asset and Branding License](ASSET_AND_BRANDING_LICENSE.md) for details.

Montage Maker uses or depends on third-party software and tools, including ImageMagick, NiceGUI, FastAPI, pywebview, PyInstaller, Python, and the Microsoft Edge WebView2 Runtime. Each third-party component remains under its own license or terms. See [Third-Party Notices](THIRD_PARTY_NOTICES.md) for details.

The standalone executable includes the Montage Maker application code and Python dependencies, but ImageMagick must be installed separately and available on your system PATH.

### **❤️ Support the Maker (and Lucy\!)**

I develop these tools to improve my own workflows and love sharing them with the community. If you find Montage Maker useful and want to say thanks, feel free to [**buy Lucy a dog treat on Ko-fi**](https://ko-fi.com/makingwithanedj)\!

---

*Happy Making\!* *— EdJ*
