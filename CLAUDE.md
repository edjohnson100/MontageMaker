# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo Structure & Key Files

| File | Role |
|---|---|
| `app.py` | NiceGUI GUI — primary entry point |
| `montage_maker.py` | Core engine — `create_montages()` + CLI `__main__` |
| `build.py` | Cross-platform PyInstaller build script |
| `setup.py` | Bootstrap — creates venv, installs dependencies |
| `config.ini` | 11 bundled presets |
| `requirements.txt` | `nicegui`, `pywebview` |
| `README.md` | GitHub-facing readme (practical, standalone-first) |
| `Montage_Maker_User_Guide.md` | End-user guide (Markdown source — also exported as PDF for distribution) |
| `examples/` | Example output images referenced in the user guide (11 preset examples, not all populated yet) |
| `LICENSE` | MIT license (source code only) |
| `ASSET_AND_BRANDING_LICENSE.md` | Covers logo, Lucy artwork, docs, screenshots, branding |
| `THIRD_PARTY_NOTICES.md` | Third-party tool/library notices |
| `PYTHON_DEPENDENCY_LICENSES.md` | Generated pip-licenses report for Python deps |
| `resources/` | App icon + hero images |
| `Archive/` | **Gitignored, local only.** Old dev notes, scratchpads, draft docs. Not public content. |

**Dev notes and next-chat handoff files** (`!Dev_Notes.md`, `!Next_Chat.md`) were moved to `Archive/` and are no longer in the tracked repo. Use memory files and CLAUDE.md for session context instead.

## Running the App

**GUI (primary):**
```bash
venv_win\Scripts\python app.py          # Windows
venv_mac/bin/python app.py              # macOS
```

**CLI (original engine, still functional):**
```bash
python montage_maker.py 2x2
python montage_maker.py --preset "Instagram Post"
python montage_maker.py 2x2 --size "500x500+5+5" --label --fontsize 24
```

**Bootstrap (first-time setup):**
```bash
python setup.py     # creates venv_win or venv_mac, installs ImageMagick
```

**System requirement:** ImageMagick must be installed and `montage` must be on PATH.

## Architecture

Two entry points share one core engine:

- **`app.py`** — NiceGUI GUI. Imports `create_montages` and `str_to_bool` from `montage_maker.py`. Opens a native pywebview window (`ui.run(native=True)`). All UI logic lives here.
- **`montage_maker.py`** — Core engine. `create_montages()` is the main function; also has a `__main__` block for CLI use.

### `montage_maker.py` flow

1. `get_all_images()` — scans CWD for `.jpg/.jpeg/.png/.bmp/.gif/.tiff/.webp`, returns sorted list
2. `create_montages()` — batches images by grid size, builds and runs an ImageMagick `montage` subprocess per page, writes output to `output_dir` (or CWD if None)
3. Logging goes to both console and `process.log` (in CWD, overwritten each run)

`create_montages` signature:
```python
create_montages(grid_size, output_extension, tile_geometry, show_labels,
                prefix, crop_dims, font_size, output_dir=None,
                background_color='white', quality=None, title='', font_name='',
                shadow=None, frame=None, mattecolor=None, border=None,
                bordercolor=None, mode=None, polaroid=None, image_files=None,
                text_color=None, title_size=None)
```

**Shadow + Polaroid conflict:** when `polaroid` is set, `shadow` is silently ignored by the engine (`-shadow` and `+polaroid` conflict — shadow flattens the layer before polaroid rotation is composited). The UI disables the shadow switch when polaroid is active.

**Two-pass title rendering:** `create_montages` runs `montage` without `-title` (pass 1), then calls `magick` to splice a title banner and annotate it onto each output page (pass 2). This gives the title independent font size (`title_size`) and color (`text_color`) from the labels. Use `magick`, not `convert`, for the second pass — on Windows IM7, `convert.exe` is shadowed by the system binary.

**`image_files` parameter:** if provided, `get_all_images()` is skipped and the supplied list is used directly. The GUI passes the checked subset from the image-selection panel. CLI never passes this; behaviour is unchanged.

### `app.py` structure

**Module-level helpers:**
- `_preset_names()` / `_preset_values(name)` / `_save_preset()` / `_delete_preset()` / `_write_config()` — read/write `config.ini` via ConfigParser; always filter out DEFAULT-inherited keys
- `_load_session()` / `_save_session()` — read/write `session.ini` folder paths
- `_load_port()` / `_save_port()` — read/write `session.ini` server port
- `_load_theme()` / `_save_theme()` — read/write `session.ini` `[ui]` theme name
- `THEMES` dict — four theme definitions (`Light`, `Warm`, `Dark`, `Midnight`), each with `dark` bool + `primary`/`secondary`/`accent` color strings
- `_serve_output_image` — FastAPI `GET /output-image` route; serves a local file path (`?p=...`) with `Cache-Control: no-cache` headers. A `?t=` timestamp query param is used as a cache-buster (not read by the handler). Required because NiceGUI derives deterministic URLs from file paths — same filename on overwrite = WebView cache hit without this endpoint.
- `_parse_grid(s)` / `_assemble_grid(c, r)` — convert `'2x3'` ↔ `(cols, rows)`
- `_parse_size(s)` / `_assemble_size(w, h, hb, vb)` — convert `'500x500+10+10'` ↔ 4 integers
- `_next_prefix(out_dir, prefix, ext)` — finds next unused `_v2`, `_v3`… variant
- `_win32_open_raised(path)` / `_open_folder(path)` — opens folder in OS file explorer; Windows version runs in a daemon thread, uses `os.startfile` + `keybd_event` trick + `SetForegroundWindow` to bring Explorer to the foreground (pywebview holds the foreground lock, so `AllowSetForegroundWindow` alone is insufficient)
- `_ensure_default_config()` — writes default `config.ini` from `_DEFAULT_PRESETS` if the file doesn't exist (called at module level; enables standalone exe first-run)
- `_load_imagemagick_fonts()` — runs `magick -list font` (or `convert -list font`) and returns a sorted list of font names; stored in module-level `_FONTS`
- `refresh_image_list()` / `_update_count()` / `select_all()` / `select_none()` — image selection panel helpers inside `index()`

