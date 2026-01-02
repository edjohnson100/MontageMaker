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

def create_montages(grid_size, output_extension, tile_geometry, show_labels, prefix, crop_dims, font_size):
    # 1. Parse the grid size
    try:
        if not grid_size:
            raise ValueError("No grid size provided.")
        cols, rows = map(int, grid_size.lower().split('x'))
        images_per_page = cols * rows
    except ValueError:
        logging.error("Grid must be in format COLxROW (e.g., 2x2, 3x4)")
        return

    # 2. Find all images
    image_files = get_all_images()
    
    if not image_files:
        logging.error("No valid image files found in the current directory.")
        return

    total_images = len(image_files)
    total_pages = math.ceil(total_images / images_per_page)
    
    logging.info(f"Found {total_images} images. Creating {total_pages} montage pages...")
    logging.info(f"Settings: Grid={grid_size}, Ext={output_extension}, Size={tile_geometry}, Labels={show_labels}, Font={font_size}")

    # 3. Loop through the images
    for i in range(total_pages):
        start_idx = i * images_per_page
        end_idx = start_idx + images_per_page
        batch_files = image_files[start_idx:end_idx]
        
        output_filename = f"{prefix}_{i+1:02d}.{output_extension}"
        
        # 4. Construct Command
        cmd = ["montage"]
        
        if show_labels:
            cmd.extend(["-label", "%f"])
            
        cmd.extend(batch_files)

        if crop_dims:
            cmd.extend(["-gravity", "center", "-crop", f"{crop_dims}+0+0"])

        cmd.extend([
            "-tile", grid_size,          
            "-geometry", tile_geometry, 
            "-gravity", "center",        
            "-background", "white",      
            "-pointsize", str(font_size), # Use the dynamic font size
            output_filename
        ])
        
        # 5. Run
        try:
            logging.info(f"Processing Page {i+1} -> {output_filename}")
            logging.debug(f"Command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error processing page {i+1}: {e}")
        except FileNotFoundError:
            logging.critical("Error: 'montage' command not found. Is ImageMagick installed?")
            return

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