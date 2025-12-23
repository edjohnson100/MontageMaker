import os
import subprocess
import argparse
import glob
import math
import configparser

def load_config(preset_name):
    """Load settings from config.ini for the given preset."""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if not os.path.exists(config_file):
        print(f"Warning: '{config_file}' not found. Presets unavailable.")
        return {}

    config.read(config_file)
    
    if preset_name in config:
        return config[preset_name]
    else:
        print(f"Warning: Preset '{preset_name}' not found in config.ini. Using defaults.")
        return {}

def create_montages(grid_size, input_extension, tile_geometry, show_labels, prefix, crop_dims):
    # 1. Parse the grid size
    try:
        if not grid_size:
            raise ValueError("No grid size provided.")
        cols, rows = map(int, grid_size.lower().split('x'))
        images_per_page = cols * rows
    except ValueError:
        print("Error: Grid must be in format COLxROW (e.g., 2x2, 3x4)")
        return

    # 2. Find all images
    image_files = sorted(glob.glob(f"*.{input_extension}"))
    
    if not image_files:
        print(f"No files found with extension .{input_extension}")
        return

    total_images = len(image_files)
    total_pages = math.ceil(total_images / images_per_page)
    
    print(f"Found {total_images} images. Creating {total_pages} montage pages...")
    print(f"Settings: Grid={grid_size}, Size={tile_geometry}, Crop={crop_dims}, Prefix={prefix}")

    # 3. Loop through the images in chunks
    for i in range(total_pages):
        start_idx = i * images_per_page
        end_idx = start_idx + images_per_page
        batch_files = image_files[start_idx:end_idx]
        
        output_filename = f"{prefix}_{i+1:02d}.{input_extension}"
        
        # 4. Construct the ImageMagick command
        cmd = ["montage"]
        
        if show_labels:
            cmd.extend(["-label", "%f"])
            
        cmd.extend(batch_files)

        # Crop logic
        if crop_dims:
            cmd.extend([
                "-gravity", "center", 
                "-crop", f"{crop_dims}+0+0"
            ])

        cmd.extend([
            "-tile", grid_size,          
            "-geometry", tile_geometry, 
            "-gravity", "center",        
            "-background", "white",      
            "-pointsize", "12",
            output_filename
        ])
        
        # 5. Run the command
        try:
            print(f"Processing Page {i+1} -> {output_filename}")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing page {i+1}: {e}")
        except FileNotFoundError:
            print("Error: 'montage' command not found. Is ImageMagick installed?")
            return

    print("Done! All montages created.")

if __name__ == "__main__":
    examples_text = """Examples:
  # Use the 'instagram_post' preset from config.ini
  python montage_maker.py --preset instagram_post

  # Use a preset but override the grid to be 3x3 instead of 2x2
  python montage_maker.py --preset instagram_post 3x3

  # Manual usage without config file
  python montage_maker.py 2x2 --crop "1000x1000"
    """

    parser = argparse.ArgumentParser(
        description="Batch create image montages with presets.",
        epilog=examples_text,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Arguments
    # Note: 'grid' is now optional (nargs='?') because a preset might supply it.
    parser.add_argument("grid", nargs='?', help="Grid layout (e.g., 2x2). Overrides preset.")
    parser.add_argument("--preset", help="Load settings from [section] in config.ini")
    parser.add_argument("--ext", help="File extension (default: jpg)")
    parser.add_argument("--size", help="Tile geometry (default: 500x500+10+10)")
    parser.add_argument("--label", action="store_true", help="Print filename under each image")
    parser.add_argument("--prefix", help="Filename prefix (default: montage)")
    parser.add_argument("--crop", help="Crop inputs to WxH (e.g. 1000x500)")

    args = parser.parse_args()

    # --- Configuration Logic ---
    # 1. Start with hardcoded defaults
    final_settings = {
        'grid': '2x2',
        'ext': 'jpg',
        'size': '500x500+10+10',
        'prefix': 'montage',
        'crop': None
    }

    # 2. If a preset is requested, load it and update defaults
    if args.preset:
        preset_config = load_config(args.preset)
        final_settings.update(preset_config)

    # 3. If command line args are present, they win (Override)
    if args.grid: final_settings['grid'] = args.grid
    if args.ext: final_settings['ext'] = args.ext
    if args.size: final_settings['size'] = args.size
    if args.prefix: final_settings['prefix'] = args.prefix
    if args.crop: final_settings['crop'] = args.crop
    
    show_labels = args.label 

    create_montages(
        final_settings['grid'], 
        final_settings['ext'], 
        final_settings['size'], 
        show_labels, 
        final_settings['prefix'], 
        final_settings['crop']
    )