**`index()` page function (single `@ui.page('/')`):**
- 3-column layout: left (~40%) = folders + image-selection panel + Generate button + output previews; middle (~25%) = preset selector + settings card (grid, tile, background, output); right (~35%) = filename prefix, text, effects
- Column flex ratios: `1.6 1 0` / `1.1` / `1.4 1 0` (no hard `max-w` cap — columns scale with window width)
- Header row: app title left; right side has Theme dropdown + Port button
- Theme applied at page load via `ui.dark_mode()` and `ui.colors()`; `apply_theme()` updates both live when dropdown changes
- `apply_preset(e)` — always sets ALL fields via `.get(key, default)`; never uses `if key in pc` (prevents stale values when switching presets)
- `generate()` — async; checks for filename conflicts before running, shows overwrite/auto-increment dialog; displays output via `/output-image` endpoint (not direct file paths) to prevent WebView cache hits on overwrite
- `open_preset_manager()` — opens a dialog for create/edit/delete of presets; mirrors all main-page settings including effects
- `open_port_dialog()` — dialog to change server port; saves to `session.ini`

### Config files

**`config.ini`** — named presets. Preset keys:

| Key | Format | Notes |
|---|---|---|
| `grid` | `2x3` | cols × rows |
| `size` | `500x500+10+10` | WxH+Hspacing+Vspacing |
| `background` | `#ffffff` | ImageMagick color (hex or named) |
| `transparent` | `on`/`off` | Forces background to `none`; output must be PNG |
| `prefix` | `montage` | Output filename prefix |
| `fontsize` | `12` | Label point size |
| `ext` | `png` | Output format |
| `labels` | `on`/`off` | Show filename labels |
| `crop` | `1080x1080` | Optional — center-crop applied before tiling |
| `title` | string | Text banner above montage |
| `font` | string | ImageMagick font name |
| `quality` | `0`–`100` | JPEG quality (default 85) |
| `mode` | `Frame`/`Concatenate` | ImageMagick montage mode |
| `shadow` | `on`/`off` | Drop shadow (ignored when polaroid is set) |
| `frame` | `6x6+3+3` | Beveled frame geometry |
| `mattecolor` | `#808080` | Frame color |
| `border` | `5x5` | Flat border geometry |
| `bordercolor` | `#000000` | Border color |
| `polaroid` | `random` or angle int | Polaroid effect |
| `textcolor` | `#ffffff` | Text fill color (title + labels); empty = IM default (black) |
| `titlesize` | `24` | Title-specific font size; label size uses `fontsize` |

Sections are written alphabetically (casefold) on every GUI save.

**`session.ini`** — gitignored. Stores last-used state across sessions:

```ini
[paths]
input = ...
output = ...

[server]
port = 8000

[ui]
theme = Dark
```

### Known gotchas

- **Folder browser** uses `tkinter.filedialog`, not `app.native.main_window.create_file_dialog` (the pywebview dialog is silent in the NiceGUI 3.x + pywebview 6.x combination)
- **Auto-increment** (`_v2` suffix) is applied for the current run only — never written back to `prefix_in`, or it compounds on repeated runs
- **ConfigParser DEFAULT inheritance** — `dict(config[section])` includes DEFAULT keys; `_preset_values()` filters them via `inherited = set(config.defaults())`
- **Image preview on overwrite** — NiceGUI assigns deterministic URLs to local files; same filename = WebView cache hit. All output images are served through `GET /output-image?p=...&t={timestamp}` to force a fresh fetch. Do not revert to `ui.image(path)` for output previews.
- **Shadow + Polaroid** — `-shadow` and `+polaroid` conflict in ImageMagick montage; shadow is skipped in the engine when polaroid is active, and the UI disables the shadow switch via `bind_enabled_from`
- **Title rendering is two-pass** — `montage` does not honour `-pointsize`/`-fill` placed before `-title` reliably; instead, pass 1 runs `montage` without a title, pass 2 runs `magick` to splice and annotate the title independently. Never revert to putting `-title` in the `montage` command.
- **`magick` not `convert` for pass 2** — on Windows IM7, `convert.exe` in System32 shadows ImageMagick's `convert`. Use `magick` as the executable for all non-`montage` IM calls.
- **`SCRIPT_DIR` in frozen exe** — `Path(__file__).parent` resolves to the temp extraction dir in a PyInstaller onefile bundle. Use `Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent`. `config.ini` and `session.ini` must both use `SCRIPT_DIR`.
- **`nicegui-pack` broken on Windows** — the subprocess spawned by `nicegui-pack` can't find `pyinstaller` because the venv Scripts dir isn't on the subprocess PATH. Use `build.py` instead, which calls `venv_win\Scripts\pyinstaller` directly.
- **Font dropdown uses `ui.select` with `with_input=True`** — not `ui.input` with `autocomplete`. `_FONTS` is populated at module load from `magick -list font`. Font names must be passed verbatim to ImageMagick's `-font`; the select uses `new_value_mode='add-unique'` to allow arbitrary values.
- **Image selection checkbox loop closure** — the `make_handler(name)` factory inside `refresh_image_list()` is required; a plain `lambda e: ...` capturing `fname` in a loop would close over the last value.
