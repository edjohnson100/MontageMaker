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
    font_size,               # string, e.g. '12'
    output_dir=None,         # absolute path; defaults to CWD if None
    background_color='white',# any ImageMagick color (hex, named, 'none')
    quality=None,            # JPEG quality 0–100
    title='',                # text banner above montage
    font_name='',            # ImageMagick font name
    shadow=None,             # truthy = add -shadow (skipped if polaroid set)
    frame=None,              # '6x6+3+3' geometry string or None
    mattecolor=None,         # frame matte color
    border=None,             # '5x5' geometry string or None
    bordercolor=None,        # border color
    mode=None,               # 'Frame', 'Concatenate', or None
    polaroid=None,           # 'random', angle int as string, or None
)
```

The CLI (`__main__` block) does not expose `output_dir`, `background_color`, or any of the effect params — those are GUI-only.

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

Presets are sorted alphabetically (casefold) on every write.

---

## Bundled Presets (11)

Contact Sheet, Filmstrip, Gallery Wall, Instagram Post, Instagram Story, Link Preview, Pinterest Pin, Polaroid, Square 3×3, X Post, YouTube Thumb

---

## Known Gaps / Deferred Work

- [ ] CLI doesn't expose `output_dir`, `background_color`, or any effect params
- [ ] No progress bar during generation (can be slow for large batches)
- [ ] PyInstaller build (`nicegui-pack --onefile --name Montage_Maker app.py`) not yet tested end-to-end
- [ ] No drag-and-drop folder support
- [ ] `process.log` writes to the input folder (CWD at generation time), not the output folder
