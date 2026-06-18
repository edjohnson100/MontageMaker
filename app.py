import asyncio
import os
import re
import subprocess
import sys
import configparser
import time
import urllib.parse
from pathlib import Path
from fastapi.responses import FileResponse
from nicegui import ui, app

from montage_maker import create_montages, str_to_bool

SCRIPT_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
SESSION_FILE = SCRIPT_DIR / 'session.ini'

_CONFIG_HEADER = """\
; Montage Maker Configuration File
; define presets below.
; You can override any of these by passing the argument on the command line.

"""

_DEFAULT_PRESETS = {
    'Contact Sheet':   {'grid': '4x4',  'size': '300x300+5+5',    'prefix': 'contact',      'fontsize': '10', 'ext': 'png', 'labels': 'on',  'crop': '300x300',    'textcolor': '', 'titlesize': '24', 'title': 'Contact Sheet'},
    'Filmstrip':       {'grid': '4x1',  'size': '480x480+0+0',    'background': '#000000',  'mode': 'Concatenate', 'prefix': 'filmstrip',  'fontsize': '12', 'ext': 'png', 'labels': 'off', 'textcolor': '#ffffff', 'titlesize': '24', 'title': 'Filmstrip', 'font': 'Arial', 'border': '12x30', 'bordercolor': '#000000'},
    'Gallery Wall':    {'grid': '2x2',  'size': '500x500+20+20',  'background': '#f0ebe0',  'prefix': 'gallery',   'fontsize': '12', 'ext': 'png', 'labels': 'off', 'shadow': 'on', 'frame': '8x8+4+4', 'mattecolor': '#c8b89a', 'textcolor': '', 'titlesize': '24'},
    'Instagram Post':  {'grid': '2x2',  'size': '1080x1080+0+0',  'prefix': 'ig_post',      'fontsize': '12', 'ext': 'jpg', 'labels': 'off', 'crop': '1080x1080',  'textcolor': '', 'titlesize': '24'},
    'Instagram Story': {'grid': '1x1',  'size': '1080x1920+0+0',  'prefix': 'ig_story',     'fontsize': '12', 'ext': 'jpg', 'labels': 'off', 'crop': '1080x1920',  'textcolor': '', 'titlesize': '24'},
    'Link Preview':    {'grid': '2x2',  'size': '600x315+5+5',    'prefix': 'link_preview', 'fontsize': '12', 'ext': 'jpg', 'labels': 'off', 'crop': '1200x630',   'textcolor': '', 'titlesize': '24'},
    'Pinterest Pin':   {'grid': '2x3',  'size': '500x750+10+10',  'prefix': 'pinterest',    'fontsize': '12', 'ext': 'jpg', 'labels': 'off', 'crop': '1000x1500',  'textcolor': '', 'titlesize': '24'},
    'Polaroid':        {'grid': '3x2',  'size': '450x450+30+30',  'background': '#1c1c1c',  'prefix': 'polaroid',  'fontsize': '12', 'ext': 'png', 'labels': 'off', 'polaroid': 'random', 'textcolor': '#ffffff', 'titlesize': '24'},
    'Square 3x3':      {'grid': '3x3',  'size': '720x720+0+0',    'prefix': 'square',       'fontsize': '12', 'ext': 'png', 'labels': 'off', 'textcolor': '', 'titlesize': '24'},
    'X Post':          {'grid': '2x2',  'size': '600x337+5+5',    'prefix': 'x_post',       'fontsize': '12', 'ext': 'jpg', 'labels': 'off', 'crop': '1200x675',   'textcolor': '', 'titlesize': '24'},
    'YouTube Thumb':   {'grid': '2x2',  'size': '640x360+0+0',    'prefix': 'yt_thumb',     'fontsize': '12', 'ext': 'png', 'labels': 'off', 'crop': '1280x720',   'textcolor': '', 'titlesize': '24'},
}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _preset_names():
    config = configparser.ConfigParser()
    cfg = SCRIPT_DIR / 'config.ini'
    if cfg.exists():
        config.read(cfg)
        return sorted(config.sections(), key=str.casefold)
    return []


def _preset_values(name):
    config = configparser.ConfigParser()
    cfg = SCRIPT_DIR / 'config.ini'
    if cfg.exists():
        config.read(cfg)
        if name in config:
            inherited = set(config.defaults())
            return {k: v for k, v in config[name].items() if k not in inherited}
    return {}


def _write_config(config):
    """Write config.ini with sections sorted alphabetically."""
    inherited = set(config.defaults())
    sorted_cfg = configparser.ConfigParser()
    for section in sorted(config.sections(), key=str.casefold):
        sorted_cfg[section] = {k: v for k, v in config[section].items() if k not in inherited}
    with open(SCRIPT_DIR / 'config.ini', 'w') as f:
        f.write(_CONFIG_HEADER)
        sorted_cfg.write(f)


def _ensure_default_config():
    if (SCRIPT_DIR / 'config.ini').exists():
        return
    config = configparser.ConfigParser()
    for section, values in _DEFAULT_PRESETS.items():
        config[section] = values
    _write_config(config)


def _save_preset(name, values):
    config = configparser.ConfigParser()
    cfg = SCRIPT_DIR / 'config.ini'
    if cfg.exists():
        config.read(cfg)
    config[name] = {k: v for k, v in values.items() if v}
    _write_config(config)


