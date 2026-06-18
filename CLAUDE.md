# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
                bordercolor=None, mode=None, polaroid=None)
```

**Shadow + Polaroid conflict:** when `polaroid` is set, `shadow` is silently ignored by the engine (`-shadow` and `+polaroid` conflict — shadow flattens the layer before polaroid rotation is composited). The UI disables the shadow switch when polaroid is active.

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
- `_open_folder(path)` — opens folder in OS file explorer (`os.startfile` / `open`)

**`index()` page function (single `@ui.page('/')`):**
- 3-column layout: left (40%) = folders + Generate button + image results; middle (flex) = preset selector + settings card (grid, tile, background, output); right (flex) = filename prefix, text, effects
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
