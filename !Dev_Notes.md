# Dev Notes — Montage Maker

## Architecture Overview

| File | Purpose |
|---|---|
| `montage_maker.py` | Core engine + standalone CLI |
| `app.py` | NiceGUI GUI frontend — imports from `montage_maker.py` |
| `config.ini` | Named presets (managed via GUI or hand-edited) |
| `session.ini` | Per-machine state (paths, port, theme) — gitignored, auto-created |
| `setup.py` | Bootstrap — installs ImageMagick, creates venv |
| `requirements.txt` | `nicegui`, `pywebview` |
| `build.py` | Cross-platform PyInstaller build script |
| `Montage_Maker_User_Guide.md` | End-user guide (Artistly community) |

---

## Key Decisions & Why

**Folder browser uses `tkinter.filedialog`**
`app.native.main_window.create_file_dialog()` (pywebview) is silent in the NiceGUI 3.x + pywebview 6.x combination — the coroutine never resolves. `tkinter.filedialog` is stdlib and works reliably on Windows from NiceGUI event handlers.

**No Ghostscript dependency**
`get_all_images()` only accepts raster formats. Ghostscript is only relevant for PDF/EPS in ImageMagick — not needed here, and it caused confusing winget failures during setup.

**`session.ini` is separate from `config.ini`**
If paths/port/theme were stored in `config.ini`, `_preset_names()` would pick up those sections as presets.

**Auto-increment doesn't write back to the prefix field**
The `_v2` suffix is used only for the current run. Writing it back caused compounding on repeated runs (`_v2_v2_v2`).

**ConfigParser DEFAULT inheritance is explicitly filtered**
`_preset_values()` excludes keys in `config.defaults()` to prevent values from one preset bleeding into another when read via SectionProxy.

**`apply_preset` uses `.get(key, default)` for ALL fields**
Using `if key in pc: set_value(...)` left stale values from prior presets (e.g., crop from Instagram Post persisting when switching to a cropless preset).

**Output images served via `/output-image` FastAPI endpoint, not direct paths**
NiceGUI derives deterministic URLs from local file paths. On overwrite, the file changes but the URL stays the same — WebView2 serves the cached old image. The endpoint adds `Cache-Control: no-cache` and accepts a `?t={timestamp}` cache-buster param that changes every run. Do not revert to `ui.image(path)` for output previews.

**Shadow is skipped when Polaroid is active (engine + UI)**
`-shadow` and `+polaroid` conflict in ImageMagick montage: shadow flattens the layer before the polaroid rotation is composited, zeroing out the angle. `+polaroid` already bakes in its own shadow. Fix: engine skips `-shadow` when `polaroid` is set; UI disables the shadow switch via `bind_enabled_from(polaroid_sw, 'value', backward=lambda v: not v)`.

**Theme stored in `session.ini` `[ui]` section**
Four themes (Light, Warm, Dark, Midnight) are defined in the `THEMES` dict in `app.py`. Theme is applied at page load via `ui.dark_mode()` and `ui.colors()`. Changing the dropdown calls `apply_theme()` which updates both live.

**Per-section comments in `config.ini` are lost on first GUI save**
`configparser` cannot round-trip comments. The top-of-file header is preserved via `_CONFIG_HEADER` prepended before `config.write()`.

**Title rendering is two-pass, not via `montage -title`**
ImageMagick's `montage` does not honour `-pointsize`/`-fill` set before `-title` in IM7. Pass 1 runs `montage` without a title (correct label size/color at the end of the command). Pass 2 runs `magick output -splice 0xH -annotate title output` with its own size and fill. This gives fully independent title vs. label styling.

**Use `magick`, not `convert`, for non-montage IM calls on Windows**
`convert.exe` in `C:\Windows\System32` (the NTFS filesystem converter) shadows ImageMagick's `convert.exe` on some Windows IM7 installs. `magick` has no system conflict and works on both IM6 and IM7.

**`nicegui-pack` is broken on Windows — use `build.py`**
`nicegui-pack` spawns `pyinstaller` as a bare subprocess, which can't find the venv's `pyinstaller.exe` because the subprocess doesn't inherit the activated venv PATH. `build.py` calls `venv_win\Scripts\pyinstaller` directly with the full path.

**`SCRIPT_DIR` uses `sys.executable` in frozen builds**
In a PyInstaller onefile bundle, `__file__` resolves to the temp extraction directory, not the exe's location. `config.ini` and `session.ini` must resolve relative to `sys.executable` in frozen mode.

**Font dropdown uses `ui.select` with `with_input=True`**
The font list is populated from `magick -list font` at module load. `ui.select` with `with_input=True` and `new_value_mode='add-unique'` gives a filterable dropdown that still accepts custom font names. Falls back to an empty list if IM is not on PATH (fields still usable as free-text).

