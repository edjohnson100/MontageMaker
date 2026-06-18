import os
import subprocess
import argparse
import math
import configparser
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("process.log", mode='w'),
        logging.StreamHandler()
    ]
)

def load_config(preset_name):
    """Load settings from config.ini for the given preset."""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if not os.path.exists(config_file):
        logging.warning(f"'{config_file}' not found. Presets unavailable.")
        return {}

    config.read(config_file)
    
    if preset_name in config:
        return config[preset_name]
    else:
        logging.warning(f"Preset '{preset_name}' not found in config.ini. Using defaults.")
        return {}

def get_all_images():
    """Scans current directory for valid image files and returns them sorted."""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    files = []
    
    for f in os.listdir('.'):
        if os.path.isfile(f):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_extensions:
                files.append(f)
    
    return sorted(files)

def create_montages(grid_size, output_extension, tile_geometry, show_labels, prefix, crop_dims, font_size,
                    output_dir=None, background_color='white', quality=None, title='', font_name='',
                    shadow=None, frame=None, mattecolor=None, border=None, bordercolor=None,
                    mode=None, polaroid=None, image_files=None,
                    text_color=None, title_size=None):
    # 1. Parse the grid size
    try:
        if not grid_size:
            raise ValueError("No grid size provided.")
        cols, rows = map(int, grid_size.lower().split('x'))
        images_per_page = cols * rows
    except ValueError:
        logging.error("Grid must be in format COLxROW (e.g., 2x2, 3x4)")
        return

    # 2. Find all images (caller may supply a pre-filtered list)
    if image_files is None:
        image_files = get_all_images()
    
    if not image_files:
        logging.error("No valid image files found in the current directory.")
        return

    total_images = len(image_files)
    total_pages = math.ceil(total_images / images_per_page)
    
    logging.info(f"Found {total_images} images. Creating {total_pages} montage pages...")
    logging.info(f"Settings: Grid={grid_size}, Ext={output_extension}, Size={tile_geometry}, Labels={show_labels}, Font={font_size}")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 3. Loop through the images
    for i in range(total_pages):
        start_idx = i * images_per_page
        end_idx = start_idx + images_per_page
        batch_files = image_files[start_idx:end_idx]

        base_name = f"{prefix}_{i+1:02d}.{output_extension}"
        output_filename = os.path.join(output_dir, base_name) if output_dir else base_name
        
        # 4. Construct Command
        # Pass 1: tile layout (no -title; -fill and -pointsize placed last so IM honours them)
        cmd = ["montage"]

        if font_name:
            cmd.extend(["-font", font_name])
        if mode:
            cmd.extend(["-mode", mode])
        if mattecolor:
            cmd.extend(["-mattecolor", mattecolor])
        if bordercolor:
            cmd.extend(["-bordercolor", bordercolor])
        if shadow and not polaroid:
            # -shadow and +polaroid conflict: shadow flattens before polaroid rotation is composited.
            # +polaroid already bakes in its own shadow, so skip -shadow when polaroid is active.
            cmd.append("-shadow")
        if frame:
            cmd.extend(["-frame", frame])
        if border:
            cmd.extend(["-border", border])
        if show_labels:
            cmd.extend(["-label", "%f"])
        if polaroid == 'random':
            cmd.append("+polaroid")
        elif polaroid is not None:
            cmd.extend(["-polaroid", str(polaroid)])

        cmd.extend(batch_files)

        if crop_dims:
            cmd.extend(["-gravity", "center", "-crop", f"{crop_dims}+0+0"])

        # Global text settings placed after geometry so they are the final values IM reads
        cmd.extend([
            "-tile", grid_size,
            "-geometry", tile_geometry,
            "-gravity", "center",
            "-background", background_color or "white",
            "-pointsize", str(font_size),
        ])
        if text_color:
            cmd.extend(["-fill", text_color])
        if quality is not None:
            cmd.extend(["-quality", str(quality)])
        cmd.append(output_filename)

        # 5. Run pass 1
        try:
            logging.info(f"Processing Page {i+1} -> {output_filename}")
            logging.debug(f"Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                logging.warning(f"Page {i+1} warnings: {result.stderr.strip()}")
        except subprocess.CalledProcessError as e:
            stderr_msg = e.stderr.strip() if e.stderr else '(no output)'
            logging.error(f"Error processing page {i+1}: {stderr_msg}")
            continue
        except FileNotFoundError:
            logging.critical("Error: 'montage' command not found. Is ImageMagick installed?")
            return

        # Pass 2: splice title banner via convert (gives independent size + color from labels)
        if title:
            ts  = int(title_size or font_size)
            bg  = background_color or "white"
            title_h = ts * 2          # vertical space added at top
            pad     = max(ts // 4, 4) # gap between top edge and text baseline
            conv_cmd = [
                "magick",
                output_filename,
                "-gravity", "North",
                "-background", bg,
                "-splice", f"0x{title_h}",
            ]
            if font_name:
                conv_cmd.extend(["-font", font_name])
            conv_cmd.extend(["-pointsize", str(ts)])
            conv_cmd.extend(["-fill", text_color or "black"])
            if quality is not None:
                conv_cmd.extend(["-quality", str(quality)])
            conv_cmd.extend(["-annotate", f"+0+{pad}", title, output_filename])
            try:
                logging.debug(f"Title command: {' '.join(conv_cmd)}")
                r2 = subprocess.run(conv_cmd, check=True, stderr=subprocess.PIPE, text=True)
                if r2.stderr:
                    logging.warning(f"Title warnings: {r2.stderr.strip()}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to render title: {e.stderr.strip()}")
            except FileNotFoundError:
                logging.error("'convert' not found — title not rendered. Ensure ImageMagick is on PATH.")

    logging.info("Done! All montages created.")

def str_to_bool(s):
    """Helper to convert config string 'on'/'true' to Boolean."""
    if isinstance(s, bool): return s
    return s.lower() in ('true', 'on', 'yes', '1')

if __name__ == "__main__":
    examples_text = """Examples:
  # Basic usage
  python montage_maker.py 2x2

  # Large font labels
  python montage_maker.py 2x2 --label --fontsize 24

  # Use preset
  python montage_maker.py --preset instagram_post
    """

    parser = argparse.ArgumentParser(
        description="Batch create image montages from mixed inputs.",
        epilog=examples_text,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("grid", nargs='?', help="Grid layout (e.g., 2x2)")
    parser.add_argument("--preset", help="Load settings from config.ini")
    parser.add_argument("--ext", help="Output extension (default: png)")
    parser.add_argument("--size", help="Tile geometry (default: 500x500+10+10)")
    parser.add_argument("--label", action="store_true", help="Force labels ON")
    parser.add_argument("--prefix", help="Filename prefix")
    parser.add_argument("--crop", help="Crop WxH")
    parser.add_argument("--fontsize", help="Label font point size (default: 12)")

    args = parser.parse_args()

    # --- Configuration Logic ---
    final_settings = {
        'grid': '2x2',
        'ext': 'png',
        'size': '500x500+10+10',
        'prefix': 'montage',
        'crop': None,
        'fontsize': '12',
        'labels': 'false'
    }

    # 1. Load Preset
    if args.preset:
        preset_config = load_config(args.preset)
        final_settings.update(preset_config)

    # 2. Apply Command Line Overrides
    if args.grid: final_settings['grid'] = args.grid
    if args.ext: final_settings['ext'] = args.ext
    if args.size: final_settings['size'] = args.size
    if args.prefix: final_settings['prefix'] = args.prefix
    if args.crop: final_settings['crop'] = args.crop
    if args.fontsize: final_settings['fontsize'] = args.fontsize

    # 3. Determine Labels (Config OR Flag)
    # If the flag is set, it's True. If config says 'true/on', it's True.
    config_labels = str_to_bool(final_settings.get('labels', 'false'))
    show_labels = args.label or config_labels

    create_montages(
        final_settings['grid'], 
        final_settings['ext'], 
        final_settings['size'], 
        show_labels, 
        final_settings['prefix'], 
        final_settings['crop'],
        final_settings['fontsize']
    )