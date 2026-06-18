# Next Chat Handoff — Montage Maker

## Current State

Fully functional NiceGUI desktop GUI (`app.py`) wrapping the `montage_maker.py` CLI engine. Runs as a native pywebview window (no browser needed). Three-column layout with themes, effects, and a curated preset set.

**Work completed across sessions:**
- Core NiceGUI GUI with 3-column layout (folders/generate/preview, settings, effects)
- Preset manager dialog (create/edit/delete presets in `config.ini`)
- Full effects support: drop shadow, frame, border, polaroid (with random angle)
- Theme system: Light, Warm, Dark, Midnight — saved in `session.ini [ui]`
- 11 bundled presets: Contact Sheet, Filmstrip, Gallery Wall, Instagram Post, Instagram Story, Link Preview, Pinterest Pin, Polaroid, Square 3×3, X Post, YouTube Thumb
- Overwrite vs auto-increment conflict dialog (overwrite targets most recent version only)
- Output image preview via FastAPI `/output-image` endpoint (cache-buster for overwrite)
- Shadow + Polaroid conflict fix: shadow disabled in UI and skipped in engine when polaroid active
- Persistent state via `session.ini`: input/output paths, server port, theme

---

## How to Run

```
# Development
venv_win\Scripts\python app.py

# Build standalone exe (Windows) — not yet tested end-to-end
venv_win\Scripts\pip install "nicegui[pyinstaller]"
nicegui-pack --onefile --name Montage_Maker app.py

# CLI (original, still works)
venv_win\Scripts\python montage_maker.py 2x2
venv_win\Scripts\python montage_maker.py --preset "Instagram Post"
```

**Kill the process if Ctrl+C doesn't respond:** `taskkill /F /IM python.exe` in a second terminal.

---

## Active Files

| File | Role |
|---|---|
| `app.py` | NiceGUI GUI — primary entry point |
| `montage_maker.py` | Core engine — `create_montages()`, `get_all_images()` |
| `config.ini` | 11 presets — read/written by `app.py`; sorted alphabetically |
| `session.ini` | Per-machine state (paths, port, theme) — gitignored, auto-created |
| `setup.py` | Bootstrap — installs ImageMagick, creates `venv_win`/`venv_mac` |
| `requirements.txt` | `nicegui`, `pywebview` |
| `Montage_Maker_User_Guide.md` | End-user guide (Artistly community) |

---

## Key Functions in `app.py`

| Function / Symbol | Purpose |
|---|---|
| `THEMES` | Dict of 4 theme definitions (dark flag + primary/secondary/accent colors) |
| `_load_theme()` / `_save_theme()` | Read/write theme from `session.ini [ui]` |
| `_serve_output_image` | FastAPI `GET /output-image` — serves local file with no-cache headers; `?t=` is cache-buster |
| `_preset_names()` | Returns sorted preset names from `config.ini` |
| `_preset_values(name)` | Returns preset dict, filtering out ConfigParser DEFAULT keys |
| `_write_config(config)` | Writes `config.ini` with sections sorted alphabetically |
| `_save_preset(name, values)` | Creates/updates a preset section |
| `_delete_preset(name)` | Removes a preset section |
| `_load_session()` / `_save_session()` | Reads/writes `session.ini` folder paths |
| `_load_port()` / `_save_port()` | Reads/writes `session.ini` server port |
| `_parse_grid(s)` / `_assemble_grid(c, r)` | Convert `'2x3'` ↔ `(2, 3)` |
| `_parse_size(s)` / `_assemble_size(w,h,hb,vb)` | Convert `'500x500+10+10'` ↔ 4 ints |
| `_next_prefix(out, prefix, ext)` | Finds next `_v2`, `_v3`… variant for auto-increment |
| `_latest_prefix(out, prefix, ext)` | Finds highest existing version (overwrite target) |
| `_open_folder(path)` | Opens folder in OS file explorer |

---

## Known Issues / Next Steps

See `!Dev_Notes.md` for the full list. Top items:
- PyInstaller build not yet tested end-to-end
- No progress indicator during generation
- CLI doesn't expose `output_dir`, `background_color`, or effect params
- `process.log` writes to the input folder (CWD at generate time), not output folder

---

## Gotchas for Next Session

- **Folder browser**: Uses `tkinter.filedialog`, NOT `app.native.main_window` (pywebview dialog is broken in this NiceGUI/pywebview version combo)
- **Preset apply**: Always uses `.get(key, default)` for ALL fields — don't revert to `if key in pc` pattern (causes stale values from previous preset to persist)
- **Auto-increment**: Never write the incremented prefix back to `prefix_in` — causes compounding on repeat runs
- **ConfigParser**: `dict(config[section])` includes DEFAULT section keys — always filter with `inherited = set(config.defaults())`
- **Output image display**: Always use `/output-image?p={quote(path)}&t={timestamp}` — never `ui.image(path)` directly. NiceGUI's deterministic URL for the same file path causes WebView2 to serve the cached old image on overwrite.
- **Shadow + Polaroid**: Never pass `-shadow` when `polaroid` is set (they conflict at the ImageMagick level). Shadow switch should be bound disabled from polaroid switch in any new UI that adds both controls.