def _delete_preset(name):
    config = configparser.ConfigParser()
    cfg = SCRIPT_DIR / 'config.ini'
    if cfg.exists():
        config.read(cfg)
        if config.has_section(name):
            config.remove_section(name)
            _write_config(config)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _load_session():
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
        p = config.get('paths', 'input', fallback='')
        q = config.get('paths', 'output', fallback='')
        return p, q
    return '', ''


def _save_session(input_path, output_path):
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
    config['paths'] = {'input': input_path, 'output': output_path}
    with open(SESSION_FILE, 'w') as f:
        config.write(f)


def _load_port():
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
        return config.getint('server', 'port', fallback=8000)
    return 8000


def _save_port(port):
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
    if 'server' not in config:
        config['server'] = {}
    config['server']['port'] = str(port)
    with open(SESSION_FILE, 'w') as f:
        config.write(f)


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

THEMES = {
    'Light':    {'dark': False, 'primary': '#1976d2', 'secondary': '#26a69a', 'accent': '#9c27b0'},
    'Warm':     {'dark': False, 'primary': '#c07830', 'secondary': '#26a69a', 'accent': '#ff8f00'},
    'Dark':     {'dark': True,  'primary': '#42a5f5', 'secondary': '#26c6da', 'accent': '#ce93d8'},
    'Midnight': {'dark': True,  'primary': '#9c63f7', 'secondary': '#5c84fa', 'accent': '#f472b6'},
}


def _load_theme():
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
        return config.get('ui', 'theme', fallback='Light')
    return 'Light'


def _save_theme(name):
    config = configparser.ConfigParser()
    if SESSION_FILE.exists():
        config.read(SESSION_FILE)
    if 'ui' not in config:
        config['ui'] = {}
    config['ui']['theme'] = name
    with open(SESSION_FILE, 'w') as f:
        config.write(f)


_ensure_default_config()


def _load_imagemagick_fonts() -> list[str]:
    import re
    for cmd in (['magick', '-list', 'font'], ['convert', '-list', 'font']):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
            fonts = sorted({m.group(1) for m in re.finditer(r'^\s+Font:\s+(.+)$', out, re.MULTILINE)})
            if fonts:
                return fonts
        except Exception:
            continue
    return []

_FONTS = _load_imagemagick_fonts()


# ---------------------------------------------------------------------------
# Geometry parsing / assembly
# ---------------------------------------------------------------------------

def _parse_grid(s):
    """'2x3' → (2, 3)"""
    try:
        cols, rows = s.lower().split('x')
        return int(cols), int(rows)
    except Exception:
        return 2, 2


def _parse_size(s):
    """'500x500+10+10' → (500, 500, 10, 10)"""
    m = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', s.strip())
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return 500, 500, 10, 10


def _assemble_grid(cols, rows):
    return f"{int(cols or 2)}x{int(rows or 2)}"


def _assemble_size(w, h, hb, vb):
    return f"{int(w or 500)}x{int(h or 500)}+{int(hb or 0)}+{int(vb or 0)}"


def _parse_frame(s):
    """'6x6+3+3' → (6, 6, 3, 3)"""
    m = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', (s or '').strip())
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return 6, 6, 3, 3


def _assemble_frame(w, h, outer, inner):
    return f"{int(w or 6)}x{int(h or 6)}+{int(outer or 3)}+{int(inner or 3)}"


def _parse_border(s):
    """'5x5' → (5, 5)"""
    m = re.match(r'(\d+)x(\d+)', (s or '').strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 5, 5


def _assemble_border(w, h):
    return f"{int(w or 5)}x{int(h or 5)}"


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def _next_prefix(out_dir, prefix, ext):
    """Return the next available prefix variant (e.g. montage_v2, montage_v3)."""
    for i in range(2, 10000):
        candidate = f'{prefix}_v{i}'
        if not list(Path(out_dir).glob(f'{candidate}_*.{ext}')):
            return candidate
    return prefix


def _latest_prefix(out_dir, prefix, ext):
    """Return the highest existing version prefix (e.g. montage_v3 if that exists, else montage)."""
    latest = prefix
    for i in range(2, 10000):
        candidate = f'{prefix}_v{i}'
        if list(Path(out_dir).glob(f'{candidate}_*.{ext}')):
            latest = candidate
        else:
            break
    return latest


def _win32_open_raised(path):
    """Open path in Explorer then raise the window (runs in a background thread)."""
    import ctypes, time
    ole32  = ctypes.windll.ole32
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong, ctypes.c_long)

    ole32.CoInitialize(None)   # COM required for ShellExecute on non-main threads
    try:
        os.startfile(path)
        time.sleep(0.5)        # wait for Explorer window to appear

        hwnds = []
        @WNDENUMPROC
        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                if cls.value in ('CabinetWClass', 'ExploreWClass'):
                    hwnds.append(hwnd)
            return True
        user32.EnumWindows(cb, 0)

        if hwnds:
            hwnd = hwnds[-1]                    # last in Z-order = most recently opened
            user32.ShowWindow(hwnd, 9)           # SW_RESTORE (un-minimise if needed)
            # Synthesising a key event makes this process the last input receiver,
            # which is required by Windows before SetForegroundWindow will succeed.
            user32.keybd_event(0, 0, 0, 0)
            user32.keybd_event(0, 0, 2, 0)      # KEYEVENTF_KEYUP
            user32.SetForegroundWindow(hwnd)
    finally:
        ole32.CoUninitialize()


def _open_folder(path):
    if not path or not os.path.isdir(path):
        return
    if sys.platform == 'win32':
        import threading
        threading.Thread(target=_win32_open_raised, args=(path,), daemon=True).start()
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

