# Changelog

All notable changes to Montage Maker are documented here.

---

## v1.0.0 — 2026-06-21 — First public release

### Added
- NiceGUI desktop GUI with three-column layout (folders/generate/preview, settings, effects)
- 11 bundled presets: Contact Sheet, Filmstrip, Gallery Wall, Instagram Post, Instagram Story, Link Preview, Pinterest Pin, Polaroid, Square 3×3, X Post, YouTube Thumb
- Image selection panel — collapsible, with 40×40 thumbnails, checkboxes, All/None, live count
- Searchable font browser populated from `magick -list font`
- Effects: drop shadow, beveled frame (with matte color), flat border, polaroid (random or fixed angle)
- Independent title size and label size via two-pass rendering (`montage` + `magick`)
- Text color picker for title and label fill
- Four UI themes: Light, Warm, Dark, Midnight — persisted across sessions
- Preset manager dialog — create, edit, and delete named presets
- Output conflict dialog — overwrite most recent version or auto-increment (`_v2`, `_v3` …)
- Output image preview served via `/output-image` endpoint (prevents stale cache on overwrite)
- Persistent session state in `session.ini`: last-used input/output folders, server port, theme
- `build.py` — cross-platform PyInstaller build script for standalone macOS and Windows executables
- `setup.py` — bootstrap script that creates a venv and checks for ImageMagick
- `examples/` — example output images for all 11 presets
- `Montage_Maker_User_Guide.pdf` — end-user documentation with preset gallery

### Changed
- Gallery Wall redesigned from 2×2 to 3×1 portrait triptych (larger frame, shadow, linen background)
- Link Preview redesigned from 2×2 to 3×1 horizontal strip with drop shadow
- X Post redesigned from 2×2 to 3×1 cinematic strip (dark background, border, 16:9 crop)
- Instagram Post: drop shadow added
- Filmstrip: film-proportioned borders (12×30), title, Arial font, white text

### Fixed
- macOS folder picker: replaced `tkinter.filedialog` with `osascript` to prevent a rogue Dock entry and a deadlock on second use
- Shadow + Polaroid conflict: `-shadow` is skipped in the engine and disabled in the UI when polaroid is active (the two conflict in ImageMagick)
- Windows `convert.exe` conflict: all non-`montage` ImageMagick calls use `magick` instead of `convert` (Windows System32 shadows the IM binary)
- Windows Open Folder: Explorer now raises to foreground via a daemon thread + `keybd_event` trick (pywebview holds the foreground lock)
- Frozen executable paths: `SCRIPT_DIR` resolves relative to `sys.executable` in PyInstaller onefile builds, not `__file__`