**Image selection uses `make_handler(name)` factory to close over loop variable**
A plain `lambda e: _image_selection[fname] = e.value` inside a for-loop would capture `fname` by reference (Python closure), so all handlers would reference the last iteration's value. The factory `make_handler(name)` binds `name` at call time.

**`_open_folder` on Windows needs threading + `keybd_event` trick**
pywebview owns the foreground window, not the Python process. `AllowSetForegroundWindow` therefore does nothing (Windows only grants this if the caller owns the foreground). The fix: run `os.startfile` in a daemon thread, wait 0.5 s for Explorer, enumerate `CabinetWClass` windows, simulate a key event (makes this process the "last input receiver"), then call `SetForegroundWindow`.

---

## `create_montages()` Signature

```python
create_montages(
    grid_size,               # '2x3' format
    output_extension,        # 'png', 'jpg', etc.
    tile_geometry,           # '500x500+10+10' (WxH+Hborder+Vborder)
    show_labels,             # bool
    prefix,                  # output filename prefix
    crop_dims,               # '1080x1080' or None
    font_size,               # string, e.g. '12' — label point size
    output_dir=None,         # absolute path; defaults to CWD if None
    background_color='white',# any ImageMagick color (hex, named, 'none')
    quality=None,            # JPEG quality 0–100
    title='',                # text banner (rendered in pass 2 via magick)
    font_name='',            # ImageMagick font name (applies to all text)
    shadow=None,             # truthy = add -shadow (skipped if polaroid set)
    frame=None,              # '6x6+3+3' geometry string or None
    mattecolor=None,         # frame matte color
    border=None,             # '5x5' geometry string or None
    bordercolor=None,        # border color
    mode=None,               # 'Frame', 'Concatenate', or None
    polaroid=None,           # 'random', angle int as string, or None
    image_files=None,        # pre-filtered list of filenames; None = scan CWD
    text_color=None,         # -fill color for all text; None = IM default (black)
    title_size=None,         # point size for title banner; None = uses font_size
)
```

The CLI (`__main__` block) does not expose `output_dir`, `background_color`, `image_files`, `text_color`, `title_size`, or any of the effect params — those are GUI-only.

**Two-pass rendering:** pass 1 runs `montage` (tile layout + labels). If `title` is set, pass 2 runs `magick <output_file> -splice 0x{title_h} -annotate +0+{pad} title <output_file>` to add the title banner independently. This is required because `-pointsize`/`-fill` set before `-title` in `montage` are not reliably honoured.

---

## Preset Config Keys

| Key | Example | Notes |
|---|---|---|
| `grid` | `2x3` | cols × rows |
| `size` | `500x500+10+10` | WxH+Hspacing+Vspacing |
| `background` | `#ffffff` | Any ImageMagick color |
| `transparent` | `on`/`off` | Forces background to `none`; PNG required |
| `prefix` | `montage` | Output filename prefix |
| `fontsize` | `12` | Label point size |
| `ext` | `png` | Output format |
| `labels` | `on`/`off` | Show filename labels |
| `crop` | `1080x1080` | Optional center-crop |
| `title` | `My Set` | Text banner above montage |
| `font` | `Arial` | ImageMagick font name |
| `quality` | `85` | JPEG quality (0–100) |
| `mode` | `Concatenate` | `Frame` or `Concatenate` |
| `shadow` | `on` | Drop shadow (ignored when polaroid is set) |
| `frame` | `6x6+3+3` | Beveled frame geometry |
| `mattecolor` | `#c8b89a` | Frame matte color |
| `border` | `5x5` | Flat border geometry |
| `bordercolor` | `#000000` | Border color |
| `polaroid` | `random` | `random` or fixed angle integer |
| `textcolor` | `#ffffff` | Text fill color; empty string = IM default (black) |
| `titlesize` | `24` | Title point size (independent of `fontsize`) |

Presets are sorted alphabetically (casefold) on every write.

---

## Bundled Presets (11)

Contact Sheet, Filmstrip, Gallery Wall, Instagram Post, Instagram Story, Link Preview, Pinterest Pin, Polaroid, Square 3×3, X Post, YouTube Thumb

---

## Known Gaps / Deferred Work

- [ ] CLI doesn't expose `output_dir`, `background_color`, `text_color`, `title_size`, `image_files`, or any effect params
- [ ] No progress bar during generation (can be slow for large batches)
- [ ] No drag-and-drop folder support
- [ ] `process.log` writes to the input folder (CWD at generation time), not the output folder
- [ ] `_ensure_default_config()` is one-shot — preset changes in `_DEFAULT_PRESETS` don't propagate to existing `config.ini`; user must update via Manage… or delete config.ini