@app.get('/output-image')
async def _serve_output_image(p: str, t: str = ''):
    """Serve a local output image with no-cache headers.
    The `t` param is a timestamp used only as a cache-buster; it is not read."""
    return FileResponse(p, headers={'Cache-Control': 'no-cache, no-store, must-revalidate'})


@ui.page('/')
def index():
    _saved_input, _saved_output = _load_session()
    _current_theme = _load_theme()
    _image_selection: dict[str, bool] = {}   # filename → checked

    dark = ui.dark_mode()
    _t = THEMES.get(_current_theme, THEMES['Light'])
    if _t['dark']:
        dark.enable()
    ui.colors(primary=_t['primary'], secondary=_t['secondary'], accent=_t['accent'])

    def apply_theme(name):
        t = THEMES.get(name, THEMES['Light'])
        dark.set_value(t['dark'])
        ui.colors(primary=t['primary'], secondary=t['secondary'], accent=t['accent'])
        _save_theme(name)

    def _update_count():
        total = len(_image_selection)
        selected = sum(1 for v in _image_selection.values() if v)
        _count_label.set_text(f'{selected} of {total} selected')

    def refresh_image_list():
        folder = folder_in.value.strip()
        if not os.path.isdir(folder):
            img_list_col.clear()
            _count_label.set_text('0 of 0 selected')
            return
        valid_ext = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        found = sorted(
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
            and os.path.splitext(f)[1].lower() in valid_ext
        )
        new_sel = {f: _image_selection.get(f, True) for f in found}
        _image_selection.clear()
        _image_selection.update(new_sel)
        img_list_col.clear()
        with img_list_col:
            for fname in found:
                def make_handler(name):
                    def on_change(e):
                        _image_selection[name] = e.value
                        _update_count()
                    return on_change
                src = f'/output-image?p={urllib.parse.quote(os.path.join(folder, fname))}'
                with ui.row().classes('w-full items-center gap-2 py-0.5'):
                    ui.checkbox('', value=_image_selection[fname],
                                on_change=make_handler(fname))
                    ui.image(src).style('width:40px; height:40px; object-fit:cover; border-radius:3px; flex-shrink:0')
                    ui.label(fname).classes('text-sm truncate')
        _update_count()

    def select_all():
        for k in _image_selection:
            _image_selection[k] = True
        refresh_image_list()

    def select_none():
        for k in _image_selection:
            _image_selection[k] = False
        refresh_image_list()

    def _pick_folder(title, starting_path):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        initial = starting_path if os.path.isdir(starting_path) else os.path.expanduser('~')
        result = filedialog.askdirectory(initialdir=initial, title=title)
        root.destroy()
        return result

    def browse_input():
        folder = _pick_folder('Select Image Folder', folder_in.value.strip())
        if folder:
            folder_in.set_value(folder)
            if not output_in.value.strip():
                output_in.set_value(str(Path(folder) / 'Montages'))
            _save_session(folder_in.value, output_in.value)
            refresh_image_list()

    def browse_output():
        start = output_in.value.strip() or folder_in.value.strip()
        folder = _pick_folder('Select Output Folder', start)
        if folder:
            output_in.set_value(folder)
            _save_session(folder_in.value, output_in.value)

    def refresh_main_presets():
        preset_sel.set_options(['(none)'] + _preset_names())

    def apply_preset(e):
        name = e.value
        if not name or name == '(none)':
            return
        pc = _preset_values(name)
        gc, gr = _parse_grid(pc.get('grid', '2x2'))
        tw, th, thb, tvb = _parse_size(pc.get('size', '500x500+10+10'))
        grid_cols_in.set_value(gc)
        grid_rows_in.set_value(gr)
        tile_w_in.set_value(tw)
        tile_h_in.set_value(th)
        tile_hb_in.set_value(thb)
        tile_vb_in.set_value(tvb)
        bg_color_in.set_value(pc.get('background', '#ffffff'))
        bg_transparent_sw.set_value(str_to_bool(pc.get('transparent', 'false')))
        title_in.set_value(pc.get('title', ''))
        font_in.set_value(pc.get('font', ''))
        text_color_in.set_value(pc.get('textcolor', '#000000'))
        title_size_in.set_value(int(pc.get('titlesize', '24')))
        quality_in.set_value(int(pc.get('quality', '85')))
        mode_sel.set_value(pc.get('mode', ''))
        prefix_in.set_value(pc.get('prefix', 'montage'))
        fontsize_in.set_value(int(pc.get('fontsize', '12')))
        crop_in.set_value(pc.get('crop', ''))
        ext_sel.set_value(pc.get('ext', 'png'))
        labels_sw.set_value(str_to_bool(pc.get('labels', 'false')))

        shadow_sw.set_value(str_to_bool(pc.get('shadow', 'false')))

        frame_val = pc.get('frame', '')
        frame_sw.set_value(bool(frame_val))
        if frame_val:
            f_w, f_h, f_out, f_in_ = _parse_frame(frame_val)
            frame_w_in.set_value(f_w)
            frame_h_in.set_value(f_h)
            frame_outer_in.set_value(f_out)
            frame_inner_in.set_value(f_in_)
        frame_matte_in.set_value(pc.get('mattecolor', '#808080'))

        border_val = pc.get('border', '')
        border_sw.set_value(bool(border_val))
        if border_val:
            b_w, b_h = _parse_border(border_val)
            border_w_in.set_value(b_w)
            border_h_in.set_value(b_h)
        border_color_in.set_value(pc.get('bordercolor', '#000000'))

        polaroid_val = pc.get('polaroid', '')
        polaroid_sw.set_value(bool(polaroid_val))
        if polaroid_val == 'random':
            polaroid_random_sw.set_value(True)
            polaroid_angle_in.set_value(0)
        elif polaroid_val:
            polaroid_random_sw.set_value(False)
            polaroid_angle_in.set_value(int(polaroid_val))
        else:
            polaroid_random_sw.set_value(False)

    async def _conflict_dialog(prefix, ext, count, overwrite_prefix):
        event = asyncio.Event()
        choice = {'value': None}

        def pick(v):
            choice['value'] = v
            dialog.close()
            event.set()

        with ui.dialog() as dialog, ui.card().style('min-width: 380px').classes('p-6 gap-3'):
            ui.label('Output files already exist').classes('text-lg font-bold')
            ui.label(
                f'{count} file(s) matching "{prefix}_*.{ext}" already exist in the output folder.'
            ).classes('text-sm text-gray-600')
            ui.label(
                f'Overwrite will replace: {overwrite_prefix}_*.{ext}'
            ).classes('text-sm text-gray-400')
            with ui.row().classes('gap-2 mt-2 justify-end'):
                ui.button('Cancel', on_click=lambda: pick(None)).props('flat')
                ui.button('Auto-increment', on_click=lambda: pick('increment')).props('unelevated color=primary')
                ui.button('Overwrite', on_click=lambda: pick('overwrite')).props('unelevated color=negative')

        dialog.open()
        await event.wait()
        return choice['value']

    async def generate():
        folder = folder_in.value.strip()
        if not os.path.isdir(folder):
            ui.notify('Input folder not found — please check the path', color='negative')
            return

        prefix = prefix_in.value.strip() or 'montage'
        ext = ext_sel.value or 'png'
        if bg_transparent_sw.value and ext != 'png':
            ext = 'png'
            ext_sel.set_value('png')
        grid_size = _assemble_grid(grid_cols_in.value, grid_rows_in.value)
        tile_geometry = _assemble_size(tile_w_in.value, tile_h_in.value,
                                       tile_hb_in.value, tile_vb_in.value)

        out = output_in.value.strip() or str(Path(folder) / 'Montages')
        output_in.set_value(out)
        _save_session(folder, out)

        existing = sorted(Path(out).glob(f'{prefix}_*.{ext}')) if Path(out).is_dir() else []
        if existing:
            overwrite_prefix = _latest_prefix(out, prefix, ext)
            choice = await _conflict_dialog(prefix, ext, len(existing), overwrite_prefix)
            if choice is None:
                return
            if choice == 'increment':
                prefix = _next_prefix(out, prefix, ext)
            elif choice == 'overwrite':
                prefix = overwrite_prefix

        bg = 'none' if bg_transparent_sw.value else (bg_color_in.value or '#ffffff')
        shadow = shadow_sw.value or None
        frame = _assemble_frame(frame_w_in.value, frame_h_in.value,
                                frame_outer_in.value, frame_inner_in.value) if frame_sw.value else None
        border = _assemble_border(border_w_in.value, border_h_in.value) if border_sw.value else None
        if polaroid_sw.value:
            polaroid = 'random' if polaroid_random_sw.value else str(int(polaroid_angle_in.value or 0))
        else:
            polaroid = None

        if not _image_selection:
            refresh_image_list()
        selected_files = sorted(f for f, checked in _image_selection.items() if checked)
        if not selected_files:
            ui.notify('No images selected — check at least one image.', color='warning')
            return

        kwargs = dict(
            grid_size=grid_size,
            output_extension=ext,
            tile_geometry=tile_geometry,
            show_labels=labels_sw.value,
            prefix=prefix,
            crop_dims=crop_in.value.strip() or None,
            font_size=str(int(fontsize_in.value or 12)),
            output_dir=out,
            background_color=bg,
            quality=int(quality_in.value or 85),
            title=title_in.value.strip(),
            font_name=font_in.value.strip(),
            text_color=text_color_in.value or None,
            title_size=int(title_size_in.value or 24) if title_in.value.strip() else None,
            shadow=shadow,
            frame=frame,
            mattecolor=frame_matte_in.value if frame_sw.value else None,
            border=border,
            bordercolor=border_color_in.value if border_sw.value else None,
            mode=mode_sel.value or None,
            polaroid=polaroid,
            image_files=selected_files,
        )
        working = ui.notification('Generating montages…', spinner=True, timeout=0, close_button=False)
        original_cwd = os.getcwd()
        try:
            os.chdir(folder)
            await asyncio.to_thread(create_montages, **kwargs)
        except Exception as exc:
            ui.notify(f'Error: {exc}', color='negative')
            return
        finally:
            working.dismiss()
            os.chdir(original_cwd)

        output_files = sorted(Path(out).glob(f'{prefix}_*.{ext}'))
        ts = int(time.time() * 1000)
        results.clear()
        with results:
            if output_files:
                ui.label(f'{len(output_files)} montage(s) created').classes(
                    'text-base font-semibold mt-2 mb-1'
                )
                for f in output_files:
                    src = f'/output-image?p={urllib.parse.quote(str(f.absolute()))}&t={ts}'
                    ui.image(src).classes('rounded shadow my-1').style('max-width: 100%')
            else:
                ui.notify(
                    'No output created — check that ImageMagick is installed and the folder contains images',
                    color='warning',
                )

    def open_preset_manager():

        def _load_effects_into(pc, sw_shadow,
                               sw_frame, fw_in, fh_in, fo_in, fi_in, fm_in,
                               sw_border, bw_in, bh_in, bc_in,
                               sw_polaroid, pa_in, pr_sw,
                               m_sel, q_in, t_in, fn_in, sw_trans, bg_in,
                               tc_in=None, ts_in=None):
            """Shared helper: populate all new-feature widgets from a preset dict."""
            bg_in.set_value(pc.get('background', '#ffffff'))
            sw_trans.set_value(str_to_bool(pc.get('transparent', 'false')))
            t_in.set_value(pc.get('title', ''))
            fn_in.set_value(pc.get('font', ''))
            if tc_in is not None:
                tc_in.set_value(pc.get('textcolor', '#000000'))
            if ts_in is not None:
                ts_in.set_value(int(pc.get('titlesize', '24')))
            q_in.set_value(int(pc.get('quality', '85')))
            m_sel.set_value(pc.get('mode', ''))

            sw_shadow.set_value(str_to_bool(pc.get('shadow', 'false')))

            frame_val = pc.get('frame', '')
            sw_frame.set_value(bool(frame_val))
            if frame_val:
                f_w, f_h, f_out, f_in_ = _parse_frame(frame_val)
                fw_in.set_value(f_w); fh_in.set_value(f_h)
                fo_in.set_value(f_out); fi_in.set_value(f_in_)
            fm_in.set_value(pc.get('mattecolor', '#808080'))

            border_val = pc.get('border', '')
            sw_border.set_value(bool(border_val))
            if border_val:
                b_w, b_h = _parse_border(border_val)
                bw_in.set_value(b_w); bh_in.set_value(b_h)
            bc_in.set_value(pc.get('bordercolor', '#000000'))

            polaroid_val = pc.get('polaroid', '')
            sw_polaroid.set_value(bool(polaroid_val))
            if polaroid_val == 'random':
                pr_sw.set_value(True); pa_in.set_value(0)
            elif polaroid_val:
                pr_sw.set_value(False); pa_in.set_value(int(polaroid_val))
            else:
                pr_sw.set_value(False)

        def on_load(e):
            name = e.value
            if not name:
                return
            pc = _preset_values(name)
            gc, gr = _parse_grid(pc.get('grid', '2x2'))
            tw, th, thb, tvb = _parse_size(pc.get('size', '500x500+10+10'))
            mgr_name.set_value(name)
            mgr_grid_cols.set_value(gc)
            mgr_grid_rows.set_value(gr)
            mgr_tile_w.set_value(tw)
            mgr_tile_h.set_value(th)
            mgr_tile_hb.set_value(thb)
            mgr_tile_vb.set_value(tvb)
            mgr_prefix.set_value(pc.get('prefix', 'montage'))
            mgr_fontsize.set_value(int(pc.get('fontsize', '12')))
            mgr_crop.set_value(pc.get('crop', ''))
            mgr_ext.set_value(pc.get('ext', 'png'))
            mgr_labels.set_value(str_to_bool(pc.get('labels', 'false')))
            _load_effects_into(pc,
                mgr_shadow_sw,
                mgr_frame_sw, mgr_frame_w, mgr_frame_h, mgr_frame_out, mgr_frame_in,
                mgr_frame_matte, mgr_border_sw, mgr_border_w, mgr_border_h, mgr_border_color,
                mgr_polaroid_sw, mgr_polaroid_angle, mgr_polaroid_random,
                mgr_mode_sel, mgr_quality, mgr_title, mgr_font,
                mgr_transparent_sw, mgr_bg_color,
                tc_in=mgr_text_color, ts_in=mgr_title_size)

        def mgr_save():
            name = mgr_name.value.strip()
            if not name:
                ui.notify('Preset name is required', color='negative')
                return
            if ']' in name or '\n' in name:
                ui.notify("Preset name cannot contain ] or line breaks", color='negative')
                return
            values = {
                'grid': _assemble_grid(mgr_grid_cols.value, mgr_grid_rows.value),
                'size': _assemble_size(mgr_tile_w.value, mgr_tile_h.value,
                                       mgr_tile_hb.value, mgr_tile_vb.value),
                'background': mgr_bg_color.value or '#ffffff',
                'transparent': 'on' if mgr_transparent_sw.value else 'off',
                'title': mgr_title.value.strip(),
                'font': mgr_font.value.strip(),
                'textcolor': mgr_text_color.value or '',
                'titlesize': str(int(mgr_title_size.value or 24)),
                'quality': str(int(mgr_quality.value or 85)),
                'mode': mgr_mode_sel.value or '',
                'prefix': mgr_prefix.value or 'montage',
                'fontsize': str(int(mgr_fontsize.value or 12)),
                'ext': mgr_ext.value or 'png',
                'labels': 'on' if mgr_labels.value else 'off',
                'shadow': 'on' if mgr_shadow_sw.value else '',
                'frame': _assemble_frame(mgr_frame_w.value, mgr_frame_h.value,
                                         mgr_frame_out.value, mgr_frame_in.value)
                         if mgr_frame_sw.value else '',
                'mattecolor': mgr_frame_matte.value if mgr_frame_sw.value else '',
                'border': _assemble_border(mgr_border_w.value, mgr_border_h.value)
                          if mgr_border_sw.value else '',
                'bordercolor': mgr_border_color.value if mgr_border_sw.value else '',
                'polaroid': ('random' if mgr_polaroid_random.value
                             else str(int(mgr_polaroid_angle.value or 0)))
                            if mgr_polaroid_sw.value else '',
            }
            if mgr_crop.value.strip():
                values['crop'] = mgr_crop.value.strip()
            _save_preset(name, values)
            mgr_sel.set_options([''] + _preset_names(), value=name)
            refresh_main_presets()
            ui.notify(f"Preset '{name}' saved", color='positive')

        def mgr_delete():
            name = mgr_sel.value
            if not name:
                ui.notify('Select a preset to delete', color='warning')
                return
            _delete_preset(name)
            mgr_sel.set_options([''] + _preset_names(), value='')
            mgr_name.set_value('')
            refresh_main_presets()
            ui.notify(f"Preset '{name}' deleted", color='positive')

        def mgr_clear():
            mgr_sel.set_value('')
            mgr_name.set_value('')
            mgr_grid_cols.set_value(2)
            mgr_grid_rows.set_value(2)
            mgr_tile_w.set_value(500)
            mgr_tile_h.set_value(500)
            mgr_tile_hb.set_value(10)
            mgr_tile_vb.set_value(10)
            mgr_bg_color.set_value('#ffffff')
            mgr_transparent_sw.set_value(False)
            mgr_title.set_value('')
            mgr_font.set_value('')
            mgr_quality.set_value(85)
            mgr_mode_sel.set_value('')
            mgr_shadow_sw.set_value(False)
            mgr_frame_sw.set_value(False)
            mgr_frame_w.set_value(6)
            mgr_frame_h.set_value(6)
            mgr_frame_out.set_value(3)
            mgr_frame_in.set_value(3)
            mgr_frame_matte.set_value('#808080')
            mgr_border_sw.set_value(False)
            mgr_border_w.set_value(5)
            mgr_border_h.set_value(5)
            mgr_border_color.set_value('#000000')
            mgr_polaroid_sw.set_value(False)
            mgr_polaroid_angle.set_value(0)
            mgr_polaroid_random.set_value(False)
            mgr_prefix.set_value('montage')
            mgr_fontsize.set_value(12)
            mgr_crop.set_value('')
            mgr_ext.set_value('png')
            mgr_labels.set_value(False)

        with ui.dialog() as dialog, ui.card().style('min-width: 520px; max-height: 90vh; overflow-y: auto').classes('p-6 gap-2'):
            ui.label('Preset Manager').classes('text-xl font-bold mb-1')

            mgr_sel = ui.select(
                [''] + _preset_names(),
                label='Load existing preset',
                value='',
                on_change=on_load,
            ).classes('w-full')

            ui.separator().classes('my-2')

            mgr_name = ui.input('Preset name').classes('w-full')

            ui.label('Grid').classes('text-xs text-gray-400 mt-2')
            with ui.row().classes('w-full gap-4'):
                mgr_grid_cols = ui.number('Columns', value=2, min=1, precision=0).classes('flex-1')
                mgr_grid_rows = ui.number('Rows', value=2, min=1, precision=0).classes('flex-1')

            ui.label('Tile size & spacing').classes('text-xs text-gray-400 mt-2')
            with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-2'):
                mgr_tile_w = ui.number('Width (px)', value=500, min=1, precision=0)
                mgr_tile_h = ui.number('Height (px)', value=500, min=1, precision=0)
                mgr_tile_hb = ui.number('H spacing (px)', value=10, min=0, precision=0)
                mgr_tile_vb = ui.number('V spacing (px)', value=10, min=0, precision=0)

            ui.label('Background').classes('text-xs text-gray-400 mt-2')
            with ui.row().classes('w-full items-center gap-3'):
                mgr_bg_color = ui.color_input(value='#ffffff').classes('flex-1')
                mgr_transparent_sw = ui.switch('Transparent')

            ui.label('Output').classes('text-xs text-gray-400 mt-2')
            with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-2'):
                mgr_crop = ui.input('Crop (e.g. 1080x1080)', value='')
                mgr_ext = ui.select(['png', 'jpg', 'bmp', 'tiff'], label='Format', value='png')
            mgr_prefix = ui.input('Output filename prefix', value='montage').classes('w-full mt-1')

            ui.label('Text').classes('text-xs text-gray-400 mt-2')
            with ui.row().classes('w-full gap-4'):
                mgr_title = ui.input('Title', value='').classes('flex-1')
                mgr_font = ui.select([''] + _FONTS, label='Font name', value='',
                                     with_input=True, new_value_mode='add-unique').classes('flex-1')
            with ui.row().classes('w-full items-center gap-3 mt-1'):
                mgr_text_color = ui.color_input(label='Text color', value='#000000').classes('flex-1')
                mgr_title_size = ui.number('Title size', value=24, min=6, precision=0).classes('flex-1')
                mgr_fontsize   = ui.number('Label size', value=12, min=6, precision=0).classes('flex-1')
            with ui.row().classes('w-full items-center gap-4 mt-1'):
                mgr_labels = ui.switch('Show filename labels')

            ui.label('Effects').classes('text-xs text-gray-400 mt-2')
            with ui.row().classes('w-full gap-4'):
                mgr_mode_sel = ui.select(
                    ['', 'Frame', 'Concatenate'],
                    label='Mode', value='',
                ).classes('flex-1')
                mgr_quality = ui.number('Quality (JPG)', value=85, min=0, max=100, precision=0).classes('flex-1')

            with ui.row().classes('w-full items-center gap-3 mt-1'):
                mgr_shadow_sw = ui.switch('Drop shadow')

            with ui.row().classes('w-full items-center gap-3 mt-1'):
                mgr_frame_sw = ui.switch('Frame')
                mgr_frame_matte = ui.color_input(label='Matte color', value='#808080').classes('flex-1')
            with ui.grid(columns=4).classes('w-full gap-2').bind_visibility_from(mgr_frame_sw, 'value'):
                mgr_frame_w   = ui.number('Width px', value=6, min=1, precision=0)
                mgr_frame_h   = ui.number('Height px', value=6, min=1, precision=0)
                mgr_frame_out = ui.number('Outer bevel', value=3, min=0, precision=0)
                mgr_frame_in  = ui.number('Inner bevel', value=3, min=0, precision=0)

            with ui.row().classes('w-full items-center gap-3 mt-1'):
                mgr_border_sw = ui.switch('Border')
                mgr_border_color = ui.color_input(label='Border color', value='#000000').classes('flex-1')
            with ui.row().classes('w-full gap-2').bind_visibility_from(mgr_border_sw, 'value'):
                mgr_border_w = ui.number('Width px', value=5, min=0, precision=0).classes('flex-1')
                mgr_border_h = ui.number('Height px', value=5, min=0, precision=0).classes('flex-1')

            with ui.row().classes('w-full items-center gap-3 mt-1'):
                mgr_polaroid_sw = ui.switch('Polaroid')
            mgr_shadow_sw.bind_enabled_from(mgr_polaroid_sw, 'value', backward=lambda v: not v)
            with ui.row().classes('w-full items-center gap-3').bind_visibility_from(mgr_polaroid_sw, 'value'):
                mgr_polaroid_angle  = ui.number('Angle °', value=0, min=-45, max=45, precision=0).classes('flex-1')
                mgr_polaroid_random = ui.switch('Random (±15°)')

            ui.separator().classes('my-2')

            with ui.row().classes('w-full justify-between'):
                with ui.row().classes('gap-2'):
                    ui.button('Save', on_click=mgr_save).props('unelevated color=primary')
                    ui.button('Delete', on_click=mgr_delete).props('flat color=negative')
                    ui.button('Clear', on_click=mgr_clear).props('flat')
                ui.button('Close', on_click=dialog.close).props('flat')

        dialog.open()

    def open_port_dialog():
        with ui.dialog() as dialog, ui.card().style('min-width: 300px').classes('p-6 gap-3'):
            ui.label('Change Port').classes('text-lg font-bold')
            ui.label('Takes effect after restarting the app.').classes('text-sm text-gray-500')
            port_in = ui.number('Port number', value=_PORT, min=1024, max=65535, precision=0).classes('w-full')

            def save_and_close():
                new_port = int(port_in.value or 8000)
                _save_port(new_port)
                dialog.close()
                ui.notify(
                    f'Port saved as {new_port} — restart the app to apply.',
                    type='info', timeout=0, close_button=True,
                )

            with ui.row().classes('w-full gap-2 justify-end mt-2'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Save', on_click=save_and_close).props('unelevated color=primary')

        dialog.open()

    # --- Main Layout ---
    with ui.column().classes('w-full mx-auto px-6 py-5 gap-4'):
        with ui.row().classes('w-full items-center justify-between'):
            ui.label('Montage Maker').classes('text-3xl font-bold tracking-tight')
            with ui.row().classes('items-center gap-2'):
                ui.select(
                    list(THEMES.keys()),
                    value=_current_theme,
                    on_change=lambda e: apply_theme(e.value),
                ).props('dense outlined label=Theme').style('min-width: 130px')
                ui.button(f'Port: {_PORT}', on_click=open_port_dialog).props('flat').classes('text-sm text-gray-400')

        with ui.row().classes('w-full gap-5 items-start'):

            # ---- Left column: folders, generate, results ----
            with ui.column().classes('gap-4').style('flex: 1.6 1.1 0'):

                with ui.card().classes('w-full p-4 gap-3'):
                    with ui.row().classes('w-full items-end gap-2'):
                        folder_in = ui.input(
                            'Image folder',
                            placeholder='/path/to/your/images',
                            value=_saved_input or os.path.expanduser('~'),
                            on_change=lambda e: refresh_image_list() if os.path.isdir(e.value.strip()) else None,
                        ).classes('flex-grow')
                        ui.button('Browse…', on_click=browse_input).props('flat color=primary')
                        ui.button('Open ↗', on_click=lambda: _open_folder(folder_in.value)).props('flat color=secondary')
                    with ui.row().classes('w-full items-end gap-2'):
                        output_in = ui.input(
                            'Output folder',
                            placeholder='Defaults to {Image folder}/Montages',
                            value=_saved_output,
                        ).classes('flex-grow')
                        ui.button('Browse…', on_click=browse_output).props('flat color=primary')
                        ui.button('Open ↗', on_click=lambda: _open_folder(output_in.value)).props('flat color=secondary')

                with ui.column().classes('w-full gap-1'):
                    with ui.row().classes('w-full items-center gap-2'):
                        img_expansion = ui.expansion(
                            'Input Image Files',
                            on_value_change=lambda e: refresh_image_list() if e.value else None,
                        ).classes('flex-1')
                        _count_label = ui.label('0 of 0 selected').classes('text-xs text-gray-400 self-center')
                    with img_expansion:
                        with ui.row().classes('w-full gap-2 mb-2'):
                            ui.button('All',  on_click=select_all).props('flat dense color=primary').classes('text-xs')
                            ui.button('None', on_click=select_none).props('flat dense color=negative').classes('text-xs')
                        with ui.scroll_area().style('max-height: 240px; width: 100%'):
                            img_list_col = ui.column().classes('w-full gap-1')

                ui.button('Generate Montage', on_click=generate).props(
                    'unelevated color=primary'
                ).classes('w-full py-3 text-base')

                results = ui.column().classes('w-full')

            # ---- Middle column: preset + core settings ----
            with ui.column().classes('gap-4').style('flex: 1'):

                with ui.card().classes('w-full p-4'):
                    with ui.row().classes('w-full items-end gap-2'):
                        preset_sel = ui.select(
                            ['(none)'] + _preset_names(),
                            label='Preset',
                            value='(none)',
                            on_change=apply_preset,
                        ).classes('flex-grow')
                        ui.button('Manage…', on_click=open_preset_manager).props('flat color=primary')

                with ui.card().classes('w-full p-4 gap-1'):
                    ui.label('Grid').classes('text-xs text-gray-400')
                    with ui.row().classes('w-full gap-4'):
                        grid_cols_in = ui.number('Columns', value=2, min=1, precision=0).classes('flex-1')
                        grid_rows_in = ui.number('Rows', value=2, min=1, precision=0).classes('flex-1')

                    ui.label('Tile size & spacing').classes('text-xs text-gray-400 mt-3')
                    with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-2'):
                        tile_w_in = ui.number('Width (px)', value=500, min=1, precision=0)
                        tile_h_in = ui.number('Height (px)', value=500, min=1, precision=0)
                        tile_hb_in = ui.number('H spacing (px)', value=10, min=0, precision=0)
                        tile_vb_in = ui.number('V spacing (px)', value=10, min=0, precision=0)

                    ui.label('Background').classes('text-xs text-gray-400 mt-3')
                    with ui.row().classes('w-full items-center gap-3'):
                        bg_color_in = ui.color_input(value='#ffffff').classes('flex-1')
                        bg_transparent_sw = ui.switch(
                            'Transparent',
                            on_change=lambda: ext_sel.set_value('png') if bg_transparent_sw.value else None,
                        )

                    ui.label('Output').classes('text-xs text-gray-400 mt-3')
                    with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-2'):
                        crop_in = ui.input('Crop (e.g. 1080x1080)', value='')
                        ext_sel = ui.select(['png', 'jpg', 'bmp', 'tiff'], label='Format', value='png')

            # ---- Right column: filename, text & effects ----
            with ui.column().classes('gap-4').style('flex: 1.4 1 0'):

                with ui.card().classes('w-full p-4'):
                    prefix_in = ui.input('Output filename prefix', value='montage').classes('w-full')

                with ui.card().classes('w-full p-4 gap-1'):
                    ui.label('Text').classes('text-xs text-gray-400')
                    with ui.row().classes('w-full gap-4'):
                        title_in = ui.input('Title', value='').classes('flex-1')
                        font_in = ui.select([''] + _FONTS, label='Font name', value='',
                                           with_input=True, new_value_mode='add-unique').classes('flex-1')
                    with ui.row().classes('w-full items-center gap-3 mt-1'):
                        text_color_in = ui.color_input(label='Text color', value='#000000').classes('flex-1')
                        title_size_in = ui.number('Title size', value=24, min=6, precision=0).classes('flex-1')
                        fontsize_in   = ui.number('Label size', value=12, min=6, precision=0).classes('flex-1')
                    with ui.row().classes('w-full items-center gap-4 mt-1'):
                        labels_sw = ui.switch('Show filename labels')

                    ui.label('Effects').classes('text-xs text-gray-400 mt-3')
                    with ui.row().classes('w-full gap-4'):
                        mode_sel = ui.select(
                            ['', 'Frame', 'Concatenate'],
                            label='Mode', value='',
                        ).classes('flex-1')
                        quality_in = ui.number('Quality (JPG)', value=85, min=0, max=100, precision=0).classes('flex-1')

                    with ui.row().classes('w-full items-center gap-4 mt-1'):
                        shadow_sw   = ui.switch('Drop shadow').classes('flex-1')
                        polaroid_sw = ui.switch('Polaroid').classes('flex-1')
                    shadow_sw.bind_enabled_from(polaroid_sw, 'value', backward=lambda v: not v)
                    with ui.row().classes('w-full items-center gap-3').bind_visibility_from(polaroid_sw, 'value'):
                        polaroid_angle_in  = ui.number('Angle °', value=0, min=-45, max=45, precision=0).classes('flex-1')
                        polaroid_random_sw = ui.switch('Random (±15°)')

                    with ui.row().classes('w-full items-center gap-3 mt-1'):
                        frame_sw = ui.switch('Frame')
                        frame_matte_in = ui.color_input(label='Matte color', value='#808080').classes('flex-1')
                    with ui.grid(columns=4).classes('w-full gap-2').bind_visibility_from(frame_sw, 'value'):
                        frame_w_in     = ui.number('Width px', value=6, min=1, precision=0)
                        frame_h_in     = ui.number('Height px', value=6, min=1, precision=0)
                        frame_outer_in = ui.number('Outer bevel', value=3, min=0, precision=0)
                        frame_inner_in = ui.number('Inner bevel', value=3, min=0, precision=0)

                    with ui.row().classes('w-full items-center gap-3 mt-1'):
                        border_sw = ui.switch('Border')
                        border_color_in = ui.color_input(label='Border color', value='#000000').classes('flex-1')
                    with ui.row().classes('w-full gap-2').bind_visibility_from(border_sw, 'value'):
                        border_w_in = ui.number('Width px', value=5, min=0, precision=0).classes('flex-1')
                        border_h_in = ui.number('Height px', value=5, min=0, precision=0).classes('flex-1')

    refresh_image_list()


_PORT = _load_port()
ui.run(native=True, window_size=(1400, 900), title='Montage Maker', port=_PORT, reload=False)
