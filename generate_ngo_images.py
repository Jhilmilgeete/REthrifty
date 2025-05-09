from PIL import Image, ImageDraw, ImageFont
import os
import sqlite3
import re
from datetime import datetime

# --- Path Definitions ---
# Get the absolute directory of the current script
# e.g., C:\Users\HP\OneDrive\Desktop\30 day fullstack\new pro
BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))

# Construct paths relative to BASE_DIR and normalize them
DATABASE_PATH = os.path.normpath(os.path.join(BASE_DIR, 'data', 'items.db'))
NGO_IMAGE_DIR = os.path.normpath(os.path.join(BASE_DIR, 'static', 'images', 'ngos'))
DATA_DIR_CHECK = os.path.normpath(os.path.join(BASE_DIR, 'data')) # For checking existence of 'data' directory

# --- Initial Setup and Debug Prints ---
print(f"--- Path Debugging ---")
print(f"Script's BASE_DIR: {BASE_DIR}")
print(f"Calculated DATA_DIR_CHECK: {DATA_DIR_CHECK}")
print(f"Calculated DATABASE_PATH: {DATABASE_PATH}")
print(f"Calculated NGO_IMAGE_DIR: {NGO_IMAGE_DIR}")
print(f"----------------------")

# Ensure the 'data' directory exists
if not os.path.exists(DATA_DIR_CHECK):
    print(f"CRITICAL ERROR: 'data' directory not found at expected path: {DATA_DIR_CHECK}")
    exit(1) # Exit if critical directory is missing
if not os.path.isdir(DATA_DIR_CHECK):
    print(f"CRITICAL ERROR: Expected 'data' directory is not a directory: {DATA_DIR_CHECK}")
    exit(1)

# Create the ngos image directory if it doesn't exist
os.makedirs(NGO_IMAGE_DIR, exist_ok=True)
print(f"Ensured NGO image directory exists at: {NGO_IMAGE_DIR}")


def get_db_connection():
    """Get database connection"""
    print(f"Attempting to connect to database at: {DATABASE_PATH}")
    if not os.path.exists(DATABASE_PATH):
        print(f"ERROR: Database file not found at {DATABASE_PATH}")
        raise sqlite3.OperationalError(f"Database file not found at {DATABASE_PATH}")
    if not os.path.isfile(DATABASE_PATH):
        print(f"ERROR: Database path exists, but is not a file: {DATABASE_PATH}")
        raise sqlite3.OperationalError(f"Database path exists, but is not a file: {DATABASE_PATH}")
        
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def generate_slug(name):
    """Generates a URL-friendly slug from a name."""
    s = name.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s).strip('-_')
    return s

def generate_placeholder_image(ngo_name, filename_base):
    """Generates a placeholder image for an NGO and saves it."""
    colors = [
        (52, 152, 219), (46, 204, 113), (155, 89, 182),
        (230, 126, 34), (231, 76, 60), (52, 73, 94),
        (26, 188, 156), (241, 196, 15), (149, 165, 166) 
    ]
    
    color_index = hash(ngo_name) % len(colors)
    img_bg_color = colors[color_index]

    img = Image.new('RGB', (400, 300), img_bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError: 
        font = ImageFont.load_default()
    
    words = ngo_name.split()
    lines = []
    current_line = ""
    max_line_width = 380 # Image width (400) - padding
    for word in words:
        # Check if current_line + word + space fits
        if draw.textlength(current_line + word + " ", font=font) <= max_line_width:
            current_line += word + " "
        else:
            # If current_line is not empty, add it to lines
            if current_line: 
                lines.append(current_line.strip())
            # Start new line with the current word
            # Check if the word itself is too long
            if draw.textlength(word + " ", font=font) <= max_line_width:
                current_line = word + " "
            else: # Word is too long, add it as is and it will be truncated or handled by PIL
                lines.append(word)
                current_line = "" 
    
    if current_line: # Add any remaining part of current_line
        lines.append(current_line.strip())

    # Calculate text block height
    line_height = font.getmetrics()[0] + font.getmetrics()[1] # ascent + descent
    total_text_height = len(lines) * line_height
    y_start = (300 - total_text_height) // 2

    for i, line in enumerate(lines):
        text_width = draw.textlength(line, font=font)
        text_position = ((400 - text_width) // 2, y_start + i * line_height)
        draw.text(text_position, line, fill='white', font=font)
    
    image_filename = f"{filename_base}.jpg"
    image_path = os.path.join(NGO_IMAGE_DIR, image_filename)
    img.save(image_path)
    print(f"Created image: {image_path} for NGO: {ngo_name}")
    return image_filename

def update_ngo_logo_in_db(ngo_id, logo_filename):
    """Updates the logo filename for an NGO in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        db_logo_path = os.path.join('ngos', logo_filename).replace('\\', '/')
        
        cursor.execute("UPDATE ngos SET logo = ? WHERE id = ?", (db_logo_path, ngo_id))
        conn.commit()
        print(f"Updated database for NGO ID {ngo_id} with logo: {db_logo_path}")
    except sqlite3.Error as e:
        print(f"Database error updating NGO ID {ngo_id}: {e}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"Unexpected error updating NGO ID {ngo_id}: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    conn = None
    try:
        # Initial checks for directories are done at the top
        # Now, directly proceed to database operations
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM ngos WHERE logo IS NULL OR logo = ''")
        ngos_without_logos = cursor.fetchall()
        
        if not ngos_without_logos:
            print("All NGOs already have logos assigned in the database.")
        else:
            print(f"Found {len(ngos_without_logos)} NGOs without logos. Generating placeholders...")
            for ngo in ngos_without_logos:
                ngo_id = ngo['id']
                ngo_name = ngo['name']
                
                filename_base = generate_slug(ngo_name)
                generated_logo_filename = generate_placeholder_image(ngo_name, filename_base)
                if generated_logo_filename:
                    update_ngo_logo_in_db(ngo_id, generated_logo_filename)
            print("\nFinished generating placeholder images and updating database.")

    except sqlite3.OperationalError as e:
        print(f"Halting due to Operational Error: {e}")
    except sqlite3.Error as e:
        print(f"A SQLite error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()